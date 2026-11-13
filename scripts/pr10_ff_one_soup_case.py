"""One concrete source/Serving decision: MR 2019 vegetarian cabbage soup.

Source output is a declared 350 g cooked product for the 12+ branch. It
supports the original REFERENCE portion, NOT a linearly scaled member mass,
physical upper bound, adult recommendation, or a Planner runtime policy.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, localcontext

RECIPE_CODE = "MR2019_1_2A_VEGETARIAN_CABBAGE_SOUP"
CARD_CODE = "1.2а"
DATE = "2026-11-03"
POSITION = 3
SOURCE_DOCUMENT_SHA256 = (
    "973acb53eee7a04c76853dff80988a0f9b70e704495b715639cd8a34a747293e"
)
SOURCE_CARD_SHA256 = "b209172357918043f9f92d485a8967a71d41dbcfaf69609ecb3781af983b45a9"
SOURCE_URL = (
    "https://sudact.ru/law/mr-240162-19-24-gigiena-detei-i-podrostkov/"
    "prilozhenie-5/supy/tekhnologicheskaia-karta-n-1.2a/"
)
SCHEMA = "PR10_FF_ONE_RECIPE_SOUP_OUTPUT_CASE_V1"
NO_GO = "NO_GO_INDIVIDUAL_PHYSICAL_FEASIBILITY_NOT_PROVEN"


class SoupCaseBlocked(ValueError):
    """Source or persisted MealEvent evidence did not match the pinned case."""


def _decimal(raw, name):
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise SoupCaseBlocked(f"Invalid {name}") from exc
    if not value.is_finite() or value <= 0:
        raise SoupCaseBlocked(f"Non-positive or nonfinite {name}")
    return value


def check_one_soup(*, portion_audit, source_frozen, recipe_detail):
    """Use already verified R3-D source bundle + actual persisted portion audit.

    Caller must obtain source_frozen through r3d._load_contract(), which checks
    the raw document/card hashes and actual 12+ ingredient/yield extraction.
    Caller must build portion_audit from the *same* persisted MealPlan/Servings.
    """
    if (
        portion_audit.get("schema") != "PR10_FF_PORTION_REALITY_AUDIT_V1"
        or portion_audit.get("status") != "PHYSICAL_FEASIBILITY_NOT_PROVEN"
        or portion_audit.get("physically_reviewed_servings") != 0
    ):
        raise SoupCaseBlocked("Missing actual non-release portion evidence")

    source = source_frozen.get("source", {})
    selected = source_frozen.get("selected", [])
    rows = [row for row in selected if row.get("canonical_code") == RECIPE_CODE]
    if len(rows) != 1:
        raise SoupCaseBlocked("One exact source card required")
    card = rows[0]
    if (
        source.get("source_document_raw_bytes_sha256") != SOURCE_DOCUMENT_SHA256
        or card.get("source_card_raw_sha256") != SOURCE_CARD_SHA256
        or card.get("source_page_url") != SOURCE_URL
        or card.get("source_section_code") != "APPENDIX_5"
        or card.get("source_card_code") != CARD_CODE
        or card.get("source_variant") != "12_PLUS"
        or card.get("source_output_g") != "350"
        or card.get("energy_kcal") != "112"
        or card.get("prepared_authority", {}).get("available") != {"ENERGY_KCAL": "112"}
    ):
        raise SoupCaseBlocked("Source output/energy/12+ card pin changed")

    if (
        recipe_detail.recipe.canonical_code != RECIPE_CODE
        or recipe_detail.version.version_number != 1
        or recipe_detail.version.source_name != "RU_MR_2_4_0162_19"
        or recipe_detail.version.source_recipe_id != "APPENDIX_5_CARD_1.2а"
        or recipe_detail.version.source_document_sha256 != SOURCE_DOCUMENT_SHA256
        or recipe_detail.version.source_url != SOURCE_URL
        or recipe_detail.version.source_original_servings != Decimal(1)
        or recipe_detail.version.base_servings != Decimal(1)
        or recipe_detail.version.source_output_g != Decimal(350)
        or not recipe_detail.version.source_output_text.startswith(
            "Выход готовой продукции: 350 г;"
        )
    ):
        raise SoupCaseBlocked("Published RecipeVersion does not bind source output")

    # Every published source ingredient must match this exact variant, not a
    # similarly named soup with sour cream or a different age branch.
    source_foods = {
        row["food_code"]: _decimal(row["quantity_g"], "source ingredient")
        for row in card.get("ingredients", [])
    }
    if len(card.get("ingredients", [])) != 7 or source_foods != {
        "CABBAGE_GREEN": Decimal(69),
        "POTATO": Decimal(35),
        "CARROT": Decimal(14),
        "TOMATO": Decimal("15.7"),
        "ONION_BULB_FRESH": Decimal(7),
        "VEGETABLE_OIL_REFINED_UNSPECIFIED": Decimal(6),
        "WATER": Decimal(309),
    }:
        raise SoupCaseBlocked("Wrong sauce/age/form recipe branch")

    cases = [
        row
        for row in portion_audit.get("rows", [])
        if row.get("recipe_code") == RECIPE_CODE
    ]
    if (
        len(cases) != 3
        or {row["member_ordinal"] for row in cases} != {1, 2, 3}
        or any(
            row.get("date") != DATE
            or row.get("position") != POSITION
            or row.get("role") != "DINNER"
            or row.get("physical_feasibility") != "NOT_PROVEN"
            or row.get("source_output_g_raw") != "350.000000"
            for row in cases
        )
    ):
        raise SoupCaseBlocked("Wrong meal/member or unproven physical PASS")

    participants = []
    for row in sorted(cases, key=lambda x: x["member_ordinal"]):
        factor = _decimal(row["portion_factor"], "persisted Serving factor")
        energy = _decimal(row["technical_energy_kcal"], "technical energy-only kcal")
        # Only a dimensional sensitivity estimate: no validated linear batch
        # scale, output-form-specific loss, physical bounds or adult policy.
        with localcontext() as ctx:
            ctx.prec = 50
            sensitivity = Decimal(350) * factor
            expected_energy = (Decimal(112) * factor).quantize(Decimal("0.001"))
        if expected_energy != energy:
            raise SoupCaseBlocked("Energy/Serving differs from source 112 kcal")
        participants.append(
            {
                "member_ordinal": row["member_ordinal"],
                "portion_factor": format(factor, ".6f"),
                "technical_energy_kcal": format(energy, ".3f"),
                "conditional_if_linear_output_g": format(sensitivity, ".4f"),
                "calculated_mass_is_not_verified": True,
                "physical_feasibility": "NOT_PROVEN",
            }
        )

    return {
        "schema": SCHEMA,
        "decision": NO_GO,
        "source_card": "APPENDIX_5_CARD_1.2а",
        "source_card_sha256": SOURCE_CARD_SHA256,
        "source_document_sha256": SOURCE_DOCUMENT_SHA256,
        "source_url": SOURCE_URL,
        "source_branch": "12_PLUS_INSTITUTIONAL_NOT_ADULT_PORTION_POLICY",
        "recipe_code": RECIPE_CODE,
        "date": DATE,
        "position": POSITION,
        "source_declared_final_output_g_per_portion": "350",
        "source_declared_kcal_per_portion": "112",
        "source_output_mapping": "PASS_EXACT_ONE_BASE_SERVING",
        "source_variant_ingredients_exactly_seven": True,
        "participants": participants,
        "linear_mass_projection_status": "SENSITIVITY_ONLY_NOT_APPLICABLE_AS_FACT",
        "physical_portion_approval": "NOT_PROVEN",
        "reason": "NO_REVIEWED_MEMBER_PHYSICAL_POLICY_OR_BATCH_SCALE_AUTHORITY",
        "planner_change": "NONE",
        "gate2_pass": False,
    }


def render_case(case):
    """Human-readable decision for one real meal, never a serving prescription."""
    if (
        case.get("schema") != SCHEMA
        or case.get("decision") != NO_GO
        or case.get("physical_portion_approval") != "NOT_PROVEN"
        or case.get("gate2_pass") is not False
        or len(case.get("participants", [])) != 3
        or any(
            row.get("physical_feasibility") != "NOT_PROVEN"
            or row.get("calculated_mass_is_not_verified") is not True
            for row in case["participants"]
        )
    ):
        raise SoupCaseBlocked("Invalid one-recipe review or readiness claim")
    output = [
        "# Одно блюдо: щи из свежей капусты вегетарианские",
        "",
        (
            "Внешний нормативный первоисточник: МР 2.4.0162-19, приложение 5, "
            "карта 1.2а, вариант 12 лет и старше. Выход **готового** блюда "
            "**350 г на нормативную порцию**, техническая энергия 112 ккал."
        ),
        (
            "Это отраслевой детский/учрежденческий источник, "
            "а не принятая политика порций взрослой семьи."
        ),
        "",
        f"Источник: {case['source_url']}",
        "",
        (
            "**Решение: NO-GO для утверждения физических порций.** "
            "Доказан выход одной нормативной порции, но не допустимая масса "
            "фактического индивидуального ужина."
        ),
        "",
        (
            "| Участник тестовой семьи | Базовые доли | Energy-only, ккал | "
            "Если бы масштабирование было линейным, г (НЕ подтверждённая масса) |"
        ),
        "| ---: | ---: | ---: | ---: |",
    ]
    for row in case["participants"]:
        output.append(
            f"| {row['member_ordinal']} | {row['portion_factor']} | "
            f"{row['technical_energy_kcal']} | "
            f"{row['conditional_if_linear_output_g']} |"
        )
    output.extend(
        [
            "",
            (
                "Коэффициенты сохраняются как факты исторического MealPlan. "
                "Условная масса показана только как проверка масштаба: "
                "она НЕ является рецептурной нормой или реальным выходом партии."
            ),
            "",
            (
                "Конкретный пробел: отсутствует независимо утверждённое правило "
                "допустимости физических порций для этого блюда/приёма пищи/участника "
                "и подтверждение линейной применимости выхода при масштабировании."
            ),
            (
                "Нельзя автоматически считать один низкокалорийный суп полноценным "
                "ужином только из-за подгонки коэффициента к энергетической цели."
            ),
            "",
            "**Ни RecipeVersion, ни Planner, ни Serving, ни Shopping не изменены.**",
            "Prep, Gate2 и использование реальной семьёй по-прежнему NO-GO.",
            "",
        ]
    )
    return "\n".join(output)
