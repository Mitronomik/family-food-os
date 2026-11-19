"""Read-only, reproducible four-axis evidence inventory for composed MealPlans.

This is a developer CLI, not an admission validator or source reviewer. It
reports persisted attestations, actual RecipeNutrition V2 calculation outcomes,
missing role/finished-mass/portion policy and exact Shopping V2 source identity.
Synthetic fixtures are not evidence of independently reviewed family meals.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from app.db.config import DatabaseConfig
from app.domain.food_recipes import RightsReviewStatus, VerificationStatus
from app.domain.meal_compositions import rule_snapshot_digest
from app.domain.meal_plans import MealSourceKind
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyRecipeNutritionV2ReadScope,
)
from app.persistence.sqlalchemy_core.shopping_uow import SqlAlchemyShoppingReadScope
from app.services.recipe_nutrition_v2 import (
    RecipeNutritionV2Service,
    RecipeNutritionV2UnavailableError,
)

from scripts.composed_week_preview import (
    ComposedWeekPreviewBlocked,
    build_preview,
)

SCHEMA = "COMPOSED_WEEK_EVIDENCE_INVENTORY_V1"
NO_GO = "NO_GO_TO_CONSUMER_COMPOSED_MEALS"


def _reject(reason: str) -> None:
    raise ComposedWeekPreviewBlocked(reason)


def _recipe_details(scope, plan):
    versions = {
        event.recipe_version_id
        for event in plan.events
        if event.source_kind is MealSourceKind.COOK_RECIPE
    } | {
        component.recipe_version_id
        for comp in plan.compositions
        for component in comp.components
    }
    if None in versions:
        _reject("Отсутствует RecipeVersion pin исходного MealPlan.")
    recipes = {}
    foods = {}
    for version_id in sorted(versions, key=str):
        detail = scope.recipes.get_detail(version_id)
        if detail is None or detail.version.id != version_id:
            _reject("Закреплённая версия рецепта недоступна.")
        recipes[version_id] = detail
        for ingredient in detail.ingredients:
            food = scope.foods.get(ingredient.food_ingredient_id)
            if food is None:
                _reject("Отсутствует FoodIngredient из версии рецепта.")
            foods[food.id] = food
    return recipes, foods


def _nutrition_unavailable_reason(scope, version_id):
    """Classify existing authority state, not localized exception wording.

    This is an observational diagnostic, not a substitute for RecipeNutrition
    authority validation. Unexpected persistence/decoder errors still propagate.
    """
    detail = scope.versions.get_detail(version_id)
    if detail is None:
        return "RECIPE_VERSION_NOT_FOUND"
    required = tuple(row for row in detail.ingredients if not row.optional)
    bound = sum(scope.bindings.get(row.id) is not None for row in required)
    prepared = scope.prepared.get_authority(version_id) is not None
    if prepared and bound:
        return "CONFLICTING_AUTHORITIES"
    if prepared:
        return "PREPARED_AUTHORITY_ONLY"
    if not required:
        return "NO_REQUIRED_RECIPE_INGREDIENTS"
    if bound == 0:
        return "MISSING_COMPOSITION_BINDINGS"
    if bound < len(required):
        return "PARTIAL_COMPOSITION_BINDINGS"
    # Complete binding count is not proof that versions, food forms or the
    # underlying composition source can actually be applied successfully.
    return "BOUND_AUTHORITY_INVALID_OR_INAPPLICABLE"


def _nutrition_unavailable_result(reason):
    return {
        "status": "UNAVAILABLE",
        "unavailable_reason": reason,
        "available_nutrients": 0,
        "total_nutrients": len(NUTRIENT_CODES),
        "unknown_codes": list(NUTRIENT_CODES),
    }


def _nutrition_observation(scope, service, version_id):
    """Report actual V2 source coverage and stable, fail-closed error codes."""
    try:
        result = service.calculate_in_scope(scope, version_id)
    except RecipeNutritionV2UnavailableError:
        return _nutrition_unavailable_result(
            _nutrition_unavailable_reason(scope, version_id)
        )
    # The V2 composition calculator alone does not inspect prepared-output
    # authority. Never report COMPLETE if the repository also has a competing
    # prepared-output authority for the same pinned RecipeVersion.
    if _nutrition_unavailable_reason(scope, version_id) == "CONFLICTING_AUTHORITIES":
        return _nutrition_unavailable_result("CONFLICTING_AUTHORITIES")
    unknown = [entry.code for entry in result.per_base_serving if entry.amount is None]
    return {
        "status": str(result.status),
        "unavailable_reason": None,
        "available_nutrients": len(NUTRIENT_CODES) - len(unknown),
        "total_nutrients": len(NUTRIENT_CODES),
        "unknown_codes": unknown,
    }


def build_inventory(*, plan, recipes, foods, preview, nutrition):
    """Derive an honest inventory from source pins, not arbitrary 'PASS' flags."""
    if preview.get("status") != "DIAGNOSTIC_ONLY" or not plan.compositions:
        _reject("Инвентаризация допускает только диагностическую составную неделю.")
    if preview["week_start"] != plan.plan.week_start.isoformat():
        _reject("Неделя источника и Shopping V2 расходятся.")
    if preview["revision"] != plan.plan.revision_number:
        _reject("Ревизия источника и Shopping V2 расходится.")
    events = {e.id: e for e in plan.events}
    composition_ids = {comp.event_id for comp in plan.compositions}
    if (
        len(composition_ids) != len(plan.compositions)
        or not composition_ids <= set(events)
        or any(
            events[eid].source_kind is not MealSourceKind.COOK_COMPOSITION
            for eid in composition_ids
        )
        or any(
            event.source_kind is MealSourceKind.COOK_COMPOSITION
            and event.id not in composition_ids
            for event in plan.events
        )
    ):
        _reject("Полнота составных MealEvent в исходной неделе нарушена.")
    servings_by_event = {}
    for serving in plan.servings:
        servings_by_event.setdefault(serving.event_id, []).append(serving)
    non_composition_events = [
        {
            "event_id": str(event.id),
            "date": event.local_date.isoformat(),
            "position": event.position,
            "meal_role": str(event.role),
            "source_kind": str(event.source_kind),
            "recipe_version_id": (
                str(event.recipe_version_id) if event.recipe_version_id else None
            ),
            "source_reference_present": event.source_reference is not None,
            "member_servings": [
                {
                    "member_id": str(serving.member_id),
                    "factor": format(serving.portion_servings, ".6f"),
                }
                for serving in sorted(
                    servings_by_event.get(event.id, ()),
                    key=lambda row: row.member_id.hex,
                )
            ],
            "detailed_evidence_assessment": "NOT_IN_SCOPE",
            "shopping_source_replay": "INCLUDED",
        }
        for event in sorted(
            plan.events, key=lambda row: (row.local_date, row.position, str(row.id))
        )
        if event.id not in composition_ids
    ]
    if len(non_composition_events) + len(composition_ids) != len(plan.events):
        _reject("Нельзя сверить все обязательства исходной недели.")
    by_kind = {
        kind: sum(item["source_kind"] == kind for item in non_composition_events)
        for kind in sorted({item["source_kind"] for item in non_composition_events})
    }
    components = []
    for comp in sorted(
        plan.compositions,
        key=lambda c: (events[c.event_id].local_date, events[c.event_id].position),
    ):
        event = events[comp.event_id]
        for component in sorted(comp.components, key=lambda c: c.position):
            detail = recipes[component.recipe_version_id]
            version = detail.version
            member_servings = [
                {
                    "member_id": str(s.member_id),
                    "factor": format(s.portion_servings, ".6f"),
                }
                for s in sorted(
                    (s for s in comp.servings if s.component_id == component.id),
                    key=lambda s: s.member_id.hex,
                )
            ]
            food_authority = all(
                foods[row.food_ingredient_id].is_active
                and foods[row.food_ingredient_id].allergens_reviewed
                for row in detail.ingredients
            )
            recorded = (
                detail.recipe.is_active
                and version.verification_status is VerificationStatus.SOURCE_VERIFIED
                and version.rights_review_status is RightsReviewStatus.REVIEWED
                and food_authority
            )
            if version.source_output_g is None:
                output_state = "MISSING_SOURCE_OUTPUT"
            elif version.base_servings != version.source_original_servings:
                output_state = "RAW_OUTPUT_DIFFERENT_BASE_UNREVIEWED"
            else:
                output_state = "RAW_OUTPUT_APPLICABILITY_UNREVIEWED"
            if version.id not in nutrition:
                _reject("Отсутствует наблюдение Nutrition V2 для RecipeVersion.")
            components.append(
                {
                    "date": event.local_date.isoformat(),
                    "event_id": str(event.id),
                    "meal_role": str(event.role),
                    "component_id": str(component.id),
                    "position": component.position,
                    "course_kind": str(component.course),
                    "recipe_version_id": str(version.id),
                    "recipe_version_number": version.version_number,
                    "member_servings": member_servings,
                    "source_rights": {
                        "recorded_status": (
                            "VERIFIED_METADATA" if recorded else "SOURCE_REVIEW_BLOCKED"
                        ),
                        "verification": str(version.verification_status),
                        "rights": str(version.rights_review_status),
                        "source_document_sha256": version.source_document_sha256,
                        "source_locator": version.source_url,
                        "food_allergens_reviewed": food_authority,
                        "independent_source_review": "NOT_PERFORMED",
                    },
                    "role_structure": {
                        "rule_code": comp.rule.code,
                        "rule_version": comp.rule.version,
                        "rule_sha256": rule_snapshot_digest(comp.rule),
                        "coverage": str(comp.rule.coverage),
                        "structure_replayed": True,
                        "course_suitability": "UNKNOWN",
                    },
                    "physical": {
                        "portion_factors_are_recipe_scales": True,
                        "base_servings": format(version.base_servings, "f"),
                        "source_original_servings": format(
                            version.source_original_servings, "f"
                        ),
                        "source_output_g_raw": (
                            format(version.source_output_g, "f")
                            if version.source_output_g is not None
                            else None
                        ),
                        "output_evidence": output_state,
                        "independently_reviewed_final_mass_g": None,
                        "member_final_edible_mass_g": None,
                        "applicable_portion_policy": None,
                        "status": "UNKNOWN",
                    },
                    "nutrition": nutrition[version.id],
                }
            )
    if not components:
        _reject("У составной недели не найдено ни одного компонента.")
    source_blocked = sum(
        x["source_rights"]["recorded_status"] != "VERIFIED_METADATA" for x in components
    )
    nutrition_missing = sum(x["nutrition"]["status"] != "COMPLETE" for x in components)
    return {
        "schema": SCHEMA,
        "verdict": NO_GO,
        "scope": "INTERNAL_READ_ONLY_EVIDENCE",
        "meal_plan_id": str(plan.plan.id),
        "revision": plan.plan.revision_number,
        "week_start": plan.plan.week_start.isoformat(),
        "shopping_source_fingerprint": preview["source_fingerprint"],
        "shopping_status": preview["shopping_status"],
        "shopping_price_status": preview["price_status"],
        "plan_events": len(plan.events),
        "composition_events": len(composition_ids),
        "non_composition_events": non_composition_events,
        "components": components,
        "summary": {
            "components": len(components),
            "composition_events": len(composition_ids),
            "non_composition_events": len(non_composition_events),
            "non_composition_by_kind": by_kind,
            "non_composition_detailed_assessment": "NOT_IN_SCOPE",
            "all_plan_events_accounted": True,
            "source_metadata_blocked": source_blocked,
            "nutrition_v2_unavailable_or_partial": nutrition_missing,
            "source_independent_review": "NOT_PERFORMED",
            "course_suitability": "UNKNOWN",
            "physical_portions": "NOT_PROVEN",
            "member_nutrition_complete": "NOT_PROVEN",
            "prep_safety": "NOT_PROVEN",
            "consumer_activation": "BLOCKED",
        },
        "notes": [
            "Проверены сохранённые source pins, но не внешнее происхождение рецептов.",
            "Rule snapshot подтверждает структуру, но не пригодность курсов.",
            "source_output_g не является проверенной массой готовой порции.",
            "Nutrition V2 — наблюдение покрытия, не полное питание семьи.",
            "Shopping COMPLETE не означает готовность семейного меню или Prep.",
            "Некомпозиционные события учтены поштучно, но не прошли отдельную source/role/physical/Nutrition оценку.",
        ],
    }


def inventory_from_database(*, database_path, household_id, plan_id, captured_at):
    """Household-scoped read, Shopping V2 replay and read-only Nutrition V2 lookup."""
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        _reject("Дата исследования должна содержать часовой пояс.")
    path = Path(database_path)
    if not path.is_file():
        _reject("Локальная SQLite-база не найдена.")
    engine = create_sqlite_engine(DatabaseConfig(path=path))
    try:
        with SqlAlchemyShoppingReadScope(engine) as scope:
            household = scope.households.get_household(household_id)
            plan = scope.plans.get_detail(household_id, plan_id)
            if household is None or plan is None or not plan.compositions:
                _reject("Исходный диагностический составной MealPlan не найден.")
            recipes, foods = _recipe_details(scope, plan)
            preview = build_preview(
                plan=plan,
                recipes=recipes,
                foods=foods,
                pantry_items=tuple(
                    scope.pantry.list_items(household_id, include_empty=True)
                ),
                household_timezone=household.timezone,
                captured_at=captured_at,
            )
            with SqlAlchemyRecipeNutritionV2ReadScope(engine) as nutrition_scope:
                service = RecipeNutritionV2Service(
                    lambda: SqlAlchemyRecipeNutritionV2ReadScope(engine),
                    lambda: None,
                )
                component_versions = {
                    part.recipe_version_id
                    for composition in plan.compositions
                    for part in composition.components
                }
                coverage = {
                    vid: _nutrition_observation(nutrition_scope, service, vid)
                    for vid in sorted(component_versions, key=str)
                }
            return build_inventory(
                plan=plan,
                recipes=recipes,
                foods=foods,
                preview=preview,
                nutrition=coverage,
            )
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Internal read-only composed week audit"
    )
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--household", type=UUID, required=True)
    parser.add_argument("--plan", type=UUID, required=True)
    parser.add_argument("--captured-at", required=True)
    args = parser.parse_args()
    captured = datetime.fromisoformat(args.captured_at)
    if captured.tzinfo is None or captured.utcoffset() is None:
        parser.error("--captured-at requires timezone")
    inventory = inventory_from_database(
        database_path=args.sqlite,
        household_id=args.household,
        plan_id=args.plan,
        captured_at=captured,
    )
    # Stdout only: never overwrite SQLite or any existing user files.
    print(json.dumps(inventory, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
