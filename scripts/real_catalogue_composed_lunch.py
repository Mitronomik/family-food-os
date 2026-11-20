"""Internal end-to-end composed lunch from TWO genuine curated RecipeVersions.

Fresh temporary SQLite only: actual seed -> Planner -> immutable MealPlan
revision -> member-component Servings -> deterministic Shopping V2 -> evidence.
This is a diagnostic product proof, not authority for physical size, complete
Nutrition, meal-course suitability, storage, cost or consumer publication.

Recipe sources are intentionally DISTINCT (MR2019 cabbage soup + School2022
beef goulash). Do not claim this exact pairing is a published School2022 menu.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.db.config import DatabaseConfig
from app.domain.food_recipes import RightsReviewStatus, VerificationStatus
from app.domain.meal_compositions import (
    CourseCardinality,
    DraftMealStructureRule,
    MealComponentDraft,
    MealCourseKind,
    MealEventCompositionDraft,
    MemberComponentServingDraft,
    RequiredCourseCoverage,
)
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealSourceKind
from app.domain.planner import PlannerSuccess
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.meal_plan_uow import SqlAlchemyMealPlanUnitOfWork
from app.persistence.sqlalchemy_core.shopping_uow import SqlAlchemyShoppingReadScope
from app.seed.dc4_a3_russian_step_corrections import (
    seed_dc4_a3_russian_step_corrections,
)
from app.services.meal_plan_composition_revisions import (
    make_complete_diagnostic_revision,
    persist_diagnostic_composition_revision,
)
from app.services.meal_plans import MealEventDraft
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
)

from scripts.audit_dc4_corpus_readiness_rerun import (
    WEEK_START,
    _accept_custom_pattern,
    _add_member,
    _services,
)
from scripts.composed_week_evidence import inventory_from_database
from scripts.composed_week_preview import preview_from_database

SOURCE_CODES = (
    ("MR2019_1_2A_VEGETARIAN_CABBAGE_SOUP", MealCourseKind.FIRST),
    ("SCHOOL2022_54_2M_BEEF_GOULASH", MealCourseKind.SECOND),
)
SCHEMA = "REAL_CATALOGUE_COMPOSED_LUNCH_DIAGNOSTIC_V1"
CREATED = datetime(2026, 11, 20, 10, tzinfo=UTC)


def _hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _recipe_pin(recipes, code):
    recipe = next(
        (item for item in recipes.list_all() if item.canonical_code == code), None
    )
    if recipe is None or not recipe.is_active:
        raise ValueError(f"No active real curated source recipe: {code}")
    detail = recipes.get_current_verified(recipe.id)
    if (
        detail is None
        or detail.version.verification_status is not VerificationStatus.SOURCE_VERIFIED
        or detail.version.rights_review_status is not RightsReviewStatus.REVIEWED
        or detail.recipe.canonical_code != code
        or not detail.version.source_document_sha256
    ):
        raise ValueError("Exact source/rights/version pin is missing")
    return detail


def build_research_proof() -> dict:
    """Disposable, isolated research database; no arbitrary DB path accepted."""
    with tempfile.TemporaryDirectory(prefix="familyfood-real-composed-") as directory:
        config = DatabaseConfig(path=Path(directory) / "diagnostic.sqlite")
        seed_dc4_a3_russian_step_corrections(config)
        engine = create_sqlite_engine(config)
        try:
            planner, meal_plans, households, recipes, _nutrition = _services(engine)
            household = households.create_household(
                name="Исследовательская семья",
                timezone_name="Europe/Moscow",
                city="Санкт-Петербург",
            )
            member = _add_member(households, household.id, 1)
            selection = _accept_custom_pattern(
                meal_plans, household.id, member.id, (MealRole.LUNCH,)
            )
            generated, prior = planner.generate_authoritative(
                AuthoritativeGenerationRequest(
                    household.id,
                    WEEK_START,
                    (GenerationMemberConstraints(member.id),),
                )
            )
            if not isinstance(generated, PlannerSuccess) or prior is None:
                raise ValueError("Real-catalogue lunch Planner baseline failed")
            old = sorted(
                prior.events, key=lambda event: (event.local_date, event.position)
            )
            if (
                len(old) != 7
                or len(prior.servings) != 7
                or any(event.role is not MealRole.LUNCH for event in old)
            ):
                raise ValueError("Planner did not persist exactly seven real lunches")
            source = tuple(
                (_recipe_pin(recipes, code), kind) for code, kind in SOURCE_CODES
            )
            source_rows = [
                {
                    "course": kind.value,
                    "recipe_code": detail.recipe.canonical_code,
                    "recipe_name_ru": detail.recipe.canonical_name,
                    "source_name": detail.version.source_name,
                    "source_recipe_id": detail.version.source_recipe_id,
                    "source_document_sha256": detail.version.source_document_sha256,
                    "source_original_servings": format(
                        detail.version.source_original_servings, "f"
                    ),
                    "source_output_g_raw": (
                        format(detail.version.source_output_g, "f")
                        if detail.version.source_output_g is not None
                        else None
                    ),
                    "portion_servings": "1.000000",
                }
                for detail, kind in source
            ]
            # Real source review is a hard admission gate. Observe exact
            # unresolved FoodIngredient status, do NOT flip reviewed flags to
            # make the research week pass.
            blocking_foods = []
            with SqlAlchemyShoppingReadScope(engine) as read:
                for detail, kind in source:
                    for ingredient in detail.ingredients:
                        food = read.foods.get(ingredient.food_ingredient_id)
                        if food is None:
                            raise ValueError("Missing canonical ingredient")
                        if not food.is_active or not food.allergens_reviewed:
                            blocking_foods.append(
                                {
                                    "recipe_code": detail.recipe.canonical_code,
                                    "course": kind.value,
                                    "food_code": food.canonical_code,
                                    "food_name_ru": food.canonical_name,
                                    "active": food.is_active,
                                    "allergens_reviewed": food.allergens_reviewed,
                                    "allergen_codes_observed": list(
                                        food.allergen_codes
                                    ),
                                }
                            )
            if blocking_foods:
                semantic = {
                    "baseline_events": len(old),
                    "source_courses": source_rows,
                    "blocking_ingredients": sorted(
                        blocking_foods,
                        key=lambda row: (row["recipe_code"], row["food_code"]),
                    ),
                    "unique_blocking_food_codes": sorted(
                        {row["food_code"] for row in blocking_foods}
                    ),
                }
                evidence = {
                    **semantic,
                    "composed_event_count": 0,
                    "shopping_status": "NOT_RUN_SOURCE_ADMISSION_BLOCKED",
                    "price_status": "UNKNOWN",
                }
                return {
                    "schema": SCHEMA,
                    "scope": "ISOLATED_SYNTHETIC_MEMBER_REAL_CURATED_RECIPES",
                    "decision": "BLOCKED_UNREVIEWED_CANONICAL_FOOD_ALLERGENS",
                    "source_pairing": "MANUAL_CROSS_SOURCE_RESEARCH_NOT_PUBLISHED_MENU",
                    "core_ai_enabled": False,
                    "semantic_sha256": _hash(evidence),
                    "evidence": evidence,
                    "limitations": {
                        "reviewed_source_provenance": True,
                        "canonical_allergen_review_complete": False,
                        "course_suitability_independently_approved": False,
                        "member_portion_mass_validated": False,
                        "nutrition_fully_complete": False,
                        "safe_prep_approved": False,
                        "customer_activation": False,
                        "no_production_data_modified": True,
                    },
                }
            # The immutable 0044 composition contract requires the original
            # target RecipeVersion to appear exactly once. First create an
            # explicit normal manual revision with goulash pinned at the target
            # lunch, retaining the six other Planner events/Serving factors.
            original_servings = {
                event.id: tuple(
                    serving
                    for serving in prior.servings
                    if serving.event_id == event.id
                )
                for event in old
            }
            goulash_version_id = source[1][0].version.id
            manual_events = [
                MealEventDraft(
                    local_date=event.local_date,
                    position=event.position,
                    role=event.role,
                    source_kind=MealSourceKind.COOK_RECIPE,
                    servings={
                        serving.member_id: (
                            Decimal(1)
                            if event.id == old[0].id
                            else serving.portion_servings
                        )
                        for serving in original_servings[event.id]
                    },
                    recipe_version_id=(
                        goulash_version_id
                        if event.id == old[0].id
                        else event.recipe_version_id
                    ),
                    source_reference=None,
                )
                for event in old
            ]
            anchored = meal_plans.create_plan_revision(
                household_id=household.id,
                week_start=WEEK_START,
                member_selection_ids={member.id: selection.selection.id},
                events=manual_events,
                status=prior.plan.status,
                config_version="REAL_CATALOGUE_RESEARCH_BASE_V1",
            )
            anchored_events = sorted(
                anchored.events, key=lambda event: (event.local_date, event.position)
            )
            target = anchored_events[0]
            if (
                anchored.plan.supersedes_plan_id != prior.plan.id
                or target.recipe_version_id != goulash_version_id
                or len(anchored_events) != len(old)
            ):
                raise ValueError("Original recipe source anchor was not preserved")
            proposal = MealEventCompositionDraft(
                anchored.plan.id,
                target.id,
                tuple(
                    MealComponentDraft(target.id, index, kind, detail.version.id)
                    for index, (detail, kind) in enumerate(source, 1)
                ),
                tuple(
                    MemberComponentServingDraft(target.id, index, member.id, Decimal(1))
                    for index in range(1, len(source) + 1)
                ),
            )
            # A research structure snapshot, not an adopted public role policy.
            rule = DraftMealStructureRule(
                code="RESEARCH_SOURCE_BACKED_FIRST_SECOND_V1",
                version=1,
                meal_role=MealRole.LUNCH,
                requirements=(
                    CourseCardinality(MealCourseKind.FIRST, 1, 1),
                    CourseCardinality(MealCourseKind.SECOND, 1, 1),
                ),
                coverage=RequiredCourseCoverage.PER_PARTICIPANT,
            )
            draft = make_complete_diagnostic_revision(
                prior=anchored,
                proposal=proposal,
                rule=rule,
                selection_details={selection.selection.id: selection},
                created_at=CREATED,
            )
            if draft.plan.supersedes_plan_id != anchored.plan.id:
                raise ValueError("Diagnostic composition lost manual anchor")
            with SqlAlchemyMealPlanUnitOfWork(
                engine, enable_internal_composition_writes=True
            ) as scope:
                persist_diagnostic_composition_revision(
                    scope,
                    draft,
                    excluded_food_codes_by_member={member.id: frozenset()},
                    excluded_allergen_codes_by_member={member.id: frozenset()},
                )
                scope.commit()
            preview = preview_from_database(
                database_path=config.path,
                household_id=household.id,
                plan_id=draft.plan.id,
                captured_at=CREATED,
            )
            inventory = inventory_from_database(
                database_path=config.path,
                household_id=household.id,
                plan_id=draft.plan.id,
                captured_at=CREATED,
            )
            target_card = preview["days"][0]["events"][0]
            if (
                len(preview["days"]) != 7
                or any(len(day["events"]) != 1 for day in preview["days"])
                or [c["course_ru"] for c in target_card["courses"]]
                != ["Первое", "Второе"]
                or inventory["verdict"] != "NO_GO_TO_CONSUMER_COMPOSED_MEALS"
                or inventory["shopping_source_fingerprint"]
                != preview["source_fingerprint"]
                or preview["price_status"] != "UNKNOWN"
            ):
                raise ValueError("Composed MealPlan, Shopping or evidence mismatch")

            shopping = [
                {
                    "food_ru": item["food_ru"],
                    "unit": item["unit"],
                    "required": item["required"],
                    "to_buy": item["to_buy"],
                }
                for item in preview["grocery"]
            ]
            semantic = {
                "week_start": preview["week_start"],
                "event_count": sum(len(x["events"]) for x in preview["days"]),
                "composed_event_count": inventory["composition_events"],
                "individual_component_servings": sum(
                    len(x["member_servings"]) for x in inventory["components"]
                ),
                "source_courses": source_rows,
                "shopping": shopping,
                "shopping_status": preview["shopping_status"],
                "price_status": preview["price_status"],
            }
            if semantic["event_count"] != 7 or semantic["composed_event_count"] != 1:
                raise ValueError("Incomplete seven-day persisted composed revision")
            return {
                "schema": SCHEMA,
                "scope": "ISOLATED_SYNTHETIC_MEMBER_REAL_CURATED_RECIPES",
                "decision": "NO_GO_FOR_CONSUMER_OR_PHYSICAL_SERVING",
                "source_pairing": "MANUAL_CROSS_SOURCE_RESEARCH_NOT_PUBLISHED_MENU",
                "core_ai_enabled": False,
                "semantic_sha256": _hash(semantic),
                "evidence": semantic,
                "limitations": {
                    "reviewed_source_provenance": True,
                    "course_suitability_independently_approved": False,
                    "member_portion_mass_validated": False,
                    "nutrition_fully_complete": False,
                    "safe_prep_approved": False,
                    "customer_activation": False,
                    "no_production_data_modified": True,
                },
            }
        finally:
            engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Real-source diagnostic week proof")
    parser.parse_args()
    print(
        json.dumps(build_research_proof(), ensure_ascii=False, sort_keys=True, indent=2)
    )


if __name__ == "__main__":
    main()
