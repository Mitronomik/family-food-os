"""Internal preview: positive readable week and fail-closed non-release boundaries."""

from copy import deepcopy

import pytest

from scripts import pr10_ff_week_preview as preview


def _example():
    # Synthetic renderer fixture only; real full-week readback is covered by
    # the existing two-process Planner+Shopping proof workflow.
    menu = []
    for day in range(2, 9):
        for pos, role in enumerate(("BREAKFAST", "LUNCH", "DINNER"), 1):
            menu.append(
                {
                    "date": f"2026-11-{day:02d}",
                    "position": pos,
                    "role": role,
                    "title_ru": "Проверочное блюдо",
                    "recipe_code": "TEST_ONLY",
                    "recipe_version": 1,
                    "servings": [
                        {"member_ordinal": number, "portion_servings": "1.250000"}
                        for number in (
                            (1, 2) if pos == 1 else ((1,) if pos == 2 else (1, 2, 3))
                        )
                    ],
                    "nutrition_status": "INCOMPLETE",
                }
            )
    return {
        "schema": "PR10_FF_PRODUCT_READ_ONLY_PREVIEW_V1",
        "status": "SYNTHETIC_TECHNICAL_ENERGY_ONLY_NOT_FOR_FAMILY_USE",
        "week_start": "2026-11-02",
        "timezone": "Europe/Moscow",
        "days": 7,
        "meal_events": 21,
        "individual_servings": 42,  # renderer input consistency checked by caller
        "serving_basis": "DECIMAL_RECIPE_SERVINGS_NOT_COOKED_MASS",
        "menu": menu,
        "shopping": [
            {
                "food_code": "TEST_ONLY",
                "title_ru": "Тестовый продукт",
                "unit": "g",
                "required": "3.125",
                "at_home": "0.000",
                "to_buy": "3.125",
                "origins": [
                    {
                        "date": "2026-11-02",
                        "position": 1,
                        "role": "BREAKFAST",
                        "recipe_code": "TEST_ONLY",
                        "recipe_title_ru": "Проверочное блюдо",
                        "source_demand_up_001": "3.125",
                        "unit": "g",
                    }
                ],
            }
        ],
        "shopping_status": "COMPLETE",
        "price_status": "UNKNOWN",
        "pantry_state": "EXPLICIT_EMPTY_TEST_PANTRY",
        "prep_state": "UNREVIEWED_NO_EXECUTABLE_INSTRUCTIONS",
        "batch_storage_safety": "UNKNOWN",
        "gate2_pass": False,
    }


def test_renderer_is_readable_and_does_not_promote_unknowns():
    report = preview.render_markdown(_example())
    assert report.count("### 2026-11-") == 7
    assert "Проверочное блюдо" in report
    assert "Тестовый продукт" in report
    assert "3.125 g" in report
    assert "№1: 1.250000" in report
    assert "цены отсутствуют" in report.lower()
    assert "заготовки" in report.lower()
    assert "Не готовый рацион" in report
    assert "сроки хранения неизвестны" in report
    assert "## Купить" in report


@pytest.mark.parametrize(
    "key,value",
    [
        ("status", "READY_FOR_FAMILY"),
        ("shopping_status", "INCOMPLETE"),
        ("pantry_state", "UNKNOWN"),
        ("serving_basis", "COOKED_MASS_G"),
        ("batch_storage_safety", "VERIFIED"),
        ("price_status", "COMPLETE"),
        ("prep_state", "APPROVED_IMMEDIATE"),
        ("gate2_pass", True),
        ("individual_servings", 41),
        ("meal_events", 20),
    ],
)
def test_renderer_rejects_false_product_claims(key, value):
    payload = deepcopy(_example())
    payload[key] = value
    with pytest.raises(preview.WeekPreviewBlocked):
        preview.render_markdown(payload)


@pytest.mark.parametrize(
    "key",
    [
        "shopping_status",
        "pantry_state",
        "serving_basis",
        "batch_storage_safety",
    ],
)
def test_renderer_rejects_missing_source_claims(key):
    payload = deepcopy(_example())
    del payload[key]
    with pytest.raises(preview.WeekPreviewBlocked):
        preview.render_markdown(payload)


def test_renderer_rejects_fake_complete_nutrition():
    payload = _example()
    payload["menu"][0]["nutrition_status"] = "COMPLETE"
    with pytest.raises(preview.WeekPreviewBlocked):
        preview.render_markdown(payload)
