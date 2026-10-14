"""PR10-FD-META: isolated research-only two-event finished-dish evidence.

Never use a user/production database. Do not create Prep, stock or storage authority.
The only persisted revisions live inside a temporary SQLite database.
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
from app.domain.food_recipes import (
    RightsReviewStatus,
    VerificationStatus,
    scale_recipe,
)
from app.domain.planner import PlannerSuccess
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.seed.dc4_a3_russian_step_corrections import (
    seed_dc4_a3_russian_step_corrections,
)
from app.services.meal_plans import MealEventDraft
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
)

from scripts.audit_dc4_corpus_readiness_rerun import (
    GATE1_ROLE_SHAPES,
    WEEK_START,
    _accept_custom_pattern,
    _add_member,
    _services,
)

GOULASH_CODE = "SCHOOL2022_54_2M_BEEF_GOULASH"
SOURCE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "data/curation/r1g-catalogue-capacity-expansion/prepared-publication-specs.json"
)
RESEARCH_EVENT_INDICES = frozenset({0, 3})
SOURCE_MANIFEST_GIT_BLOB_SHA = "394b35d3d02c0498a681584a37d36b1d98faf40d"
SOURCE_RECIPE_KEYS = (
    "canonical_code",
    "recipe_version_id",
    "version_number",
    "base_servings",
    "source_name",
    "source_recipe_id",
    "source_url",
    "source_version",
    "source_document_sha256",
    "source_card_sha256",
    "rights_review_status",
    "verification_status",
    "source_output_g",
    "batch_friendly",
    "freezable",
    "storage_days_fridge",
    "storage_days_freezer",
    "steps",
    "process_sha256",
)
SOURCE_INGREDIENT_KEYS = (
    "recipe_ingredient_id",
    "food_ingredient_id",
    "unit",
    "source_quantity",
)



def _sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _finite_decimal(value: str) -> Decimal:
    result = Decimal(value)
    if not result.is_finite() or result <= 0:
        raise ValueError("Serving/quantity must be positive finite Decimal")
    return result


def _canonical_decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _semantic_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Exact event/member/recipe semantic identity, independent of minted UUIDs."""
    return sorted(
        [
            {
                "local_date": event["local_date"],
                "position": event["position"],
                "role": event["role"],
                "source_kind": event["source_kind"],
                "recipe_version_id": event["recipe_version_id"],
                "servings": sorted(
                    [
                        {
                            "member_id": row["member_id"],
                            "portion_servings": _canonical_decimal(
                                _finite_decimal(row["portion_servings"])
                            ),
                        }
                        for row in event["servings"]
                    ],
                    key=lambda row: row["member_id"],
                ),
            }
            for event in events
        ],
        key=lambda row: (row["local_date"], row["position"]),
    )


def _source_pins(recipe: dict[str, Any], ingredients: list[dict[str, Any]]) -> dict[str, Any]:
    """Canonical allowlist: do not accept untrusted extra source fields."""
    return {
        "recipe": {key: recipe[key] for key in SOURCE_RECIPE_KEYS},
        "ingredients": [
            {
                key: (
                    _canonical_decimal(_finite_decimal(row[key]))
                    if key == "source_quantity"
                    else row[key]
                )
                for key in SOURCE_INGREDIENT_KEYS
            }
            for row in ingredients
        ],
    }


