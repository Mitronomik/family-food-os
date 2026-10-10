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
from datetime import timedelta
from decimal import Decimal
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


def validate_fixture_receipt(receipt: dict[str, Any]) -> None:
    """Fail closed if persisted fixture has missing or crossed authority pins."""
    plan = receipt["plan"]
    members = {row["member_id"] for row in receipt["members"]}
    events = plan["events"]
    servings = plan["servings"]
    catalogue = {row["recipe_version_id"] for row in receipt["catalogue"]}
    event_ids = {event["event_id"] for event in events}
    if len(members) != 3 or len(events) != 21 or len(event_ids) != 21:
        raise ValueError("Three-member week must contain 21 distinct events")
    if len(servings) != 42 or len({s["serving_id"] for s in servings}) != 42:
        raise ValueError("Three-member week must contain 42 distinct servings")
    if len(catalogue) < 30 or len(catalogue) != len(receipt["catalogue"]):
        raise ValueError("Fixture catalogue must contain >=30 distinct current pins")
    if len({e["local_date"] for e in events}) != 7:
        raise ValueError("Fixture must cover seven local calendar days")
    if len(plan["member_selections"]) != 3:
        raise ValueError("Missing member selection version pins")
    if {x["member_id"] for x in plan["member_selections"]} != members:
        raise ValueError("Member selection ownership mismatch")
    if any(
        row["event_id"] not in event_ids
        or row["member_id"] not in members
        or Decimal(row["portion_servings"]) <= 0
        for row in servings
    ):
        raise ValueError("Unscoped or invalid Serving")
    for event in events:
        if event["plan_id"] != plan["plan_id"]:
            raise ValueError("Event belongs to a foreign plan")
        if event["source_kind"] != MealSourceKind.COOK_RECIPE.value:
            raise ValueError("Fixture unexpectedly contains non-recipe source")
        if event["recipe_version_id"] not in catalogue:
            raise ValueError("Event points outside verified active catalogue")
    if not receipt["planner"]["deterministic"]:
        raise ValueError("Planner trace is not deterministic")
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
            and pure_a.trace.request_fingerprint
            == pure_b.trace.request_fingerprint
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
            for item in sorted(
                detail.member_selections, key=lambda x: str(x.member_id)
            )
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
                "unique_selected_versions": len({x["recipe_version_id"] for x in events}),
            },
        }
        validate_fixture_receipt(payload)
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
            {"status": "FIXTURE_PINS_CAPTURED", "gate": receipt["gate_decision"],
             "counts": receipt["counts"], "output": str(args.output)},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
