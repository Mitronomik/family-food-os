"""One home-lunch composition: positive structural proof and fail-closed inputs."""

from copy import deepcopy
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
from types import SimpleNamespace as Row
from uuid import UUID, uuid4

import pytest
from app.domain.food_recipes import RightsReviewStatus, VerificationStatus
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealSourceKind
from app.domain.units import UnitCode

from scripts import pr10_ff_one_lunch_courses as lunch

ROOT = Path(__file__).resolve().parents[3]
PIN = ROOT / "docs/family-food/evidence/pr10-ff-forward-input-v1/planner-B-PROPOSED.json"


def _scene():
    # Real accepted frozen member patterns, candidate source pins and kcal.
    # RecipeIngredient shapes are explicitly synthetic unit-test fixtures;
    # full persisted SQLite readback is tested by two independent CI workers.
    raw = json.loads(PIN.read_text(encoding="utf-8"))
    event_id = uuid4()
    member_ids = {1: uuid4(), 2: uuid4(), 3: uuid4()}
    by_code = {row["canonical_code"]: row for row in raw["candidate_inputs"]}
    details, foods = {}, {}
    for label, code, _ in lunch.COURSES:
        pin = by_code[code]
        vid = UUID(pin["recipe_version_id"])
        version = Row(
            id=vid,
            version_number=pin["version_number"],
            source_document_sha256=pin["source_document_sha256"],
            source_recipe_id=pin["source_recipe_id"],
            source_name=pin["source_name"],
            verification_status=VerificationStatus.SOURCE_VERIFIED,
            rights_review_status=RightsReviewStatus.REVIEWED,
            base_servings=Decimal(1),
            meal_type_code=pin["meal_type_code"],
        )
        ingredients = []
        for product_code in pin["ingredient_codes"]:
            fid = uuid4()
            foods[fid] = Row(
                id=fid, canonical_code=product_code,
                is_active=True, default_unit=UnitCode.GRAM
            )
            ingredients.append(
                Row(
                    food_ingredient_id=fid,
                    recipe_version_id=vid,
                    optional=False,
                    unit=UnitCode.GRAM,
                    quantity=Decimal(10),
                )
            )
        details[vid] = Row(
            recipe=Row(canonical_code=code, canonical_name="Проверочное блюдо " + label),
            version=version,
            ingredients=tuple(ingredients),
        )
    second_id = UUID(by_code[lunch.COURSES[1][1]]["recipe_version_id"])
    plan = Row(
        events=(
            Row(
                id=event_id, local_date=date(2026, 11, 3),
                role=MealRole.LUNCH, source_kind=MealSourceKind.COOK_RECIPE,
                recipe_version_id=second_id
            ),
        ),
        servings=(
            Row(
                event_id=event_id, member_id=member_ids[1],
                portion_servings=Decimal("2.031139"),
            ),
        ),
    )
    return {
        "plan": plan,
        "member_ordinals": {mid: ordinal for ordinal, mid in member_ids.items()},
        "members": deepcopy(raw["members"]),
        "candidate_inputs": deepcopy(raw["candidate_inputs"]),
        "details": details,
        "foods": foods,
    }


def test_actual_selected_home_lunch_is_one_member_without_filling_missing_meals():
    result = lunch.build_lunch(**_scene())
    assert result["home_participant_ordinals"] == [1]
    assert result["non_lunch_member_ordinals"] == [2, 3]
    assert result["out_of_home_food_tracking"] == "NOT_COLLECTED"
    assert result["original_lunch_factor"] == "2.031139"
    assert result["planned_daily_share"] == "0.90"
    assert result["reference_allocated_share"] == "0.35"
    assert result["energy_reference_kcal"] == "830.126500"
    assert result["hypothetical_energy_only_kcal"] == "671.300000"
    assert result["reference_alignment_delta_kcal"] == "158.826500"
    assert result["delta_is_not_deficit_or_reallocation"] is True
    assert [c["course"] for c in result["courses"]] == [
        "FIRST", "SECOND", "DESSERT_STUDY"
    ]
    assert [c["factor"] for c in result["courses"]] == [
        "1.000000", "1.000000", "0.500000"
    ]
    assert [c["energy_only_kcal"] for c in result["courses"]] == [
        "112.000000", "408.700000", "150.600000"
    ]
    assert result["courses"][2]["dessert_role_status"] == (
        "UNREVIEWED_BREAKFAST_RECIPE_REUSE"
    )
    assert result["physical_serving_approval"] == "NOT_PROVEN"
    assert result["shopping_authority"] == "NONE"
    assert result["authoritative_mealplan"] is False
    assert result["gate2_pass"] is False
    report = lunch.render_markdown(result)
    assert "не дефицит" in report
    assert "Десертная роль" in report
    assert "питание вне" in report


