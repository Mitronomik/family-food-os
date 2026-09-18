"""Generate the Gate1-A current-recipe readiness matrix from a fresh database."""

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys
from itertools import product

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.config import DatabaseConfig  # noqa: E402
from app.persistence.sqlalchemy_core.b2b2 import B2B2UnitOfWork  # noqa: E402
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine  # noqa: E402
from app.persistence.sqlalchemy_core.food_recipe_composition import (  # noqa: E402
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (  # noqa: E402
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.food_composition_tables import (  # noqa: E402
    versions as composition_table,
)
from app.persistence.sqlalchemy_core.food_recipe_tables import (  # noqa: E402
    food_recipe_ingredients_table as ingredient_row_table,
)
from app.persistence.sqlalchemy_core.nutrition_evidence_tables import (  # noqa: E402
    nutrition_measure_evidence_table as evidence_table,
    recipe_ingredient_nutrition_assessments_table as assessment_table,
)
from app.seed.b2b2 import upgrade_b2b2  # noqa: E402
from app.seed.food_recipes import seed_food_recipes  # noqa: E402
from app.seed.nutrition_measure_evidence import (  # noqa: E402
    seed_nutrition_measure_evidence,
)
from app.seed.recipe_corrections import (  # noqa: E402
    seed_correction_assessments,
    seed_recipe_corrections,
)
from app.seed.ru_food_data import seed_ru_food_data  # noqa: E402
from sqlalchemy import select  # noqa: E402


ROLE_TYPES = {
    "BREAKFAST": frozenset({"breakfast", "sandwich"}),
    "LUNCH": frozenset({"main", "sandwich"}),
    "DINNER": frozenset({"main"}),
}


def minimum_candidate_capacity(slots, *, sandwich_excluded_members=frozenset()):
    """Exhaust role counts and sandwich allocation with Planner split semantics."""
    role_slots = {
        role: [
            frozenset(participants) for actual, participants in slots if actual == role
        ]
        for role in ROLE_TYPES
    }
    for total in range(1, 10):
        for breakfasts in range(total + 1):
            for mains in range(total - breakfasts + 1):
                sandwiches = total - breakfasts - mains
                if sandwiches > 1:
                    continue
                for sandwich_breakfast_uses in range(3 * sandwiches + 1):
                    sandwich_lunch_uses = 3 * sandwiches - sandwich_breakfast_uses
                    breakfast_help = sum(
                        not (participants & sandwich_excluded_members)
                        for participants in role_slots["BREAKFAST"]
                    )
                    lunch_help = sum(
                        not (participants & sandwich_excluded_members)
                        for participants in role_slots["LUNCH"]
                    )
                    if (
                        3 * breakfasts + min(sandwich_breakfast_uses, breakfast_help)
                        < len(role_slots["BREAKFAST"])
                        or 3 * mains < len(role_slots["DINNER"])
                        or 3 * mains + min(sandwich_lunch_uses, lunch_help)
                        < len(role_slots["LUNCH"]) + len(role_slots["DINNER"])
                    ):
                        continue
                    return {
                        "total": total,
                        "breakfast": breakfasts,
                        "main": mains,
                        "sandwich": sandwiches,
                        "allocation": {
                            "sandwich_breakfast_uses": sandwich_breakfast_uses,
                            "sandwich_lunch_uses": sandwich_lunch_uses,
                        },
                    }
    raise ValueError("No capacity within the audited bounded search.")


def capacity_audit():
    generic = tuple(
        (role, ("member-1",))
        for _day, role in product(range(7), ("BREAKFAST", "LUNCH", "DINNER"))
    )
    exclusion = tuple(
        (role, ("adult", "child"))
        for _day, role in product(range(7), ("BREAKFAST", "LUNCH", "DINNER"))
    )
    # Fixture 3 has a heterogeneous second member and one fixed subset event; the
    # fixed participant is removed before automatic candidate assignment.
    fixed = []
    for day, role in product(range(7), ("BREAKFAST", "LUNCH", "DINNER")):
        participants = ["adult"]
        if role != "LUNCH":
            participants.append("child")
        if day == 0 and role == "DINNER":
            participants.remove("child")
        fixed.append((role, tuple(participants)))
    return {
        "generic_three_meal": minimum_candidate_capacity(generic),
        "hard_exclusion": minimum_candidate_capacity(
            exclusion, sandwich_excluded_members=frozenset({"child"})
        ),
        "heterogeneous_with_subset_fixed_event": minimum_candidate_capacity(
            tuple(fixed)
        ),
        "fixture_contract": {
            "hard_exclusion_food": "sandwich candidate ingredient",
            "fixed_event": "day 1 DINNER for child",
        },
    }


def _classification(scope, contribution, profile):
    row = contribution.row
    assessment = contribution.assessment
    issues = set() if assessment is None else {item.value for item in assessment.issues}
    reusable = (
        scope.adapter_connection.execute(
            select(evidence_table.c.evidence_key)
            .select_from(
                evidence_table.join(
                    assessment_table,
                    assessment_table.c.measure_evidence_id == evidence_table.c.id,
                ).join(
                    ingredient_row_table,
                    ingredient_row_table.c.id
                    == assessment_table.c.recipe_ingredient_id,
                )
            )
            .where(
                assessment_table.c.status_code == "APPROVED_EXACT",
                assessment_table.c.is_current.is_(True),
                assessment_table.c.nutrition_profile_id == profile.id,
                ingredient_row_table.c.food_ingredient_id == row.food_ingredient_id,
                ingredient_row_table.c.unit == row.unit.value,
                evidence_table.c.normalized_input_unit == row.unit.value,
                evidence_table.c.estimated.is_(False),
            )
            .order_by(evidence_table.c.evidence_key)
        )
        .scalars()
        .all()
    )
    if reusable:
        repair_class = "ALREADY_ACCEPTED_EVIDENCE_REBIND"
    elif issues & {"FOOD_FORM_MISMATCH", "IDENTITY_MISMATCH"}:
        repair_class = "IMMUTABLE_RECIPE_REVISION_REQUIRED"
    elif issues == {"PROFILE_REPRESENTATIVENESS_REVIEW"}:
        repair_class = "PROFILE_OR_FORM_DATA_REPAIR"
    elif assessment is None:
        repair_class = "ASSESSMENT_PUBLICATION_REPAIR"
    else:
        repair_class = "NEW_PRIMARY_EVIDENCE_REQUIRED"
    return repair_class, list(dict.fromkeys(reusable))


def _plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    return str(value)


def seed_current(config: DatabaseConfig) -> None:
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
    seed_recipe_corrections(config)
    seed_correction_assessments(config)
    seed_ru_food_data(config)
    upgrade_b2b2(config)


def audit(config: DatabaseConfig) -> dict[str, object]:
    seed_current(config)
    engine = create_sqlite_engine(config)
    try:
        recipes = create_food_recipe_catalogue_service(engine)
        nutrition = create_nutrition_service(engine)
        rows = []
        with B2B2UnitOfWork(engine) as scope:
            for recipe in sorted(
                recipes.list_active(limit=100), key=lambda item: item.canonical_code
            ):
                detail = recipes.get_current_verified(recipe.id)
                result = nutrition.recipe_version(detail.version.id)
                blockers = []
                for contribution in result.required_contributions:
                    if contribution.nutrition.mass_g is not None:
                        continue
                    assessment = contribution.assessment
                    evidence = contribution.measure_evidence
                    food = scope.ingredients.get(contribution.row.food_ingredient_id)
                    profile = contribution.assessment_profile
                    repair_class, reusable = _classification(
                        scope, contribution, profile
                    )
                    compositions = (
                        scope.adapter_connection.execute(
                            select(
                                composition_table.c.id,
                                composition_table.c.version,
                                composition_table.c.kind,
                                composition_table.c.input_state,
                                composition_table.c.profile_id,
                            )
                            .where(
                                composition_table.c.food_ingredient_id
                                == contribution.row.food_ingredient_id
                            )
                            .order_by(composition_table.c.version)
                        )
                        .mappings()
                        .all()
                    )
                    blockers.append(
                        {
                            "position": contribution.row.position,
                            "food_code": food.canonical_code,
                            "quantity": str(contribution.row.quantity),
                            "unit": contribution.row.unit.value,
                            "assessment_status": None
                            if assessment is None
                            else assessment.status_code.value,
                            "assessment_issues": []
                            if assessment is None
                            else [item.value for item in assessment.issues],
                            "evidence_key": None
                            if evidence is None
                            else evidence.evidence_key,
                            "nutrition_profile": None
                            if profile is None
                            else {
                                "id": str(profile.id),
                                "source_name": profile.source_name,
                                "source_id": profile.source_id,
                                "source_version": profile.source_version,
                                "estimated": profile.estimated,
                                "is_current": profile.is_current,
                            },
                            "food_identity": {
                                "id": str(food.id),
                                "canonical_code": food.canonical_code,
                                "canonical_name": food.canonical_name,
                            },
                            "composition_versions": [
                                {
                                    **dict(item),
                                    "id": str(item["id"]),
                                    "profile_id": None
                                    if item["profile_id"] is None
                                    else str(item["profile_id"]),
                                }
                                for item in compositions
                            ],
                            "required_authority": (
                                "exact input grams for the stated food form, backed by "
                                "an authoritative profile and, for non-gram units, an "
                                "exact same-form measure"
                            ),
                            "accepted_repository_evidence_resolves": bool(reusable),
                            "reusable_exact_evidence_keys": reusable,
                            "new_external_primary_evidence_required": repair_class
                            == "NEW_PRIMARY_EVIDENCE_REQUIRED",
                            "repair_class": repair_class,
                        }
                    )
                rows.append(
                    {
                        "recipe_code": recipe.canonical_code,
                        "recipe_version_id": str(detail.version.id),
                        "version_number": detail.version.version_number,
                        "meal_type_code": detail.version.meal_type_code.value,
                        "nutrition_status": result.status.value,
                        "kcal_per_base_serving": _plain(result.per_base_serving.kcal)
                        if result.per_base_serving.kcal is not None
                        else None,
                        "blocking_ingredient_positions": blockers,
                        "technical_gate1_suitable": result.status.value != "INCOMPLETE",
                        "positive_kcal_available": result.per_base_serving.kcal
                        is not None
                        and result.per_base_serving.kcal > 0,
                        "planner_eligible": result.status.value != "INCOMPLETE"
                        and result.per_base_serving.kcal is not None
                        and result.per_base_serving.kcal > 0,
                        "consumer_publication_ready": False,
                    }
                )
        eligible = [row for row in rows if row["planner_eligible"]]
        selected_codes = {
            row["recipe_code"]
            for row in rows
            if row["meal_type_code"] in {"breakfast", "main"}
            and not row["planner_eligible"]
        }
        return {
            "schema_version": 1,
            "accepted_starting_sha": "ce5cf6e2faaf9159e74d8c235f334d47743ab2a0",
            "seed_chain": [
                "seed_food_recipes",
                "seed_nutrition_measure_evidence",
                "seed_recipe_corrections",
                "seed_correction_assessments",
                "seed_ru_food_data",
                "upgrade_b2b2",
            ],
            "recipe_count": len(rows),
            "capacity": capacity_audit(),
            "repair_plan": {
                "current_eligible_recipe_codes": [
                    row["recipe_code"] for row in eligible
                ],
                "selected_actual_fixture_targets": [
                    {
                        "recipe_code": row["recipe_code"],
                        "meal_type_code": row["meal_type_code"],
                        "blocking_rows": [
                            {
                                "position": blocker["position"],
                                "food_code": blocker["food_code"],
                                "repair_class": blocker["repair_class"],
                                "reusable_exact_evidence_keys": blocker[
                                    "reusable_exact_evidence_keys"
                                ],
                            }
                            for blocker in row["blocking_ingredient_positions"]
                        ],
                    }
                    for row in rows
                    if row["recipe_code"] in selected_codes
                ],
                "generic_only_alternate": "WIC1_BEYOND_BASIC_GRILLED_CHEESE",
                "selection_reason": (
                    "The hard-exclusion fixture lower bound requires all three "
                    "breakfast and all five main catalogue versions; the current "
                    "eligible oatmeal supplies one breakfast slot. The sandwich "
                    "is lower capacity under the exclusion split and remains only "
                    "the generic-fixture alternate."
                ),
            },
            "recipes": rows,
        }
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.database.exists():
        raise SystemExit("Audit database must not already exist.")
    result = audit(DatabaseConfig(path=args.database))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