def _trusted_source_pins(
    *, recipe: Any, current: Any, manifest: dict[str, Any], food: Any
) -> dict[str, Any]:
    """Derive independent source truth from the accepted manifest and live seeded domain.

    Do not read receipt fields to build the trusted digest. Rights and process
    text are checked against the exact manifest before any digest is produced.
    """
    source_row = manifest["recipes"][GOULASH_CODE]
    source = source_row["source_receipt"]
    frozen = source_row["trusted_recipe_seed"]
    seed_version = frozen["version"]
    version = current.version
    if frozen["canonical_code"] != recipe.canonical_code:
        raise ValueError("Frozen recipe canonical identity changed")
    if source["rights_review_status"] != "REVIEWED":
        raise ValueError("Frozen source rights are not reviewed")
    for key, actual in (
        ("source_name", version.source_name),
        ("source_recipe_id", version.source_recipe_id),
        ("source_version", version.source_version),
        ("source_document_sha256", version.source_document_sha256),
    ):
        if source[key] != actual:
            raise ValueError(f"Frozen recipe source {key} differs from runtime")
    if version.source_url != source["source_locator"]:
        raise ValueError("Runtime original URL differs from frozen source")
    if (
        version.rights_review_status is not RightsReviewStatus.REVIEWED
        or version.verification_status is not VerificationStatus.SOURCE_VERIFIED
        or _canonical_decimal(version.base_servings)
        != _canonical_decimal(_finite_decimal(seed_version["base_servings"]))
    ):
        raise ValueError("Current RecipeVersion is not accepted source truth")

    manifest_ingredients = seed_version["ingredients"]
    if len(current.ingredients) != len(manifest_ingredients):
        raise ValueError("Current source ingredient count differs from manifest")
    ingredient_rows = []
    for actual, frozen_row in zip(
        current.ingredients, manifest_ingredients, strict=True
    ):
        food_row = food.get(actual.food_ingredient_id)
        if (
            food_row is None
            or food_row.canonical_code != frozen_row["food_ingredient_code"]
            or actual.unit.value != frozen_row["unit"]
            or actual.quantity
            != _finite_decimal(frozen_row["quantity"])
        ):
            raise ValueError("Source ingredient identity/unit/quantity mismatch")
        ingredient_rows.append(
            {
                "recipe_ingredient_id": str(actual.id),
                "food_ingredient_id": str(actual.food_ingredient_id),
                "unit": actual.unit.value,
                "source_quantity": _canonical_decimal(actual.quantity),
            }
        )

    if len(current.steps) != len(seed_version["steps"]):
        raise ValueError("Source process step count differs from manifest")
    steps = []
    for actual, frozen_text in zip(current.steps, seed_version["steps"], strict=True):
        if actual.instruction != frozen_text:
            raise ValueError("Source process step text differs from manifest")
        steps.append(
            {
                "recipe_step_id": str(actual.id),
                "position": actual.position,
                "instruction_sha256": _sha(frozen_text),
            }
        )
    version_fields = {
        "canonical_code": frozen["canonical_code"],
        "recipe_version_id": str(version.id),
        "version_number": version.version_number,
        "base_servings": str(version.base_servings),
        "source_name": source["source_name"],
        "source_recipe_id": source["source_recipe_id"],
        "source_url": source["source_locator"],
        "source_version": source["source_version"],
        "source_document_sha256": source["source_document_sha256"],
        "source_card_sha256": source["exact_source_card_sha256"],
        "rights_review_status": source["rights_review_status"],
        "verification_status": "SOURCE_VERIFIED",
        "source_output_g": (
            str(version.source_output_g) if version.source_output_g is not None else None
        ),
        "batch_friendly": version.batch_friendly,
        "freezable": version.freezable,
        "storage_days_fridge": version.storage_days_fridge,
        "storage_days_freezer": version.storage_days_freezer,
        "steps": steps,
        "process_sha256": _sha(steps),
    }
    return _source_pins(version_fields, ingredient_rows)


