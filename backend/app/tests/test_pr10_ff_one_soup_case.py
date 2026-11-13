"""One exact normative soup and three actual synthetic Serving factors."""

from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace as Row
from uuid import uuid4

import pytest
from app.domain.units import UnitCode
from app.seed import r3d_final_dc3_batch as r3d

from scripts import pr10_ff_one_soup_case as case


def _source_fixture():
    # Accepted source loader independently checks real bundled document/card
    # bytes, R3-D SHA pins, net ingredients and finished 12+ output values.
    frozen, _, bundle = r3d._load_contract()
    seeds, _ = r3d._recipe_seeds_and_specs(frozen, bundle)
    seed = next(s for s in seeds if s.canonical_code == case.RECIPE_CODE)
    version_id = uuid4()
    version = Row(
        **{
            **vars(seed.version),
            "id": version_id,
            "version_number": 1,
        }
    )
    # Independent RecipeIngredient-shaped persisted rows and canonical Food
    # identity lookup. Tests mutate these, not the frozen source card.
    food_ids = {row.food_ingredient_code: uuid4() for row in seed.version.ingredients}
    foods_by_id = {
        fid: Row(
            id=fid, canonical_code=code, default_unit=UnitCode.GRAM, is_active=True
        )
        for code, fid in food_ids.items()
    }
    detail = Row(
        recipe=Row(canonical_code=seed.canonical_code),
        version=version,
        ingredients=tuple(
            Row(
                recipe_version_id=version_id,
                food_ingredient_id=food_ids[item.food_ingredient_code],
                quantity=item.quantity,
                unit=UnitCode.GRAM,
                position=i,
                optional=False,
            )
            for i, item in enumerate(seed.version.ingredients, 1)
        ),
    )
    frozen_rows = [
        ("1", "5.294174", "592.947"),
        ("2", "6.155112", "689.373"),
        ("3", "5.294174", "592.947"),
    ]
    audit = {
        "schema": "PR10_FF_PORTION_REALITY_AUDIT_V1",
        "status": "PHYSICAL_FEASIBILITY_NOT_PROVEN",
        "physically_reviewed_servings": 0,
        "rows": [
            {
                "recipe_code": case.RECIPE_CODE,
                "date": case.DATE,
                "position": case.POSITION,
                "role": "DINNER",
                "member_ordinal": int(member),
                "portion_factor": factor,
                "technical_energy_kcal": energy,
                "source_output_g_raw": "350.000000",
                "physical_feasibility": "NOT_PROVEN",
            }
            for member, factor, energy in frozen_rows
        ],
    }
    return frozen, detail, audit, foods_by_id


def test_verified_card_is_finished_350g_112kcal_but_not_sixfold_member_policy():
    frozen, detail, audit, foods_by_id = _source_fixture()
    receipt = case.check_one_soup(
        portion_audit=audit, source_frozen=frozen, recipe_detail=detail, foods_by_id=foods_by_id
    )
    assert receipt["source_output_mapping"] == "PASS_EXACT_ONE_BASE_SERVING"
    assert receipt["source_declared_final_output_g_per_portion"] == "350"
    assert receipt["source_declared_kcal_per_portion"] == "112"
    assert receipt["source_branch"].startswith("12_PLUS_INSTITUTIONAL")
    assert receipt["source_card_sha256"] == case.SOURCE_CARD_SHA256
    assert receipt["physical_portion_approval"] == "NOT_PROVEN"
    assert receipt["decision"] == case.NO_GO
    assert receipt["gate2_pass"] is False
    assert [x["conditional_if_linear_output_g"] for x in receipt["participants"]] == [
        "1852.9609",
        "2154.2892",
        "1852.9609",
    ]
    assert receipt["participants"][1]["technical_energy_kcal"] == "689.373"
    text = case.render_case(receipt)
    assert "350 г" in text
    assert "2154.2892" in text
    assert "НЕ подтверждённая масса" in text
    assert "NO-GO" in text


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_card",
        "sour_cream_branch",
        "wrong_yield",
        "wrong_energy",
        "wrong_ingredient",
        "wrong_version_base",
        "wrong_version_sha",
        "wrong_source_text",
        "swapped_technical_kcal",
        "wrong_member_factor",
        "physical_pass",
    ],
)
def test_source_or_member_correction_cannot_be_laundered(mutation):
    frozen, detail, audit, foods_by_id = _source_fixture()
    if mutation == "wrong_card":
        frozen["selected"][0]["source_card_raw_sha256"] = "0" * 64
    elif mutation == "sour_cream_branch":
        frozen["selected"][0]["source_card_code"] = "1.2"
    elif mutation == "wrong_yield":
        frozen["selected"][0]["source_output_g"] = "250"
    elif mutation == "wrong_energy":
        frozen["selected"][0]["energy_kcal"] = "128"
    elif mutation == "wrong_ingredient":
        frozen["selected"][0]["ingredients"][0]["quantity_g"] = "70"
    elif mutation == "wrong_version_base":
        detail.version.base_servings = Decimal(2)
    elif mutation == "wrong_version_sha":
        detail.version.source_document_sha256 = "0" * 64
    elif mutation == "wrong_source_text":
        detail.version.source_output_text = "raw input 350 g"
    elif mutation == "swapped_technical_kcal":
        audit["rows"][1]["technical_energy_kcal"] = "592.947"
    elif mutation == "wrong_member_factor":
        audit["rows"][1]["portion_factor"] = "0"
    elif mutation == "physical_pass":
        audit["rows"][1]["physical_feasibility"] = "PASS"
    with pytest.raises(case.SoupCaseBlocked):
        case.check_one_soup(
            portion_audit=audit, source_frozen=frozen, recipe_detail=detail, foods_by_id=foods_by_id
        )


