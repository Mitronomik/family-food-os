"""PR10-META read-only evidence operation: persisted synthetic 3-member fixture.

Runs against a fresh temporary SQLite database; NEVER opens production data.
The receipt pins actual persisted plan/event/serving/catalogue source relationships
but does not grant freezer/storage/Prep implementation authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from app.db.config import DatabaseConfig
from app.domain.food_recipes import RightsReviewStatus, VerificationStatus
from app.domain.meal_plans import MealSourceKind
from app.domain.planner import PlannerSuccess, generate_week
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.seed.dc4_a3_russian_step_corrections import (
    seed_dc4_a3_russian_step_corrections,
)
from app.services.planner import AuthoritativeGenerationRequest

from scripts.audit_dc4_corpus_readiness_rerun import (
    GATE1_ROLE_SHAPES,
    PLANNER_CONFIG,
    WEEK_START,
    _accept_custom_pattern,
    _add_member,
    _fixture_exclusions,
    _selected_exclusion_violations,
    _services,
)


def _hash(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite_portion(value: object) -> str:
    """Canonical exact Decimal amount, rejecting NaN, infinity, invalid and zero."""
    if not isinstance(value, str):
        raise ValueError("Serving amount must be a finite Decimal string")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Serving amount is not a Decimal") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Serving amount must be positive and finite")
    return format(amount.normalize(), "f")


def _semantic_pins(events: list[dict[str, Any]]) -> str:
    """Hash exact Planner semantic selection and per-event participant servings."""
    ordered = sorted(events, key=lambda row: (row["local_date"], row["position"]))
    return _hash(ordered)


def _receipt_semantic_events(
    events: list[dict[str, Any]], servings: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_event: dict[str, list[dict[str, str]]] = {
        event["event_id"]: [] for event in events
    }
    for serving in servings:
        by_event[serving["event_id"]].append(
            {
                "member_id": serving["member_id"],
                "portion_servings": _finite_portion(serving["portion_servings"]),
            }
        )
    return [
        {
            "local_date": event["local_date"],
            "position": event["position"],
            "role": event["role"],
            "source_kind": event["source_kind"],
            "recipe_version_id": event["recipe_version_id"],
            "servings": sorted(
                by_event[event["event_id"]], key=lambda item: item["member_id"]
            ),
        }
        for event in events
    ]


def _planner_semantic_events(planned_events: object) -> list[dict[str, Any]]:
    """Independent Planner output; do not derive the baseline from the receipt."""
    return [
        {
            "local_date": event.local_date.isoformat(),
            "position": event.position,
            "role": event.role.value,
            "source_kind": event.source_kind.value,
            "recipe_version_id": (
                str(event.recipe_version_id)
                if event.recipe_version_id is not None
                else None
            ),
            "servings": sorted(
                (
                    {
                        "member_id": str(member_id),
                        "portion_servings": _finite_portion(str(quantity)),
                    }
                    for member_id, quantity in event.portions
                ),
                key=lambda item: item["member_id"],
            ),
        }
        for event in planned_events
    ]


def validate_fixture_receipt(
    receipt: dict[str, Any], *, trusted_semantic_pins_sha256: str | None = None
) -> None:
    """Validate structural pins plus an independently calculated Planner baseline.

    An external verifier must additionally pin the JSON SHA256 from CI. The
    embedded expected_semantic_pins_sha256 detects accidental/partial mutation,
    but does not authenticate malicious edits that also replace that field.
    """
    if receipt["schema"] != "PR10_META_GATE2_FIXTURE_PINS_V1":
        raise ValueError("Unsupported receipt schema")
    if receipt["scope"] != "SYNTHETIC_FRESH_SQLITE_PERSISTED_DIAGNOSTIC_ONLY":
        raise ValueError("Unsupported fixture scope")
    plan = receipt["plan"]
    events = plan["events"]
    servings = plan["servings"]
    catalogue = receipt["catalogue"]
    members = receipt["members"]
    selected_members = {row["member_id"] for row in members}
    event_ids = {event["event_id"] for event in events}
    catalogue_ids = {row["recipe_version_id"] for row in catalogue}

    if len(members) != 3 or len(selected_members) != 3:
        raise ValueError("Three-member fixture must have distinct members")
    if {row["fixture_ordinal"] for row in members} != {1, 2, 3}:
        raise ValueError("Invalid member ordinals")
    if len(events) != 21 or len(event_ids) != 21:
        raise ValueError("Three-member week must contain 21 distinct events")
    if len(servings) != 42 or len({row["serving_id"] for row in servings}) != 42:
        raise ValueError("Three-member week must contain 42 distinct servings")
    if len(catalogue_ids) < 30 or len(catalogue_ids) != len(catalogue):
        raise ValueError("Fixture catalogue must contain >=30 distinct current pins")
    if len({row["canonical_code"] for row in catalogue}) != len(catalogue):
        raise ValueError("Duplicate canonical recipe identity")

    if len(plan["member_selections"]) != 3 or {
        row["member_id"] for row in plan["member_selections"]
    } != selected_members:
        raise ValueError("Member selection coverage mismatch")
    if len({row["selection_id"] for row in plan["member_selections"]}) != 3:
        raise ValueError("Member selection identifiers must be distinct")
    try:
        first_day = date.fromisoformat(plan["week_start"])
        last_day = date.fromisoformat(plan["week_end"])
        days = {date.fromisoformat(row["local_date"]) for row in events}
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid fixture date") from exc
    if last_day != first_day + timedelta(days=6) or days != {
        first_day + timedelta(days=i) for i in range(7)
    }:
        raise ValueError("Meal events must cover exactly seven fixture days")
    if len({(e["local_date"], e["position"]) for e in events}) != 21:
        raise ValueError("Duplicate event schedule slot")

    seen_pairs: set[tuple[str, str]] = set()
    event_members = {event_id: set() for event_id in event_ids}
    for row in servings:
        pair = (row["event_id"], row["member_id"])
        if (
            row["event_id"] not in event_ids
            or row["member_id"] not in selected_members
            or pair in seen_pairs
        ):
            raise ValueError("Serving is foreign or duplicates an event/member pair")
        _finite_portion(row["portion_servings"])
        seen_pairs.add(pair)
        event_members[row["event_id"]].add(row["member_id"])
    if any(not members_for_event for members_for_event in event_members.values()):
        raise ValueError("Meal event missing all Servings")

    for event in events:
        if event["plan_id"] != plan["plan_id"]:
            raise ValueError("Event belongs to a foreign plan")
        if event["source_kind"] != MealSourceKind.COOK_RECIPE.value:
            raise ValueError("Fixture unexpectedly contains non-recipe source")
        if event["recipe_version_id"] not in catalogue_ids:
            raise ValueError("Event points outside verified active catalogue")

    for recipe in catalogue:
        steps = recipe["steps"]
        if not steps or len({step["recipe_step_id"] for step in steps}) != len(steps):
            raise ValueError("Recipe source steps missing or duplicated")
        if sorted(step["position"] for step in steps) != list(range(1, len(steps) + 1)):
            raise ValueError("Recipe step positions are not contiguous")
        if any(
            not isinstance(step["instruction_sha256"], str)
            or len(step["instruction_sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in step["instruction_sha256"])
            for step in steps
        ):
            raise ValueError("Recipe step fingerprint malformed")
        if recipe["process_hash"] != _hash(steps):
            raise ValueError("Recipe process hash differs from included source steps")

    counts = receipt["counts"]
    expected_counts = {
        "members": len(members),
        "meal_events": len(events),
        "servings": len(servings),
        "current_verified_catalogue_versions": len(catalogue),
        "unique_selected_versions": len(
            {event["recipe_version_id"] for event in events}
        ),
    }
    if counts != expected_counts:
        raise ValueError("Receipt declared counts disagree with actual collections")
    planner = receipt["planner"]
    if planner["version"] != PLANNER_CONFIG.version or not planner["deterministic"]:
        raise ValueError("Planner trace or configuration is unverified")
    if planner["selected_exclusion_violations"]:
        raise ValueError("Selected Planner meal violates member exclusions")
    expected_semantic_sha = planner["expected_semantic_pins_sha256"]
    if not isinstance(expected_semantic_sha, str) or len(expected_semantic_sha) != 64:
        raise ValueError("Missing trusted Planner semantic baseline digest")
    actual_semantic_sha = _semantic_pins(
        _receipt_semantic_events(events, servings)
    )
    if actual_semantic_sha != expected_semantic_sha:
        raise ValueError("Event/recipe/member Servings differ from Planner baseline")
    if (
        trusted_semantic_pins_sha256 is not None
        and expected_semantic_sha != trusted_semantic_pins_sha256
    ):
        raise ValueError("Receipt Planner baseline differs from external trusted pin")
    if receipt["gate_decision"] != "BLOCKED":
        raise ValueError("Fixture evidence alone cannot declare PR10-META READY")


def build_fixture_receipt(config: DatabaseConfig) -> dict[str, Any]:
    """Create and read back one synthetic fixture via accepted app services."""
    seed_dc4_a3_russian_step_corrections(config)
    engine = create_sqlite_engine(config)
    try:
        planner, meal_plans, households, recipes, _ = _services(engine)
        food = create_food_catalogue_service(engine)
        household = households.create_household(
            name="PR10-META проверочная семья",
            timezone_name="Europe/Moscow",
            city="Санкт-Петербург",
        )
        members = []
        for index, roles in enumerate(GATE1_ROLE_SHAPES[2], 1):
            member = _add_member(households, household.id, index)
            selection = _accept_custom_pattern(
                meal_plans, household.id, member.id, roles
            )
            members.append((member, selection))
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            _fixture_exclusions(3, [m for m, _ in members], food),
        )
        request = planner.compose_authoritative_request(command)
        pure_a = generate_week(request, PLANNER_CONFIG)
        pure_b = generate_week(request, PLANNER_CONFIG)
        if not isinstance(pure_a, PlannerSuccess):
            raise TypeError("Three-member Planner fixture did not succeed")
        if not isinstance(pure_b, PlannerSuccess):
            raise TypeError("Planner replay failed")
        trace_stable = (
            pure_a.trace.fingerprint == pure_b.trace.fingerprint
            and pure_a.trace.request_fingerprint == pure_b.trace.request_fingerprint
        )
        violations = _selected_exclusion_violations(
            pure_a.events,
            [m for m, _ in members],
            command.members,
            recipes,
        )
        if violations:
            raise ValueError("Planner fixture violates a member exclusion")

        result, persisted = planner.generate_authoritative(command)
        if not isinstance(result, PlannerSuccess) or persisted is None:
            raise ValueError("Authoritative MealPlan persistence failed")
        detail = meal_plans.get_current_plan(household.id, WEEK_START)
        if detail != persisted:
            raise ValueError("Persisted MealPlan read-back differs from service")
        if not trace_stable:
            raise ValueError("Pure Planner semantic replay drift")

        active = [r for r in recipes.list_all() if r.is_active]
        catalogue = []
        for recipe in sorted(active, key=lambda r: r.canonical_code):
            rd = recipes.get_current_verified(recipe.id)
            version = rd.version
            if (
                version.verification_status is not VerificationStatus.SOURCE_VERIFIED
                or version.rights_review_status is not RightsReviewStatus.REVIEWED
            ):
                raise ValueError("Unverified catalogue authority")
            steps = [
                {
                    "recipe_step_id": str(step.id),
                    "position": step.position,
                    "instruction_sha256": _hash(step.instruction),
                    "stage_code": step.stage_code,
                }
                for step in sorted(rd.steps, key=lambda s: s.position)
            ]
            if not steps:
                raise ValueError("Recipe is missing its process instructions")
            catalogue.append(
                {
                    "canonical_code": recipe.canonical_code,
                    "recipe_version_id": str(version.id),
                    "version_number": version.version_number,
                    "source_name": version.source_name,
                    "source_recipe_id": version.source_recipe_id,
                    "source_version": version.source_version,
                    "source_document_sha256": version.source_document_sha256,
                    "source_original_servings": str(version.source_original_servings),
                    "base_servings": str(version.base_servings),
                    "prep_time_minutes": version.prep_time_minutes,
                    "cook_time_minutes": version.cook_time_minutes,
                    "total_time_minutes": version.total_time_minutes,
                    "batch_friendly": version.batch_friendly,
                    "freezable": version.freezable,
                    "storage_days_fridge": version.storage_days_fridge,
                    "storage_days_freezer": version.storage_days_freezer,
                    "process_hash": _hash(steps),
                    "steps": steps,
                }
            )
        events = [
            {
                "event_id": str(event.id),
                "plan_id": str(event.plan_id),
                "local_date": event.local_date.isoformat(),
                "position": event.position,
                "role": event.role.value,
                "source_kind": event.source_kind.value,
                "recipe_version_id": (
                    str(event.recipe_version_id)
                    if event.recipe_version_id is not None
                    else None
                ),
            }
            for event in sorted(
                detail.events, key=lambda e: (e.local_date, e.position, str(e.id))
            )
        ]
        servings = [
            {
                "serving_id": str(row.id),
                "event_id": str(row.event_id),
                "member_id": str(row.member_id),
                "portion_servings": str(row.portion_servings),
            }
            for row in sorted(
                detail.servings,
                key=lambda r: (str(r.event_id), str(r.member_id)),
            )
        ]
        pins = [
            {
                "member_id": str(item.member_id),
                "selection_id": str(item.selection_id),
            }
            for item in sorted(detail.member_selections, key=lambda x: str(x.member_id))
        ]
        payload = {
            "schema": "PR10_META_GATE2_FIXTURE_PINS_V1",
            "scope": "SYNTHETIC_FRESH_SQLITE_PERSISTED_DIAGNOSTIC_ONLY",
            "gate_decision": "BLOCKED",
            "gate_blockers_remaining": [
                "SOURCE_REVIEWED_SHARED_PREP_NOT_PROVEN",
                "FOOD_STORAGE_TRANSITION_UNVERIFIED",
                "NUMERIC_STEP_CLASSIFICATION_UNVERIFIED",
            ],
            "planner": {
                "version": PLANNER_CONFIG.version,
                "deterministic": trace_stable,
                "trace_fingerprint": pure_a.trace.fingerprint,
                "request_fingerprint": pure_a.trace.request_fingerprint,
                "expected_semantic_pins_sha256": _semantic_pins(
                    _planner_semantic_events(pure_a.events)
                ),
                "selected_exclusion_violations": violations,
            },
            "members": [
                {"member_id": str(member.id), "fixture_ordinal": ordinal}
                for ordinal, (member, _) in enumerate(members, 1)
            ],
            "plan": {
                "household_id": str(household.id),
                "plan_id": str(detail.plan.id),
                "revision_number": detail.plan.revision_number,
                "week_start": detail.plan.week_start.isoformat(),
                "week_end": (detail.plan.week_start + timedelta(days=6)).isoformat(),
                "timezone": household.timezone,
                "config_version": detail.plan.config_version,
                "member_selections": pins,
                "events": events,
                "servings": servings,
            },
            "catalogue": catalogue,
            "counts": {
                "members": len(members),
                "meal_events": len(events),
                "servings": len(servings),
                "current_verified_catalogue_versions": len(catalogue),
                "unique_selected_versions": len(
                    {x["recipe_version_id"] for x in events}
                ),
            },
        }
        validate_fixture_receipt(
            payload,
            trusted_semantic_pins_sha256=_semantic_pins(
                _planner_semantic_events(pure_a.events)
            ),
        )
        return payload
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="pr10-meta-gate2-") as directory:
        receipt = build_fixture_receipt(
            DatabaseConfig(path=Path(directory) / "fixture.sqlite")
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "FIXTURE_PINS_CAPTURED",
                "gate": receipt["gate_decision"],
                "counts": receipt["counts"],
                "output": str(args.output),
                "planner_semantic_pins_sha256": receipt["planner"]["expected_semantic_pins_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
