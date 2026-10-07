"""Reproducible DC4 corpus readiness and Gate1 consumption audit."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.errors import DomainValidationError
from app.domain.food_recipes import RightsReviewStatus, VerificationStatus
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MemberMealPatternSourceKind
from app.domain.planner import (
    PlannerConfig,
    PlannerFailure,
    PlannerRejectionCode,
    PlannerSuccess,
    generate_week,
)
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES, RecipeNutritionAuthorityKind
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.household_composition import (
    create_household_service,
)
from app.persistence.sqlalchemy_core.household_uow import SqlAlchemyHouseholdReadScope
from app.persistence.sqlalchemy_core.meal_pattern_uow import (
    SqlAlchemyMealPatternCatalogueReadScope,
)
from app.persistence.sqlalchemy_core.meal_plan_uow import (
    SqlAlchemyMealPlanReadScope,
    SqlAlchemyMealPlanUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.pantry_composition import create_pantry_service
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.seed.r3d_final_dc3_batch import seed_r3d_final_dc3_batch
from app.services.meal_plans import MealPlanNotFoundError, MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)
from app.services.recipe_nutrition_v2 import RecipeNutritionV2UnavailableError

from scripts.gate1a_fixture_spec import GATE1_ROLE_SHAPES

WEEK_START = date(2026, 9, 14)
PLANNER_CONFIG = PlannerConfig(version="planner-v0.4", max_recipe_repetitions=3)
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")

EXPECTED_ELIGIBLE = Counter({"breakfast": 17, "main": 33, "sandwich": 1})
EXPECTED_EVENT_COUNTS = (7, 14, 21)
EXPECTED_SERVING_COUNTS = (7, 21, 42)


def _meal_plan_service(engine) -> MealPlanService:
    return MealPlanService(
        lambda: SqlAlchemyMealPlanUnitOfWork(engine),
        lambda: SqlAlchemyMealPlanReadScope(engine),
        lambda: SqlAlchemyHouseholdReadScope(engine),
        lambda: SqlAlchemyMealPatternCatalogueReadScope(engine),
    )


def _services(engine):
    meal_plans = _meal_plan_service(engine)
    households = create_household_service(engine)
    recipes = create_food_recipe_catalogue_service(engine)
    nutrition = create_nutrition_service(engine)
    pantry = create_pantry_service(engine)
    recipe_nutrition = create_recipe_nutrition_v2_service(engine)
    planner = PlannerService(
        meal_plans,
        households,
        recipes,
        nutrition,
        pantry,
        PLANNER_CONFIG,
        recipe_nutrition=recipe_nutrition,
    )
    return planner, meal_plans, households, recipes, recipe_nutrition


def _audit_active_catalogue(recipes, food, recipe_nutrition) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []

    active = tuple(recipe for recipe in recipes.list_all() if recipe.is_active)
    for recipe in active:
        issues: list[str] = []
        detail = recipes.get_current_verified(recipe.id)
        version = detail.version

        if version.verification_status is not VerificationStatus.SOURCE_VERIFIED:
            issues.append("VERIFICATION_NOT_SOURCE_VERIFIED")
        if version.rights_review_status is not RightsReviewStatus.REVIEWED:
            issues.append("RIGHTS_NOT_REVIEWED")
        if not version.rights_basis:
            issues.append("RIGHTS_BASIS_MISSING")
        if not version.source_name or not version.source_recipe_id:
            issues.append("SOURCE_IDENTITY_MISSING")
        if not version.source_url or not version.source_document_sha256:
            issues.append("SOURCE_PROVENANCE_MISSING")
        if not CYRILLIC_RE.search(recipe.canonical_name):
            issues.append("RUSSIAN_NAME_MISSING")
        if not detail.steps:
            issues.append("RECIPE_STEPS_MISSING")
        elif any(
            not CYRILLIC_RE.search(step.instruction)
            or ASCII_WORD_RE.search(step.instruction)
            for step in detail.steps
        ):
            issues.append("RUSSIAN_STEPS_NOT_READY")

        ingredient_codes: list[str] = []
        for ingredient in detail.ingredients:
            resolved = food.get(ingredient.food_ingredient_id)
            if resolved is None or not resolved.is_active:
                issues.append("FOOD_INGREDIENT_UNRESOLVED_OR_INACTIVE")
                continue
            ingredient_codes.append(resolved.canonical_code)

        exact_energy_ready = False
        nutrition_available = True
        nutrition_authority_kind = None
        unknown_nutrient_count = None
        available_nutrient_count = None
        try:
            projection = recipe_nutrition.neutral_consumption_projection(version.id)
        except RecipeNutritionV2UnavailableError:
            nutrition_available = False
            issues.append("NUTRITION_AUTHORITY_UNAVAILABLE")
        else:
            exact_energy_ready = projection.exact_energy_ready
            nutrition_authority_kind = projection.authority_kind.value
            if projection.authority_kind is RecipeNutritionAuthorityKind.PREPARED_OUTPUT_V1:
                try:
                    canonical = recipe_nutrition.prepared_canonical_nutrition(version.id)
                except RecipeNutritionV2UnavailableError:
                    issues.append("PREPARED_CANONICAL_NUTRITION_UNAVAILABLE")
                else:
                    unknown_nutrient_count = sum(
                        row.amount is None for row in canonical.required_total
                    )
                    available_nutrient_count = sum(
                        row.amount is not None for row in canonical.required_total
                    )
                    if (
                        len(canonical.required_total) != len(NUTRIENT_CODES)
                        or canonical.total_amount("ENERGY_KCAL") is None
                        or any(
                            row.amount != per_serving.amount * version.base_servings
                            for row, per_serving in zip(
                                canonical.required_total,
                                canonical.per_base_serving,
                                strict=True,
                            )
                            if row.amount is None and per_serving.amount is not None
                        )
                    ):
                        issues.append("PREPARED_UNKNOWN_OR_ENERGY_SEMANTICS")
                    if any(
                        total.amount is None and serving.amount is not None
                        for total, serving in zip(
                            canonical.required_total,
                            canonical.per_base_serving,
                            strict=True,
                        )
                    ):
                        issues.append("UNKNOWN_PROMOTED_TO_NUMERIC")
            if not exact_energy_ready:
                issues.append("EXACT_ENERGY_UNAVAILABLE")

        disposition = "PASS" if not issues else "BLOCKED"
        if issues:
            blockers.append(recipe.canonical_code)

        rows.append(
            {
                "canonical_code": recipe.canonical_code,
                "canonical_name": recipe.canonical_name,
                "recipe_version_id": str(version.id),
                "meal_type": version.meal_type_code.value,
                "ingredient_codes": ingredient_codes,
                "nutrition_available": nutrition_available,
                "exact_energy_ready": exact_energy_ready,
                "nutrition_authority_kind": nutrition_authority_kind,
                "unknown_nutrient_count": unknown_nutrient_count,
                "available_nutrient_count": available_nutrient_count,
                "issues": sorted(set(issues)),
                "disposition": disposition,
            }
        )

    return {
        "active_count": len(rows),
        "blocked_count": len(blockers),
        "blocked_recipe_codes": sorted(blockers),
        "recipes": sorted(rows, key=lambda row: row["canonical_code"]),
    }


def _audit_planner_supply(planner) -> dict[str, Any]:
    admissions = planner.compose_candidate_admission()
    eligible = tuple(item for item in admissions if item.eligible)
    counts = Counter(item.meal_type_code for item in eligible)
    expected = dict(EXPECTED_ELIGIBLE)
    actual = {key: counts.get(key, 0) for key in expected}
    matches = len(eligible) == 51 and actual == expected
    return {
        "eligible_count": len(eligible),
        "meal_type_counts": actual,
        "expected_count": 51,
        "expected_meal_type_counts": expected,
        "matches_accepted_baseline": matches,
        "eligible_recipe_codes": sorted(item.canonical_code for item in eligible),
        "ineligible": [
            {
                "canonical_code": item.canonical_code,
                "is_active": item.is_active,
                "blockers": [blocker.value for blocker in item.blockers],
            }
            for item in admissions
            if not item.eligible
        ],
    }


def _add_member(households, household_id, index: int):
    return households.add_household_member(
        household_id,
        name=f"Участник {index}",
        birth_date=date(1990, 1, index),
        sex="female" if index % 2 else "male",
        height_cm=Decimal(170),
        weight_kg=Decimal(65),
        activity_level="active",
        goal="maintain",
    )


def _accept_custom_pattern(meal_plans, household_id, member_id, roles):
    shares = {
        MealRole.BREAKFAST: Decimal("0.30"),
        MealRole.LUNCH: Decimal("0.35"),
        MealRole.DINNER: Decimal("0.25"),
        MealRole.SNACK: Decimal("0.10"),
        MealRole.PRE_WORKOUT: Decimal("0.10"),
        MealRole.POST_WORKOUT: Decimal("0.10"),
        MealRole.OTHER: Decimal("0.10"),
    }
    schedule = {weekday: roles for weekday in range(1, 8)}
    energy = {weekday: tuple(shares[role] for role in roles) for weekday in range(1, 8)}
    return meal_plans.accept_member_pattern(
        household_id=household_id,
        member_id=member_id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule=schedule,
        energy_shares=energy,
    )


def _fixture_exclusions(number: int, members, food) -> tuple[GenerationMemberConstraints, ...]:
    milk_id = food.get_by_code("MILK_2_5").id
    beef_id = food.get_by_code("BEEF_CATEGORY_1_RAW").id
    constraints = []
    for index, member in enumerate(members, 1):
        excluded = frozenset()
        if number == 2 and index == 1:
            excluded = frozenset({milk_id})
        if number == 3 and index == 3:
            excluded = frozenset({beef_id})
        constraints.append(GenerationMemberConstraints(member.id, excluded))
    return tuple(constraints)


def _selected_exclusion_violations(
    events, members, constraints, recipes
) -> list[dict[str, object]]:
    """Check selected Planner meals against each participating member exclusion."""
    excluded = {item.member_id: item.excluded_food_ingredient_ids for item in constraints}
    selected_version_ingredients = {
        detail.version.id: frozenset(row.food_ingredient_id for row in detail.ingredients)
        for recipe in recipes.list_all()
        if recipe.is_active
        for detail in (recipes.get_current_verified(recipe.id),)
    }
    violations: list[dict[str, object]] = []
    for event_index, event in enumerate(events, 1):
        if event.recipe_version_id is None:
            continue
        ingredients = selected_version_ingredients.get(event.recipe_version_id)
        if ingredients is None:
            violations.append(
                {
                    "event": event_index,
                    "reason": "SELECTED_VERSION_NOT_IN_ACTIVE_CATALOGUE",
                    "recipe_version_id": str(event.recipe_version_id),
                }
            )
            continue
        for member_index, member in enumerate(members, 1):
            if member.id not in event.participant_member_ids:
                continue
            forbidden = ingredients & excluded.get(member.id, frozenset())
            if forbidden:
                violations.append(
                    {
                        "event": event_index,
                        "member": member_index,
                        "recipe_version_id": str(event.recipe_version_id),
                        "excluded_ingredient_ids": sorted(
                            str(value) for value in forbidden
                        ),
                    }
                )
    return violations


def _run_success_fixtures(
    planner, meal_plans, households, food, recipes
) -> list[dict[str, Any]]:
    outcomes = []
    for number, roles_by_member in enumerate(GATE1_ROLE_SHAPES, 1):
        household = households.create_household(
            name=f"DC4 Семья {number}",
            timezone_name="Europe/Moscow",
            city="Санкт-Петербург",
        )
        members = []
        for index, roles in enumerate(roles_by_member, 1):
            member = _add_member(households, household.id, index)
            _accept_custom_pattern(meal_plans, household.id, member.id, roles)
            members.append(member)

        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            _fixture_exclusions(number, members, food),
        )
        constraints = command.members
        pure_request = planner.compose_authoritative_request(command)
        first_pure = generate_week(pure_request, PLANNER_CONFIG)
        second_pure = generate_week(pure_request, PLANNER_CONFIG)
        deterministic = (
            first_pure.trace.fingerprint == second_pure.trace.fingerprint
            and first_pure.trace.request_fingerprint
            == second_pure.trace.request_fingerprint
        )
        planned_success = isinstance(first_pure, PlannerSuccess)
        planned_events = first_pure.events if planned_success else ()
        selected_violations = _selected_exclusion_violations(
            planned_events, members, constraints, recipes
        )

        persisted = None
        persistence_error = None
        try:
            result, persisted = planner.generate_authoritative(command)
        except DomainValidationError as exc:
            result = first_pure
            persistence_error = str(exc)

        persisted_success = isinstance(result, PlannerSuccess) and persisted is not None
        event_count = len(planned_events)
        serving_count = len(persisted.servings) if persisted is not None else 0

        hard_exclusion_rejections = sum(
            PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in row.rejection_codes
            for row in first_pure.trace.candidates
        )

        outcomes.append(
            {
                "fixture": number,
                "member_count": len(members),
                "roles": [[role.value for role in roles] for roles in roles_by_member],
                "planned_success": planned_success,
                "success": persisted_success,
                "persistence_error": persistence_error,
                "event_count": event_count,
                "expected_event_count": EXPECTED_EVENT_COUNTS[number - 1],
                "serving_count": serving_count,
                "expected_serving_count": EXPECTED_SERVING_COUNTS[number - 1],
                "deterministic": deterministic,
                "trace_fingerprint": first_pure.trace.fingerprint,
                "hard_exclusion_rejections": hard_exclusion_rejections,
                "selected_exclusion_violations": selected_violations,
                "selected_exclusions_respected": not selected_violations,
                "planner_version": first_pure.trace.config_version,
            }
        )
    return outcomes


def _run_fail_closed_fixture(planner, meal_plans, households, food) -> dict[str, Any]:
    household = households.create_household(
        name="DC4 bounded infeasibility",
        timezone_name="Europe/Moscow",
        city="Санкт-Петербург",
    )
    member = _add_member(households, household.id, 1)
    _accept_custom_pattern(meal_plans, household.id, member.id, (MealRole.BREAKFAST,))
    milk_id = food.get_by_code("MILK_2_5").id
    egg_id = food.get_by_code("EGG").id
    command = AuthoritativeGenerationRequest(
        household.id,
        WEEK_START,
        (
            GenerationMemberConstraints(
                member.id,
                frozenset({milk_id, egg_id}),
            ),
        ),
    )
    result, persisted = planner.generate_authoritative(command)
    persisted_after = True
    try:
        meal_plans.get_current_plan(household.id, WEEK_START)
    except MealPlanNotFoundError:
        persisted_after = False

    max_repeat_rejections = sum(
        PlannerRejectionCode.MAX_REPETITIONS in row.rejection_codes
        for row in result.trace.candidates
    )
    exclusion_rejections = sum(
        PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in row.rejection_codes
        for row in result.trace.candidates
    )
    return {
        "is_failure": isinstance(result, PlannerFailure),
        "failure_code": None if not isinstance(result, PlannerFailure) else result.code.value,
        "returned_persisted_plan": persisted is not None,
        "partial_plan_exists": persisted_after,
        "max_repetition_rejections": max_repeat_rejections,
        "hard_exclusion_rejections": exclusion_rejections,
        "trace_fingerprint": result.trace.fingerprint,
    }


def audit(config: DatabaseConfig) -> dict[str, Any]:
    seed_r3d_final_dc3_batch(config)
    engine = create_sqlite_engine(config)
    try:
        planner, meal_plans, households, recipes, recipe_nutrition = _services(engine)
        food = create_food_catalogue_service(engine)
        catalogue = _audit_active_catalogue(recipes, food, recipe_nutrition)
        planner_supply = _audit_planner_supply(planner)
        fixtures = _run_success_fixtures(planner, meal_plans, households, food, recipes)
        fail_closed = _run_fail_closed_fixture(
            planner, meal_plans, households, food
        )
    finally:
        engine.dispose()

    fixtures_pass = all(
        row["success"]
        and row["event_count"] == row["expected_event_count"]
        and row["serving_count"] == row["expected_serving_count"]
        and row["deterministic"]
        and row["selected_exclusions_respected"]
        and row["planner_version"] == PLANNER_CONFIG.version
        for row in fixtures
    )
    fail_closed_pass = (
        fail_closed["is_failure"]
        and not fail_closed["returned_persisted_plan"]
        and not fail_closed["partial_plan_exists"]
        and fail_closed["max_repetition_rejections"] > 0
        and fail_closed["hard_exclusion_rejections"] > 0
    )
    blockers = []
    if catalogue["blocked_count"]:
        blockers.append("FULL_ACTIVE_CATALOGUE_READINESS")
    if not planner_supply["matches_accepted_baseline"]:
        blockers.append("PLANNER_ELIGIBLE_BASELINE_DRIFT")
    if not fixtures_pass:
        blockers.append("GATE1_FIXTURE_FAILURE")
    if not fail_closed_pass:
        blockers.append("BOUNDED_INFEASIBILITY_FAILURE")
    migration_ids = migrations.expected_migration_ids()
    migration_ok = (
        migration_ids[-1] == "0042_recipe_prepared_output_nutrition"
        and not any(item.startswith("0043") for item in migration_ids)
    )
    if not migration_ok:
        blockers.append("MIGRATION_HEAD_DRIFT")

    return {
        "contract": "DC4_CORPUS_READINESS_V1",
        "week_start": WEEK_START.isoformat(),
        "planner_version": PLANNER_CONFIG.version,
        "catalogue": catalogue,
        "planner_supply": planner_supply,
        "fixtures": fixtures,
        "bounded_infeasibility": fail_closed,
        "migration_head": migration_ids[-1],
        "migration_ok": migration_ok,
        "ai_enabled_required": False,
        "blockers": blockers,
        "overall_status": "PASS" if not blockers else "BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database")
    parser.add_argument("--output")
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    if args.database:
        config = DatabaseConfig(path=Path(args.database))
        payload = audit(config)
    else:
        with tempfile.TemporaryDirectory(prefix="family-food-dc4-") as tmp:
            payload = audit(DatabaseConfig(path=Path(tmp) / "dc4.sqlite"))

    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    if args.require_pass and payload["overall_status"] != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
