"""Concrete source-backed two-component dinner hypothesis, not a new MealPlan."""

from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace as Row
from uuid import uuid4

import pytest
from app.domain.units import UnitCode
from app.seed import r3d_final_dc3_batch as r3d
from app.tests.test_pr10_ff_one_soup_case import _source_fixture

from scripts import pr10_ff_one_dinner_composition as composition
from scripts import pr10_ff_one_soup_case as soup


def _case():
    frozen, _, bundle = r3d._load_contract()
    seeds, _ = r3d._recipe_seeds_and_specs(frozen, bundle)
    candidate = next(
        seed for seed in seeds if seed.canonical_code == composition.CHICKEN_CODE
    )
    version_id = uuid4()
    version = Row(**{**vars(candidate.version), "id": version_id, "version_number": 1})
    foods = {
        ingredient.food_ingredient_code: uuid4()
        for ingredient in candidate.version.ingredients
    }
    chicken_foods = {
        uuid: Row(
            id=uuid,
            canonical_code=code,
            default_unit=UnitCode.GRAM,
            is_active=True,
        )
        for code, uuid in foods.items()
    }
    chicken = Row(
        recipe=Row(canonical_code=candidate.canonical_code),
        version=version,
        ingredients=tuple(
            Row(
                recipe_version_id=version_id,
                food_ingredient_id=foods[item.food_ingredient_code],
                unit=UnitCode.GRAM,
                quantity=item.quantity,
                optional=False,
            )
            for item in candidate.version.ingredients
        ),
    )
    _, soup_detail, audit, soup_foods = _source_fixture()
    reference_case = soup.check_one_soup(
        portion_audit=audit,
        source_frozen=frozen,
        recipe_detail=soup_detail,
        foods_by_id=soup_foods,
    )
    members = [
        {
            "ordinal": ordinal,
            "excluded_food_codes": exclusions,
            "reference_energy_kcal": reference,
            "opportunities": [
                {
                    "weekday": 2,
                    "role": "DINNER",
                    "energy_share": "0.25",
                }
            ],
        }
        for ordinal, exclusions, reference in (
            (1, [], "2371.79"),
            (2, [], "2757.49"),
            (3, ["BEEF_CATEGORY_1_RAW"], "2371.79"),
        )
    ]
    candidate_inputs = [
        {
            "canonical_code": composition.CHICKEN_CODE,
            "recipe_version_id": str(version_id),
            "nutrition_status": "INCOMPLETE",
            "exact_energy_ready": True,
            "kcal_per_base_serving": "267",
        }
    ]
    return {
        "soup_case": reference_case,
        "chicken_detail": chicken,
        "chicken_foods": chicken_foods,
        "source_frozen": frozen,
        "candidate_inputs": candidate_inputs,
        "members": members,
    }


def test_one_real_soup_dinner_can_have_two_components_with_energy_ledger():
    proposal = composition.propose_one_dinner(**_case())
    assert proposal["decision"] == composition.DECISION
    assert proposal["user_accepted_composition"] is False
    assert proposal["shopping_demand_authority"] == "NONE"
    assert proposal["gate2_pass"] is False
    assert proposal["physical_portion_approval"] == "NOT_PROVEN"
    assert [row["chicken_component_factor_study"] for row in proposal["members"]] == [
        "1.801300",
        "2.162446",
        "1.801300",
    ]
    assert [row["technical_energy_kcal"] for row in proposal["members"]] == [
        "592.947100",
        "689.373082",
        "592.947100",
    ]
    assert [
        row["conditional_if_both_outputs_linear_g"] for row in proposal["members"]
    ] == ["548.143000", "587.869060", "548.143000"]
    assert all(row["physical_feasibility"] == "NOT_PROVEN" for row in proposal["members"])
    text = composition.render_markdown(proposal)
    assert "расчётный прототип" in text
    assert "587.869060" in text
    assert "НЕ подтверждена" in text
    assert "не создают покупки" in text