def test_renderer_must_not_promote_physical_eligibility():
    frozen, detail, audit, foods_by_id = _source_fixture()
    receipt = case.check_one_soup(
        portion_audit=audit, source_frozen=frozen, recipe_detail=detail, foods_by_id=foods_by_id
    )
    tampered = deepcopy(receipt)
    tampered["decision"] = "PASS"
    with pytest.raises(case.SoupCaseBlocked):
        case.render_case(tampered)
    tampered = deepcopy(receipt)
    tampered["participants"][0]["physical_feasibility"] = "PASS"
    with pytest.raises(case.SoupCaseBlocked):
        case.render_case(tampered)


@pytest.mark.parametrize(
    "mutation",
    [
        "removed_ingredient",
        "different_food_identity",
        "quantity_changed",
        "unit_changed",
        "unknown_food_identity",
        "duplicate_canonical_food",
        "wrong_recipe_version_fk",
        "optional_ingredient",
        "inactive_canonical_food",
        "incompatible_canonical_unit",
    ],
)
def test_persisted_ingredient_mismatch_blocks_unmodified_source(mutation):
    frozen, detail, audit, foods_by_id = _source_fixture()
    stored = list(detail.ingredients)
    first = stored[0]
    if mutation == "removed_ingredient":
        stored.pop(0)
    elif mutation == "different_food_identity":
        replacement_id = uuid4()
        foods_by_id[replacement_id] = Row(
            id=replacement_id,
            canonical_code="UNRELATED_CANONICAL_FOOD",
            default_unit=UnitCode.GRAM,
            is_active=True,
        )
        first.food_ingredient_id = replacement_id
    elif mutation == "quantity_changed":
        first.quantity += Decimal("0.001")
    elif mutation == "unit_changed":
        first.unit = UnitCode.MILLILITER
    elif mutation == "unknown_food_identity":
        first.food_ingredient_id = uuid4()
    elif mutation == "duplicate_canonical_food":
        first.food_ingredient_id = stored[1].food_ingredient_id
    elif mutation == "wrong_recipe_version_fk":
        first.recipe_version_id = uuid4()
    elif mutation == "optional_ingredient":
        first.optional = True
    elif mutation == "inactive_canonical_food":
        foods_by_id[first.food_ingredient_id].is_active = False
    elif mutation == "incompatible_canonical_unit":
        foods_by_id[first.food_ingredient_id].default_unit = UnitCode.MILLILITER
    detail.ingredients = tuple(stored)
    with pytest.raises(case.SoupCaseBlocked, match="RecipeIngredient|FoodIngredient"):
        case.check_one_soup(
            portion_audit=audit,
            source_frozen=frozen,
            recipe_detail=detail,
            foods_by_id=foods_by_id,
        )
