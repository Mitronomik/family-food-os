"""Offline mobile preview: readable quantities, honest unknowns, safe markup."""

from copy import deepcopy

import pytest
from app.tests.test_pr10_ff_week_preview import _example

from scripts import pr10_ff_mobile_preview as mobile
from scripts.pr10_ff_week_preview import WeekPreviewBlocked


def test_mobile_preview_shows_real_source_structure_and_ephemeral_checklist():
    page = mobile.render_html(_example())
    assert '<html lang="ru">' in page
    assert "Демонстрационная неделя" in page
    assert page.count('class="day"') == 7
    assert page.count('class="meal"') == 21
    assert 'type="checkbox"' in page
    assert "не сохраняются" in page
    assert "Купить" in page
    assert "№1: ×1.250000" in page
    assert "масса готовых порций не подтверждены" in page
    assert "Цены неизвестны" in page
    assert "Заготовки" in page
    assert "не Gate2" in page
    assert "3,125" not in page  # raw 3.125 g is rendered as 4 g, not confused with kg
    assert "4 г" in page
    assert "3.125 g" in page  # raw exact values remain available
    assert "https://" not in page
    assert "http://" not in page


@pytest.mark.parametrize(
    "raw,unit,shown",
    [
        ("312.194", "g", "313 г"),
        ("1685.827", "g", "1,686 кг"),
        ("19925.989", "g", "19,926 кг"),
        ("999.999", "ml", "1000 мл"),
        ("1000.001", "ml", "1,001 л"),
        ("1.01", "pcs", "2 шт."),
        ("0.000", "g", "0 г"),
    ],
)
def test_purchase_display_always_rounds_up_without_mass_volume_guessing(
    raw, unit, shown
):
    assert mobile._quantity(raw, unit) == shown


@pytest.mark.parametrize(
    "raw,unit",
    [
        ("NaN", "g"),
        ("Infinity", "g"),
        ("-2.0", "g"),
        ("bad", "ml"),
        ("1.0", "l"),
        (12.5, "g"),
    ],
)
def test_unsupported_or_invalid_quantity_fails_closed(raw, unit):
    with pytest.raises(WeekPreviewBlocked):
        mobile._quantity(raw, unit)


@pytest.mark.parametrize(
    "field,new_value",
    [
        ("at_home", "1.000"),
        ("to_buy", "2.125"),
        ("required", "3.126"),
        ("to_buy", "NaN"),
        ("required", "-1"),
    ],
)
def test_mobile_preview_rejects_stock_and_quantity_contradictions(field, new_value):
    payload = _example()
    payload["shopping"][0][field] = new_value
    with pytest.raises(WeekPreviewBlocked):
        mobile.render_html(payload)


def test_mobile_preview_blocks_duplicate_food_code():
    payload = _example()
    payload["shopping"].append(deepcopy(payload["shopping"][0]))
    with pytest.raises(WeekPreviewBlocked):
        mobile.render_html(payload)


def test_source_display_text_is_html_escaped_in_attribute_and_body():
    payload = _example()
    injection = '<script>alert("owned")</script>'
    payload["menu"][0]["title_ru"] = injection
    payload["shopping"][0]["title_ru"] = injection
    payload["shopping"][0]["origins"][0]["recipe_title_ru"] = injection
    page = mobile.render_html(payload)
    assert injection not in page
    assert "&lt;script&gt;" in page
    assert "alert(&quot;owned&quot;)" in page


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "READY_FOR_REAL_USE"),
        ("price_status", "COMPLETE"),
        ("prep_state", "APPROVED_IMMEDIATE"),
        ("batch_storage_safety", "APPROVED"),
        ("pantry_state", "USER_PANTRY"),
        ("serving_basis", "READY_MASS"),
        ("gate2_pass", True),
    ],
)
def test_html_reuses_nonrelease_gate_validation(field, value):
    payload = _example()
    payload[field] = value
    with pytest.raises(WeekPreviewBlocked):
        mobile.render_html(payload)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "empty",
        "wrong_recipe",
        "wrong_role",
        "wrong_unit",
        "negative",
        "infinite",
        "overstated",
        "understated",
        "duplicate",
    ],
)
def test_mobile_preview_rejects_unverifiable_purchase_origins(mutation):
    payload = _example()
    row = payload["shopping"][0]
    source = row["origins"][0]
    if mutation == "missing":
        del row["origins"]
    elif mutation == "empty":
        row["origins"] = []
    elif mutation == "wrong_recipe":
        source["recipe_code"] = "UNKNOWN_RECIPE"
    elif mutation == "wrong_role":
        source["role"] = "DINNER"
    elif mutation == "wrong_unit":
        source["unit"] = "ml"
    elif mutation == "negative":
        source["source_demand_up_001"] = "-3.125"
    elif mutation == "infinite":
        source["source_demand_up_001"] = "Infinity"
    elif mutation == "overstated":
        source["source_demand_up_001"] = "3.127"
    elif mutation == "understated":
        source["source_demand_up_001"] = "3.124"
    elif mutation == "duplicate":
        row["origins"].append(deepcopy(source))
    with pytest.raises(WeekPreviewBlocked):
        mobile.render_html(payload)


def test_water_source_is_explained_without_assuming_bottled_water_purchase():
    payload = _example()
    payload["shopping"][0]["food_code"] = "WATER"
    payload["shopping"][0]["title_ru"] = "Вода питьевая"
    page = mobile.render_html(payload)
    assert "Из каких блюд: 1" in page
    assert "не подтверждает необходимость покупать бутилированную воду" in page
    assert "3.125 g" in page