@pytest.mark.parametrize(
    "mutation",
    [
        "chicken_missing_row",
        "chicken_food_replaced",
        "chicken_amount_drift",
        "chicken_non_g",
        "chicken_source_yield_drift",
        "chicken_source_energy_drift",
        "wrong_chicken_recipe",
        "wrong_chicken_energy_pin",
        "chicken_unknown_energy",
        "excluded_chicken",
        "excluded_soup",
        "lost_exclusion_authority",
        "missing_dinner",
        "bad_reference_energy",
        "duplicate_member",
        "false_soup_physical_pass",
        "wrong_soup_dinner",
        "different_target_energy",
    ],
)
def test_one_dinner_fails_closed_on_untrusted_source_or_member(mutation):
    data = _case()
    if mutation == "chicken_missing_row":
        data["chicken_detail"].ingredients = data["chicken_detail"].ingredients[1:]
    elif mutation == "chicken_food_replaced":
        data["chicken_detail"].ingredients[0].food_ingredient_id = uuid4()
    elif mutation == "chicken_amount_drift":
        data["chicken_detail"].ingredients[0].quantity += Decimal("0.001")
    elif mutation == "chicken_non_g":
        data["chicken_detail"].ingredients[0].unit = UnitCode.MILLILITER
    elif mutation == "chicken_source_yield_drift":
        row = next(
            x for x in data["source_frozen"]["selected"]
            if x["canonical_code"] == composition.CHICKEN_CODE
        )
        row["source_output_g"] = "75"
    elif mutation == "chicken_source_energy_drift":
        row = next(
            x for x in data["source_frozen"]["selected"]
            if x["canonical_code"] == composition.CHICKEN_CODE
        )
        row["energy_kcal"] = "268"
    elif mutation == "wrong_chicken_recipe":
        data["chicken_detail"].version.source_recipe_id = "APPENDIX_5_CARD_2.15"
    elif mutation == "wrong_chicken_energy_pin":
        data["candidate_inputs"][0]["kcal_per_base_serving"] = "268"
    elif mutation == "chicken_unknown_energy":
        data["candidate_inputs"][0]["exact_energy_ready"] = False
    elif mutation == "excluded_chicken":
        data["members"][2]["excluded_food_codes"].append(
            "CHICKEN_CATEGORY_1_WHOLE_RAW"
        )
    elif mutation == "excluded_soup":
        data["members"][2]["excluded_food_codes"].append("CABBAGE_GREEN")
    elif mutation == "lost_exclusion_authority":
        del data["members"][0]["excluded_food_codes"]
    elif mutation == "missing_dinner":
        data["members"][0]["opportunities"] = []
    elif mutation == "bad_reference_energy":
        data["members"][1]["reference_energy_kcal"] = "1999"
    elif mutation == "duplicate_member":
        data["members"][2]["ordinal"] = 1
    elif mutation == "false_soup_physical_pass":
        data["soup_case"]["physical_portion_approval"] = "PASS"
    elif mutation == "wrong_soup_dinner":
        data["soup_case"]["position"] = 2
    elif mutation == "different_target_energy":
        data["soup_case"]["participants"][1]["technical_energy_kcal"] = "700"
    with pytest.raises(composition.CompositionBlocked):
        composition.propose_one_dinner(**data)


def test_renderer_rejects_false_plan_or_physical_promotion():
    result = composition.propose_one_dinner(**_case())
    for key, value in (
        ("decision", "ACCEPTED_MEALPLAN"),
        ("physical_portion_approval", "PASS"),
        ("shopping_demand_authority", "AUTHORITATIVE"),
        ("gate2_pass", True),
        ("user_accepted_composition", True),
    ):
        bad = deepcopy(result)
        bad[key] = value
        with pytest.raises(composition.CompositionBlocked):
            composition.render_markdown(bad)
