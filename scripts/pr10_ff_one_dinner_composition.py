"""One non-release two-dish dinner proposal over accepted persisted source truth.

This is a useful deterministic *alternative* to multiplying a low-energy soup.
It is NOT a MealPlan/Serving/Shopping write, physical feasibility admission,
adult portion recommendation or supported multi-component Planner runtime.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext

from app.domain.units import UnitCode
from scripts.pr10_ff_one_soup_case import (
    DATE,
    NO_GO,
    RECIPE_CODE as SOUP_CODE,
    SOURCE_DOCUMENT_SHA256,
    SoupCaseBlocked,
)

SCHEMA = "PR10_FF_ONE_DINNER_TWO_COMPONENT_PROPOSAL_V1"
DECISION = "DIAGNOSTIC_ONLY_NOT_A_MEALPLAN"
CHICKEN_CODE = "MR2019_2_14_BOILED_CHICKEN_CATEGORY_1"
CHICKEN_CARD_SHA = "6b5a0849d1ff302115045dd557096e4f52d17b14ebe67c90dd51603ac58fdcf6"
CHICKEN_SOURCE_URL = (
    "https://sudact.ru/law/mr-240162-19-24-gigiena-detei-i-podrostkov/"
    "prilozhenie-5/miasnye-bliuda/tekhnologicheskaia-karta-n-2.14/"
)
SOUP_KCAL = Decimal(112)
CHICKEN_KCAL = Decimal(267)
SOUP_SOURCE_OUTPUT_G = Decimal(350)
CHICKEN_SOURCE_OUTPUT_G = Decimal(110)
PORTION_STEP = Decimal("0.000001")
ENERGY_STEP = Decimal("0.001")
MEMBER_DAY = 2  # Tuesday 2026-11-03, explicitly in the frozen fixture


class CompositionBlocked(ValueError):
    """The single-dinner alternative cannot be grounded to accepted sources."""


def _positive(value, subject):
    if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
        raise CompositionBlocked(f"Invalid {subject}")
    return value


def _parse(value, subject):
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CompositionBlocked(f"Invalid {subject}") from exc
    return _positive(parsed, subject)


def _check_chicken(*, source_frozen, detail, foods_by_id, candidate_inputs):
    """Check real RecipeVersion ingredients/energy against the accepted R3-D card."""
    cards = [
        row
        for row in source_frozen.get("selected", [])
        if row.get("canonical_code") == CHICKEN_CODE
    ]
    if len(cards) != 1:
        raise CompositionBlocked("Missing exact source chicken card")
    card = cards[0]
    if (
        source_frozen.get("source", {}).get("source_document_raw_bytes_sha256")
        != SOURCE_DOCUMENT_SHA256
        or card.get("source_section_code") != "APPENDIX_5"
        or card.get("source_card_code") != "2.14"
        or card.get("source_variant") != "12_PLUS"
        or card.get("source_card_raw_sha256") != CHICKEN_CARD_SHA
        or card.get("source_page_url") != CHICKEN_SOURCE_URL
        or card.get("source_output_g") != "110"
        or card.get("energy_kcal") != "267"
        or card.get("prepared_authority", {}).get("available")
        != {"ENERGY_KCAL": "267"}
    ):
        raise CompositionBlocked("Chicken source identity/output/kcal drift")

    v = detail.version
    if (
        detail.recipe.canonical_code != CHICKEN_CODE
        or v.version_number != 1
        or v.source_name != "RU_MR_2_4_0162_19"
        or v.source_document_sha256 != SOURCE_DOCUMENT_SHA256
        or v.source_recipe_id != "APPENDIX_5_CARD_2.14"
        or v.source_url != CHICKEN_SOURCE_URL
        or v.base_servings != Decimal(1)
        or v.source_original_servings != Decimal(1)
        or v.source_output_g != CHICKEN_SOURCE_OUTPUT_G
        or not v.source_output_text.startswith("Выход готовой продукции: 110 г;")
    ):
        raise CompositionBlocked("Persisted chicken RecipeVersion source is different")

    candidate = [
        row for row in candidate_inputs if row.get("canonical_code") == CHICKEN_CODE
    ]
    if (
        len(candidate) != 1
        or candidate[0].get("recipe_version_id") != str(v.id)
        or candidate[0].get("exact_energy_ready") is not True
        or candidate[0].get("nutrition_status") != "INCOMPLETE"
        or _parse(candidate[0].get("kcal_per_base_serving"), "chicken kcal")
        != CHICKEN_KCAL
    ):
        raise CompositionBlocked("Candidate not pinned to energy-only chicken source")

    expected_source = {
        "CHICKEN_CATEGORY_1_WHOLE_RAW": Decimal(155),
        "CARROT": Decimal(8),
        "SALT_IODIZED": Decimal(1),
    }
    source_ingredients = card.get("ingredients", [])
    if (
        len(source_ingredients) != 3
        or {
            row["food_code"]: _parse(row["quantity_g"], "source chicken quantity")
            for row in source_ingredients
        }
        != expected_source
    ):
        raise CompositionBlocked("Chicken source ingredients differ")

    stored = getattr(detail, "ingredients", None)
    if not isinstance(stored, (tuple, list)) or len(stored) != 3:
        raise CompositionBlocked("Persisted chicken ingredients are missing")
    observed = {}
    for ingredient in stored:
        food = foods_by_id.get(ingredient.food_ingredient_id)
        if (
            food is None
            or food.id != ingredient.food_ingredient_id
            or not food.is_active
            or food.default_unit is not UnitCode.GRAM
            or ingredient.recipe_version_id != v.id
            or ingredient.unit is not UnitCode.GRAM
            or ingredient.optional is not False
            or not isinstance(ingredient.quantity, Decimal)
        ):
            raise CompositionBlocked("Unverified persisted chicken FoodIngredient")
        code = food.canonical_code
        if code in observed:
            raise CompositionBlocked("Duplicated chicken FoodIngredient")
        observed[code] = _positive(ingredient.quantity, "persisted chicken quantity")
    if observed != expected_source:
        raise CompositionBlocked("Persisted chicken amounts differ from R3-D card")
    return tuple(sorted(observed))


def propose_one_dinner(
    *,
    soup_case,
    chicken_detail,
    chicken_foods,
    source_frozen,
    candidate_inputs,
    members,
):
    """Compare fixed one-source-portion soup plus exact-kcal chicken remainder.

    The one soup portion is a *study input*, not a member-approved prescription.
    Chicken factor is derived from the energy-only gap and rounded to Serving
    precision, keeping the tiny residual explicit. All adult/child feasibility
    and scaled cooked-mass claims remain NOT_PROVEN.
    """
    if (
        soup_case.get("decision") != NO_GO
        or soup_case.get("physical_portion_approval") != "NOT_PROVEN"
        or soup_case.get("source_output_mapping") != "PASS_EXACT_ONE_BASE_SERVING"
        or soup_case.get("recipe_code") != SOUP_CODE
        or soup_case.get("date") != DATE
        or soup_case.get("position") != 3
        or soup_case.get("source_declared_final_output_g_per_portion") != "350"
        or soup_case.get("source_declared_kcal_per_portion") != "112"
        or soup_case.get("gate2_pass") is not False
        or len(soup_case.get("participants", [])) != 3
    ):
        raise CompositionBlocked("Missing exact one-soup persisted diagnostic receipt")

    food_codes = _check_chicken(
        source_frozen=source_frozen,
        detail=chicken_detail,
        foods_by_id=chicken_foods,
        candidate_inputs=candidate_inputs,
    )
    soup_food_codes = {
        "CABBAGE_GREEN",
        "POTATO",
        "CARROT",
        "TOMATO",
        "ONION_BULB_FRESH",
        "VEGETABLE_OIL_REFINED_UNSPECIFIED",
        "WATER",
    }
    member_map = {m["ordinal"]: m for m in members}
    if len(member_map) != 3 or set(member_map) != {1, 2, 3}:
        raise CompositionBlocked("Missing or duplicate generation member semantics")
    result_members = []
    for participant in sorted(
        soup_case["participants"], key=lambda row: row["member_ordinal"]
    ):
        ordinal = participant["member_ordinal"]
        member = member_map.get(ordinal)
        if (
            member is None
            or participant.get("physical_feasibility") != "NOT_PROVEN"
            or participant.get("calculated_mass_is_not_verified") is not True
        ):
            raise CompositionBlocked("Unknown member or false physical approval")
        exclusions = member.get("excluded_food_codes")
        if (
            not isinstance(exclusions, list)
            or len(set(exclusions)) != len(exclusions)
            or (set(exclusions) & (set(food_codes) | soup_food_codes))
        ):
            raise CompositionBlocked("Missing exclusions or unsuitable chicken/soup")
        opportunities = [
            item for item in member.get("opportunities", [])
            if item["weekday"] == MEMBER_DAY and item["role"] == "DINNER"
        ]
        if len(opportunities) != 1:
            raise CompositionBlocked("Missing accepted member DINNER opportunity")
        share = _parse(opportunities[0]["energy_share"], "dinner energy share")
        reference = _parse(member.get("reference_energy_kcal"), "member reference")
        target = _parse(participant.get("technical_energy_kcal"), "pinned dinner kcal")
        original = _parse(participant.get("portion_factor"), "existing soup factor")
        with localcontext() as ctx:
            ctx.prec = 50
            reference_target = reference * share
            if abs(reference_target - target) > ENERGY_STEP:
                raise CompositionBlocked("Energy goal not bound to accepted member share")
            if abs(original * SOUP_KCAL - target) > ENERGY_STEP:
                raise CompositionBlocked("Existing soup share differs from source kcal")
            remaining = target - SOUP_KCAL
            if remaining <= 0:
                raise CompositionBlocked("The fixed soup already fills the opportunity")
            chicken_factor = (remaining / CHICKEN_KCAL).quantize(
                PORTION_STEP, rounding=ROUND_HALF_EVEN
            )
            _positive(chicken_factor, "hypothetical chicken factor")
            approximate_energy = SOUP_KCAL + CHICKEN_KCAL * chicken_factor
            residual = target - approximate_energy
            # Half a Serving quantum times chicken energy is the rounding bound.
            if abs(residual) > CHICKEN_KCAL * PORTION_STEP / 2:
                raise CompositionBlocked("Unbounded energy reconciliation")
            sensitivity_g = SOUP_SOURCE_OUTPUT_G + (
                chicken_factor * CHICKEN_SOURCE_OUTPUT_G
            )
        result_members.append(
            {
                "member_ordinal": ordinal,
                "energy_only_target_kcal": format(target, ".3f"),
                "old_soup_only_factor": format(original, ".6f"),
                "soup_component_factor_test_input": "1.000000",
                "chicken_component_factor_study": format(chicken_factor, ".6f"),
                "technical_energy_kcal": format(approximate_energy, ".6f"),
                "unfilled_energy_kcal": format(residual, ".6f"),
                "conditional_if_both_outputs_linear_g": format(sensitivity_g, ".6f"),
                "conditional_mass_not_verified": True,
                "physical_feasibility": "NOT_PROVEN",
            }
        )
    if [m["member_ordinal"] for m in result_members] != [1, 2, 3]:
        raise CompositionBlocked("Unexpected diagnostic member coverage")

    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "source_date": DATE,
        "meal_role": "DINNER",
        "original_soup_recipe_code": SOUP_CODE,
        "alternative_second_recipe_code": CHICKEN_CODE,
        "chicken_source_card_sha256": CHICKEN_CARD_SHA,
        "chicken_source_output_g_per_original_portion": "110",
        "soup_source_output_g_per_original_portion": "350",
        "energy_only": True,
        "source_recipe_ingredients_verified": True,
        "user_accepted_composition": False,
        "hypothetical_soup_base_factor": "1.000000",
        "physical_portion_approval": "NOT_PROVEN",
        "batch_scale_approval": "NOT_PROVEN",
        "shopping_demand_authority": "NONE",
        "prep_release": False,
        "gate2_pass": False,
        "members": result_members,
    }


def render_markdown(proposal):
    """Explain one energy-only compositional hypothesis in human terms."""
    if (
        proposal.get("schema") != SCHEMA
        or proposal.get("decision") != DECISION
        or proposal.get("physical_portion_approval") != "NOT_PROVEN"
        or proposal.get("batch_scale_approval") != "NOT_PROVEN"
        or proposal.get("shopping_demand_authority") != "NONE"
        or proposal.get("user_accepted_composition") is not False
        or proposal.get("gate2_pass") is not False
        or len(proposal.get("members", [])) != 3
        or any(
            r.get("physical_feasibility") != "NOT_PROVEN"
            or r.get("conditional_mass_not_verified") is not True
            for r in proposal["members"]
        )
    ):
        raise CompositionBlocked("Composite dinner cannot claim production readiness")
    lines = [
        "# Один ужин из двух блюд — расчётный прототип",
        "",
        "**Внутренний прототип. НЕ сохранённый MealPlan, НЕ готовое меню для семьи.**",
        "",
        "Исходный ужин 3 ноября состоял только из вегетарианских щей, "
        "для которых Planner назначил большие коэффициенты порций.",
        "",
        "Проверяем **одну явно заданную гипотезу**: оставить каждому по одной "
        "нормативной базовой порции щей (350 г, 112 ккал) и математически "
        "распределить оставшуюся энергию на проверенную отварную курицу "
        "(нормативный выход 110 г, 267 ккал на базовую порцию).",
        "",
        "Это НЕ физиологическая норма, не установленный объём готовой порции, "
        "не разрешение на линейное приготовление партии и не подтверждение, "
        "что сочетание подходит человеку. КБЖУ неполные.",
        "",
        "| Участник | Цель, ккал | Было: доли щей | Тест: щи | Тест: курица | "
        "Энергия теста, ккал | Остаток, ккал | "
        "Условная масса при линейном выходе, г (НЕ подтверждена) |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in proposal["members"]:
        lines.append(
            f"| {row['member_ordinal']} | {row['energy_only_target_kcal']} "
            f"| {row['old_soup_only_factor']} | {row['soup_component_factor_test_input']} "
            f"| {row['chicken_component_factor_study']} | "
            f"{row['technical_energy_kcal']} | {row['unfilled_energy_kcal']} "
            f"| {row['conditional_if_both_outputs_linear_g']} |"
        )
    lines.extend(
        [
            "",
            "Все исходные MealEvents/Servings, RecipeVersions и Shopping сохранены "
            "без изменений. Суммы здесь не создают покупки и не подтверждают "
            "реальную потребность в продуктах.",
            "",
            "Для перехода в Planner нужны отдельные доказательства: приемлемость "
            "каждого компонента для участника, применимость исходного выхода к "
            "масштабированию, политика физической порции, модель нескольких "
            "компонентов одного MealEvent и перерасчёт Shopping без дублей.",
            "",
            "**Вывод:** технически можно составить двухкомпонентный вариант "
            "без шестикратного увеличения *супа*. Физическая пригодность "
            "варианта по-прежнему NOT_PROVEN, релиз/Gate2 NO-GO.",
            "",
        ]
    )
    return "\n".join(lines)