def validate_research_receipt(
    receipt: dict[str, Any], *, trusted_semantic_sha256: str, trusted_source_sha256: str
) -> None:
    """Fail closed if a read-back receipt is modified or claims safety approval.

    The caller must obtain the trusted semantic hash independently from the
    intended MealEventDraft inputs; a self-contained JSON hash is not a signature.
    """
    if receipt["schema"] != "PR10_FD_META_RESEARCH_GOULASH_V1":
        raise ValueError("Invalid receipt schema")
    if receipt["scope"] != "ISOLATED_SYNTHETIC_MEALPLAN_ONLY":
        raise ValueError("Production scope is forbidden")
    if receipt["gate_decision"] != "BLOCKED":
        raise ValueError("Research cannot approve finished-dish storage")
    if (
        receipt["safety"]["time_authority"] != "TIME_UNRESOLVED"
        or receipt["safety"]["storage_policy_status"] != "UNAPPROVED_RESEARCH_ONLY"
        or receipt["safety"]["executable_freezer_task"] is not False
        or receipt["safety"]["confirmed_stock"] is not False
    ):
        raise ValueError("Safety/stock authority was falsely promoted")

    plan = receipt["research_plan"]
    events = plan["events"]
    if len(events) != 7 or len({row["event_id"] for row in events}) != 7:
        raise ValueError("Research week must have seven distinct events")
    expected_dates = {
        (WEEK_START + timedelta(days=day)).isoformat() for day in range(7)
    }
    if {row["local_date"] for row in events} != expected_dates:
        raise ValueError("Research week dates do not match")
    if plan["revision_number"] != 2:
        raise ValueError("Research plan revision missing")
    if any(row["source_kind"] != "COOK_RECIPE" for row in events):
        raise ValueError("Unsupported research meal source")
    if any(len(row["servings"]) != 1 for row in events):
        raise ValueError("Research Member/Serving coverage altered")
    if any(row["servings"][0]["member_id"] != plan["member_id"] for row in events):
        raise ValueError("Serving belongs to another member")
    if any(row["role"] != "DINNER" or row["position"] != 1 for row in events):
        raise ValueError("Accepted dinner-only pattern altered")
    if len({(row["local_date"], row["position"]) for row in events}) != 7:
        raise ValueError("Duplicate event slot")

    semantic_sha = _sha(_semantic_rows(events))
    if semantic_sha != trusted_semantic_sha256:
        raise ValueError("Persisted events diverge from trusted intended revisions")
    if semantic_sha != receipt["expected_semantic_sha256"]:
        raise ValueError("Receipt semantic fingerprint mismatch")

    pair = receipt["candidate_pair"]
    if len(pair) != 2 or len({row["event_id"] for row in pair}) != 2:
        raise ValueError("Candidate events must be different")
    by_id = {row["event_id"]: row for row in events}
    if {row["event_id"] for row in pair} - set(by_id):
        raise ValueError("Candidate event not in research plan")
    version = receipt["recipe"]["recipe_version_id"]
    if receipt["recipe"]["canonical_code"] != GOULASH_CODE:
        raise ValueError("Candidate recipe was substituted")
    if receipt["recipe"]["verification_status"] != "SOURCE_VERIFIED":
        raise ValueError("Recipe verification incomplete")
    if receipt["recipe"]["rights_review_status"] != "REVIEWED":
        raise ValueError("Recipe rights not reviewed")
    if (
        receipt["recipe"]["source_recipe_id"] != "ru-school2022:recipe:54-2м"
        or receipt["recipe"]["source_document_sha256"]
        != "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
    ):
        raise ValueError("Source receipt mismatch")
    expected_total = Decimal(0)
    for item in pair:
        row = by_id[item["event_id"]]
        if (
            row["local_date"] != item["local_date"]
            or row["recipe_version_id"] != version
            or item["recipe_version_id"] != version
            or row["servings"] != item["servings"]
        ):
            raise ValueError("Candidate pair not pinned to same verified version")
        expected_total += _finite_decimal(item["servings"][0]["portion_servings"])
    if _canonical_decimal(expected_total) != pair[0]["combined_servings"]:
        raise ValueError("Combined Serving demand incorrect")
    if any(item["combined_servings"] != pair[0]["combined_servings"] for item in pair):
        raise ValueError("Candidate pair disagrees on combined servings")

    quantities = receipt["combined_ingredient_demand"]
    if (
        len(quantities) != 7
        or len({x["recipe_ingredient_id"] for x in quantities}) != 7
    ):
        raise ValueError("Ingredient source rows missing")
    base = _finite_decimal(receipt["recipe"]["base_servings"])
    for ingredient in quantities:
        quantity = _finite_decimal(ingredient["source_quantity"])
        combined = _finite_decimal(ingredient["planned_combined_quantity"])
        if combined != quantity * expected_total / base:
            raise ValueError("Combined demand differs from source Decimal scaling")
        if combined != _finite_decimal(ingredient["per_event_sum_quantity"]):
            raise ValueError("Combined demand double-counts or drops a contribution")
    if not receipt["recipe"]["steps"] or any(
        not step["instruction_sha256"] or not step["recipe_step_id"]
        for step in receipt["recipe"]["steps"]
    ):
        raise ValueError("Immutable recipe step references missing")
    if _sha(receipt["recipe"]["steps"]) != receipt["recipe"]["process_sha256"]:
        raise ValueError("Immutable process hash differs from pinned steps")
    receipt_source_sha = _sha(
        _source_pins(receipt["recipe"], receipt["combined_ingredient_demand"])
    )
    if (
        receipt_source_sha != trusted_source_sha256
        or receipt_source_sha != receipt["source_fingerprint_sha256"]
    ):
        raise ValueError("Receipt source pins differ from independent trusted source")
    if (
        receipt["planned_cook_sessions_baseline"] != len(pair)
        or receipt["planned_cook_sessions_candidate"] != 1
        or receipt["minutes_or_net_actions_saved"] != "NOT_PROVEN"
    ):
        raise ValueError("Cook-session claim not supported by two event contributions")
    if (
        {row["local_date"] for row in pair}
        != {
            WEEK_START.isoformat(),
            (WEEK_START + timedelta(days=3)).isoformat(),
        }
        or sum(row["recipe_version_id"] == version for row in events) != 2
    ):
        raise ValueError("Research pair event schedule or count changed")