def test_partial_home_schedules_are_not_completed_by_inference():
    scene = _scene()
    members = scene["members"]
    selected = lunch.selected_home_lunch(members, 2)
    assert set(selected) == {1}
    assert selected[1][2] == Decimal("0.90")
    # No outside meal rows, no false at-home breakfast or dinner for member 3.
    assert not any(
        row["role"] != "DINNER"
        for row in members[2]["opportunities"]
    )
    # A dinner-only single-member schedule is valid, but has no home lunch.
    assert lunch.selected_home_lunch([members[2]], 2) == {}
    # The member with breakfast+dinner also has no home lunch.
    assert lunch.selected_home_lunch([members[1]], 2) == {}
    # Lunch-only is allowed when explicitly selected, not completed to 100%.
    custom = deepcopy(members[0])
    custom["opportunities"] = [
        {"weekday": 2, "position": 1, "role": "LUNCH", "energy_share": "0.35"}
    ]
    assert set(lunch.selected_home_lunch([custom], 2)) == {1}


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_lunch", "extra_home_lunch", "changed_plan_event",
        "extra_plan_serving", "changed_serving_factor", "wrong_second_recipe",
        "wrong_candidate_kcal", "wrong_source_hash", "inactive_food",
        "substitute_food", "changed_ingredient_quantity_to_nan",
        "member_excluded_beef", "missing_exclusions", "share_over_all",
        "missing_member_schedule", "duplicate_role",
        "dessert_cannot_be_called_reviewed",
    ],
)
def test_realistic_lunch_prototype_fails_closed_on_untrusted_input(mutation):
    s = _scene()
    member = s["members"][0]
    detail = next(iter(s["details"].values()))
    if mutation == "missing_lunch":
        member["opportunities"] = [
            x for x in member["opportunities"]
            if not (x["weekday"] == 2 and x["role"] == "LUNCH")
        ]
    elif mutation == "extra_home_lunch":
        s["members"][1]["opportunities"].append(
            {"weekday": 2, "role": "LUNCH", "position": 3, "energy_share": "0.10"}
        )
    elif mutation == "changed_plan_event":
        s["plan"].events[0].role = MealRole.DINNER
    elif mutation == "extra_plan_serving":
        s["plan"].servings += (s["plan"].servings[0],)
    elif mutation == "changed_serving_factor":
        s["plan"].servings[0].portion_servings = Decimal("1.000000")
    elif mutation == "wrong_second_recipe":
        s["plan"].events[0].recipe_version_id = detail.version.id
    elif mutation == "wrong_candidate_kcal":
        next(
            row for row in s["candidate_inputs"]
            if row["canonical_code"] == lunch.COURSES[1][1]
        )["kcal_per_base_serving"] = "999"
        s["plan"].servings[0].portion_servings = Decimal("2.031139")
    elif mutation == "wrong_source_hash":
        detail.version.source_document_sha256 = "0" * 64
    elif mutation == "inactive_food":
        food_id = detail.ingredients[0].food_ingredient_id
        s["foods"][food_id].is_active = False
    elif mutation == "substitute_food":
        food_id = detail.ingredients[0].food_ingredient_id
        s["foods"][food_id].canonical_code = "UNRELATED_FOOD"
    elif mutation == "changed_ingredient_quantity_to_nan":
        detail.ingredients[0].quantity = Decimal("NaN")
    elif mutation == "member_excluded_beef":
        member["excluded_food_codes"] = ["BEEF_CATEGORY_1_RAW"]
    elif mutation == "missing_exclusions":
        del member["excluded_food_codes"]
    elif mutation == "share_over_all":
        member["opportunities"][0]["energy_share"] = "0.95"
    elif mutation == "missing_member_schedule":
        member["opportunities"] = []
    elif mutation == "duplicate_role":
        duplicate = next(
            x for x in member["opportunities"]
            if x["weekday"] == 2 and x["role"] == "LUNCH"
        )
        member["opportunities"].append(deepcopy(duplicate))
    elif mutation == "dessert_cannot_be_called_reviewed":
        dessert_id = UUID(
            next(
                row["recipe_version_id"] for row in s["candidate_inputs"]
                if row["canonical_code"] == lunch.COURSES[2][1]
            )
        )
        s["details"][dessert_id].version.meal_type_code = "main"
    with pytest.raises(lunch.LunchBlocked):
        lunch.build_lunch(**s)


def test_renderer_refuses_false_family_or_shopping_claims():
    good = lunch.build_lunch(**_scene())
    for key, value in [
        ("physical_serving_approval", "PASS"),
        ("dessert_course_approval", "REVIEWED"),
        ("authoritative_mealplan", True),
        ("shopping_authority", "YES"),
        ("gate2_pass", True),
    ]:
        changed = deepcopy(good)
        changed[key] = value
        with pytest.raises(lunch.LunchBlocked):
            lunch.render_markdown(changed)