def _intended_event(
    event: Any,
    servings: list[Any],
    *,
    target_version_id: Any,
    fixed_research_servings: Decimal | None = None,
) -> tuple[MealEventDraft, dict[str, Any]]:
    exact = {row.member_id: row.portion_servings for row in servings}
    if fixed_research_servings is not None:
        if len(exact) != 1:
            raise ValueError("This bounded proof supports one synthetic member")
        exact[next(iter(exact))] = fixed_research_servings
    recipe_id = (
        target_version_id if target_version_id is not None else event.recipe_version_id
    )
    draft = MealEventDraft(
        local_date=event.local_date,
        position=event.position,
        role=event.role,
        source_kind=event.source_kind,
        servings=exact,
        recipe_version_id=recipe_id,
        source_reference=event.source_reference,
    )
    return draft, {
        "local_date": event.local_date.isoformat(),
        "position": event.position,
        "role": event.role.value,
        "source_kind": event.source_kind.value,
        "recipe_version_id": str(recipe_id) if recipe_id else None,
        "servings": [
            {
                "member_id": str(member_id),
                "portion_servings": str(amount),
            }
            for member_id, amount in sorted(exact.items(), key=lambda v: v[0].hex)
        ],
    }


def build_research_receipt() -> tuple[dict[str, Any], str, str]:
    """Own fresh disposable SQLite; never accept a caller-supplied database path."""
    with tempfile.TemporaryDirectory(prefix="pr10-fd-meta-") as owned_dir:
        config = DatabaseConfig(path=Path(owned_dir) / "research.sqlite")
        seed_dc4_a3_russian_step_corrections(config)
        engine = create_sqlite_engine(config)
        try:
            planner, meal_plans, households, recipes, _ = _services(engine)
            household = households.create_household(
                name="FD-META синтетическая семья",
                timezone_name="Europe/Moscow",
                city="Санкт-Петербург",
            )
            member = _add_member(households, household.id, 1)
            selection = _accept_custom_pattern(
                meal_plans, household.id, member.id, GATE1_ROLE_SHAPES[0][0]
            )
            generation = AuthoritativeGenerationRequest(
                household.id, WEEK_START, (GenerationMemberConstraints(member.id),)
            )
            plan_result, baseline = planner.generate_authoritative(generation)
            if not isinstance(plan_result, PlannerSuccess) or baseline is None:
                raise ValueError("Baseline Planner failed in isolated research database")

            recipe = next(
                (
                    x
                    for x in recipes.list_all()
                    if x.canonical_code == GOULASH_CODE and x.is_active
                ),
                None,
            )
            if recipe is None:
                raise ValueError("Reviewed cooked-goulash Recipe is not active")
            current = recipes.get_current_verified(recipe.id)
            version = current.version
            if (
                version.verification_status is not VerificationStatus.SOURCE_VERIFIED
                or version.rights_review_status is not RightsReviewStatus.REVIEWED
            ):
                raise ValueError("Source/rights gate not met")
            manifest_bytes = SOURCE_MANIFEST.read_bytes()
            git_blob_bytes = b"blob " + str(len(manifest_bytes)).encode("ascii") + b"\x00" + manifest_bytes
            if hashlib.sha1(git_blob_bytes).hexdigest() != SOURCE_MANIFEST_GIT_BLOB_SHA:
                raise ValueError("Pinned manifest Git blob identity changed")
            manifest = json.loads(manifest_bytes)
            source = manifest["recipes"][GOULASH_CODE]["source_receipt"]
            if (
                version.source_recipe_id != source["source_recipe_id"]
                or version.source_document_sha256 != source["source_document_sha256"]
                or version.source_version != source["source_version"]
            ):
                raise ValueError("Actual RecipeVersion diverges from frozen source")

            trusted_source_sha = _sha(
                _trusted_source_pins(
                    recipe=recipe,
                    current=current,
                    manifest=manifest,
                    food=create_food_catalogue_service(engine),
                )
            )

            baseline_servings: dict[Any, list[Any]] = {
                event.id: [row for row in baseline.servings if row.event_id == event.id]
                for event in baseline.events
            }
            originals = sorted(baseline.events, key=lambda e: (e.local_date, e.position))
            if len(originals) != 7:
                raise ValueError("Expected validated one-member seven-event baseline")
            drafts, intended = [], []
            # Fixed fractional Decimal portions avoid conflating per-event quantized
            # rounding residuals with double-counting in this one bounded proof.
            # These are explicit synthetic manual-plan inputs, NOT Planner predictions.
            fixed_portions = {0: Decimal("2.000000"), 3: Decimal("2.500000")}
            for index, event in enumerate(originals):
                draft, semantic = _intended_event(
                    event,
                    baseline_servings[event.id],
                    target_version_id=version.id
                    if index in RESEARCH_EVENT_INDICES
                    else None,
                    fixed_research_servings=fixed_portions.get(index),
                )
                drafts.append(draft)
                intended.append(semantic)
            trusted_digest = _sha(_semantic_rows(intended))
            revised = meal_plans.create_plan_revision(
                household_id=household.id,
                week_start=WEEK_START,
                member_selection_ids={member.id: selection.selection.id},
                events=drafts,
                status=baseline.plan.status,
                config_version="PR10_FD_META_RESEARCH_ONLY_V1",
            )
            persisted = meal_plans.get_current_plan(household.id, WEEK_START)
            if persisted != revised:
                raise ValueError("Revised plan is not the persisted current revision")
            if revised.plan.revision_number != baseline.plan.revision_number + 1:
                raise ValueError("Unexpected revision lineage")
            if revised.plan.supersedes_plan_id != baseline.plan.id:
                raise ValueError("Research plan did not preserve revision history")

            events = []
            for event in sorted(persisted.events, key=lambda e: (e.local_date, e.position)):
                rows = sorted(
                    (x for x in persisted.servings if x.event_id == event.id),
                    key=lambda x: x.member_id.hex,
                )
                events.append(
                    {
                        "event_id": str(event.id),
                        "local_date": event.local_date.isoformat(),
                        "position": event.position,
                        "role": event.role.value,
                        "source_kind": event.source_kind.value,
                        "recipe_version_id": str(event.recipe_version_id),
                        "servings": [
                            {
                                "member_id": str(row.member_id),
                                "portion_servings": str(row.portion_servings),
                            }
                            for row in rows
                        ],
                    }
                )
            if _sha(_semantic_rows(events)) != trusted_digest:
                raise ValueError("Persisted research plan differs from intended inputs")
            pair = [
                {
                    "event_id": row["event_id"],
                    "local_date": row["local_date"],
                    "recipe_version_id": row["recipe_version_id"],
                    "servings": row["servings"],
                }
                for index, row in enumerate(events)
                if index in RESEARCH_EVENT_INDICES
            ]
            if len(pair) != 2 or len({row["event_id"] for row in pair}) != 2:
                raise ValueError("Cannot pin two distinct MealEvents")
            total = sum(
                (
                    _finite_decimal(row["portion_servings"])
                    for event in pair
                    for row in event["servings"]
                ),
                Decimal(0),
            )
            for item in pair:
                item["combined_servings"] = _canonical_decimal(total)

            scaled = scale_recipe(current, total)
            contribution = [
                scale_recipe(
                    current, _finite_decimal(event["servings"][0]["portion_servings"])
                )
                for event in pair
            ]
            demand = []
            for index, (source_row, combined) in enumerate(
                zip(current.ingredients, scaled.ingredients, strict=True)
            ):
                independently_summed = sum(
                    (details.ingredients[index].quantity for details in contribution),
                    Decimal(0),
                )
                if combined.quantity != independently_summed:
                    raise ValueError("Double count / Decimal scaling disagreement")
                demand.append(
                    {
                        "recipe_ingredient_id": str(source_row.id),
                        "food_ingredient_id": str(source_row.food_ingredient_id),
                        "unit": source_row.unit.value,
                        "source_quantity": str(source_row.quantity),
                        "planned_combined_quantity": str(combined.quantity),
                        "per_event_sum_quantity": str(independently_summed),
                    }
                )
            receipt = {
                "schema": "PR10_FD_META_RESEARCH_GOULASH_V1",
                "scope": "ISOLATED_SYNTHETIC_MEALPLAN_ONLY",
                "gate_decision": "BLOCKED",
                "accepted_code_base": "89b13a61fbfb8bb6246b7fb39ad8b3a1a3acf352",
                "research_plan": {
                    "household_id": str(household.id),
                    "member_id": str(member.id),
                    "selection_id": str(selection.selection.id),
                    "timezone": household.timezone,
                    "plan_id": str(persisted.plan.id),
                    "supersedes_research_plan_id": str(baseline.plan.id),
                    "revision_number": persisted.plan.revision_number,
                    "week_start": WEEK_START.isoformat(),
                    "events": events,
                },
                "expected_semantic_sha256": trusted_digest,
                "recipe": {
                    "canonical_code": recipe.canonical_code,
                    "recipe_version_id": str(version.id),
                    "version_number": version.version_number,
                    "base_servings": str(version.base_servings),
                    "source_name": version.source_name,
                    "source_recipe_id": version.source_recipe_id,
                    "source_url": version.source_url,
                    "source_version": version.source_version,
                    "source_document_sha256": version.source_document_sha256,
                    "source_card_sha256": source["exact_source_card_sha256"],
                    "rights_review_status": version.rights_review_status.value,
                    "verification_status": version.verification_status.value,
                    "source_output_g": str(version.source_output_g)
                    if version.source_output_g
                    else None,
                    "freezable": version.freezable,
                    "batch_friendly": version.batch_friendly,
                    "storage_days_fridge": version.storage_days_fridge,
                    "storage_days_freezer": version.storage_days_freezer,
                    "steps": [
                        {
                            "recipe_step_id": str(step.id),
                            "position": step.position,
                            "instruction_sha256": _sha(step.instruction),
                        }
                        for step in current.steps
                    ],
                    "process_sha256": _sha(
                        [
                            {
                                "recipe_step_id": str(step.id),
                                "position": step.position,
                                "instruction_sha256": _sha(step.instruction),
                            }
                            for step in current.steps
                        ]
                    ),
                },
                "candidate_pair": pair,
                "combined_ingredient_demand": demand,
                "safety": {
                    "time_authority": "TIME_UNRESOLVED",
                    "storage_policy_status": "UNAPPROVED_RESEARCH_ONLY",
                    "executable_freezer_task": False,
                    "confirmed_stock": False,
                    "source_evidence_reference": "docs/family-food/pr10-fd-meta-goulash-source-review.md",
                    "blockers": [
                        "RECIPE_SPECIFIC_FINISHED_DISH_STORAGE_NOT_ACCEPTED",
                        "BATCH_EQUIPMENT_CAPACITY_NOT_REVIEWED",
                        "COOLING_AND_STORAGE_ENTRY_TIME_UNVERIFIED",
                        "APPLICABLE_JURISDICTION_POLICY_NOT_APPROVED",
                        "SCALED_NUMERIC_PROCESS_STEPS_NOT_REVIEWED",
                    ],
                },
                "planned_cook_sessions_baseline": 2,
                "planned_cook_sessions_candidate": 1,
                "minutes_or_net_actions_saved": "NOT_PROVEN",
            }
            receipt["source_fingerprint_sha256"] = _sha(
                _source_pins(receipt["recipe"], receipt["combined_ingredient_demand"])
            )
            validate_research_receipt(
                receipt,
                trusted_semantic_sha256=trusted_digest,
                trusted_source_sha256=trusted_source_sha,
            )
            return receipt, trusted_digest, trusted_source_sha
        finally:
            engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt, trusted_semantic, trusted_source = build_research_receipt()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    args.output.write_bytes(encoded)
    print(
        json.dumps(
            {
                "gate": receipt["gate_decision"],
                "scope": receipt["scope"],
                "pair_events": len(receipt["candidate_pair"]),
                "trusted_semantic_sha256": trusted_semantic,
                "trusted_source_sha256": trusted_source,
                "artifact_sha256": hashlib.sha256(encoded).hexdigest(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
