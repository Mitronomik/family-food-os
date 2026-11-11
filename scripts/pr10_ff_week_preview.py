"""Developer-only, truthful product preview from the accepted technical week.

Reads the same persisted synthetic MealPlan/Recipe/Food/Pantry snapshots used
by the PR10-FF proof. Does not publish a ShoppingList, PrepPlan or consumer API.
Never treats an energy-only fixture as a nutritionally validated family menu.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.shopping_calculation import (
    ShoppingPriceStatus,
    ShoppingStatus,
    calculate_shopping,
)
from app.persistence.sqlalchemy_core.shopping_uow import SqlAlchemyShoppingReadScope
from scripts.pr10_ff_shopping_origins import ShoppingOriginBlocked, shopping_origins


class WeekPreviewBlocked(ValueError):
    """Source/readback inconsistency: do not emit a misleading preview."""


_ROLES_RU = {"BREAKFAST": "Завтрак", "LUNCH": "Обед", "DINNER": "Ужин"}


def project_week(*, engine, plan, semantic_events, candidate_inputs, timezone):
    """Render verified readback into a *non-authoritative* synthetic product view.

    All quantities come from the actual deterministic Shopping calculator. IDs
    remain run-local and are deliberately absent from cross-process UI output.
    """
    if len(semantic_events) != 21 or len(candidate_inputs) != 51:
        raise WeekPreviewBlocked("Unexpected frozen week or candidate coverage")
    candidates = {r["canonical_code"]: r for r in candidate_inputs}
    if len(candidates) != len(candidate_inputs):
        raise WeekPreviewBlocked("Ambiguous canonical recipe code")
    if any(r["nutrition_status"] != "INCOMPLETE" for r in candidates.values()):
        raise WeekPreviewBlocked("The energy-only fixture changed without review")

    with SqlAlchemyShoppingReadScope(engine) as scope:
        versions = {}
        foods = {}
        for event in plan.events:
            detail = scope.recipes.get_detail(event.recipe_version_id)
            if detail is None or detail.version.id != event.recipe_version_id:
                raise WeekPreviewBlocked("Missing persisted RecipeVersion readback")
            versions[event.recipe_version_id] = detail
            for ingredient in detail.ingredients:
                fid = ingredient.food_ingredient_id
                if fid not in foods:
                    food = scope.foods.get(fid)
                    if food is None or not food.is_active:
                        raise WeekPreviewBlocked("Missing or inactive canonical food")
                    foods[fid] = food
        pantry_items = tuple(
            scope.pantry.list_items(plan.plan.household_id, include_empty=True)
        )
        # The accepted frozen fixture explicitly has no home stock. A later
        # stocked fixture must be separately scoped, not silently substituted.
        if pantry_items:
            raise WeekPreviewBlocked("Frozen week unexpectedly has Pantry stock")
        shopping = calculate_shopping(
            plan=plan,
            recipes=versions,
            foods=foods,
            pantry_items=pantry_items,
            household_timezone=timezone,
            captured_at=datetime(2026, 11, 2, 9, tzinfo=UTC),
        )
    if (
        shopping.status is not ShoppingStatus.COMPLETE
        or shopping.price_status is not ShoppingPriceStatus.UNKNOWN
        or shopping.unresolved
    ):
        raise WeekPreviewBlocked("Unexpected incomplete Shopping calculation")

    by_slot = {
        (event.local_date.isoformat(), event.position): event for event in plan.events
    }
    if len(by_slot) != 21:
        raise WeekPreviewBlocked("Duplicate persisted day/meal positions")
    menu = []
    for source in semantic_events:
        date = source["date"]
        pos = source["position"]
        event = by_slot.get((date, pos))
        if event is None or event.recipe_version_id not in versions:
            raise WeekPreviewBlocked("Preview event has no persisted source")
        detail = versions[event.recipe_version_id]
        recipe_code = detail.recipe.canonical_code
        if (
            recipe_code != source["recipe"]["code"]
            or detail.version.version_number != source["recipe"]["version"]
            or recipe_code not in candidates
            or event.role.value != source["role"]
            or source["role"] not in _ROLES_RU
        ):
            raise WeekPreviewBlocked("Preview recipe/role differs from accepted week")
        name = detail.recipe.canonical_name
        if not name:
            raise WeekPreviewBlocked("Recipe has no Russian display name")
        menu.append(
            {
                "date": date,
                "position": pos,
                "role": source["role"],
                "title_ru": name,
                "recipe_code": recipe_code,
                "recipe_version": detail.version.version_number,
                "servings": source["servings"],  # exact recipe portions, never grams
                "nutrition_status": candidates[recipe_code]["nutrition_status"],
            }
        )
    if (
        len({r["date"] for r in menu}) != 7
        or sum(len(r["servings"]) for r in menu) != 42
    ):
        raise WeekPreviewBlocked("Preview lost days or individual servings")

    # Explain each canonical item through actual MealEvents and RecipeIngredients.
    # Compare exact unrounded event totals to the *existing* Shopping engine;
    # a mismatch is BLOCKED, never a correction of published quantities.
    try:
        origin_map = shopping_origins(
            plan=plan, recipes=versions, shopping=shopping
        )
    except ShoppingOriginBlocked as exc:
        raise WeekPreviewBlocked("Unverifiable Shopping ingredient origins") from exc

    shopping_rows = []
    for item in shopping.items:
        food = foods[item.food_ingredient_id]
        shopping_rows.append(
            {
                "food_code": food.canonical_code,
                "title_ru": food.canonical_name,
                "unit": item.unit.value,
                "required": format(item.required_quantity, "f"),
                "at_home": format(item.pantry_available_quantity, "f"),
                "to_buy": format(item.purchase_quantity, "f"),
                "origins": origin_map[(item.food_ingredient_id, item.unit)],
            }
        )
    shopping_rows.sort(key=lambda r: (r["title_ru"], r["food_code"]))
    if not shopping_rows:
        raise WeekPreviewBlocked("Expected source-backed grocery demand")
    return {
        "schema": "PR10_FF_PRODUCT_READ_ONLY_PREVIEW_V1",
        "status": "SYNTHETIC_TECHNICAL_ENERGY_ONLY_NOT_FOR_FAMILY_USE",
        "week_start": plan.plan.week_start.isoformat(),
        "timezone": timezone,
        "days": 7,
        "meal_events": 21,
        "individual_servings": 42,
        "serving_basis": "DECIMAL_RECIPE_SERVINGS_NOT_COOKED_MASS",
        "menu": menu,
        "shopping": shopping_rows,
        "shopping_status": shopping.status.value,
        "price_status": shopping.price_status.value,
        "pantry_state": "EXPLICIT_EMPTY_TEST_PANTRY",
        "prep_state": "UNREVIEWED_NO_EXECUTABLE_INSTRUCTIONS",
        "batch_storage_safety": "UNKNOWN",
        "gate2_pass": False,
    }


def _cell(text):
    return str(text).replace("|", r"\|").replace("\n", " ").strip()


def render_markdown(preview):
    """A readable internal week, never executable preparation instructions."""
    if (
        preview.get("schema") != "PR10_FF_PRODUCT_READ_ONLY_PREVIEW_V1"
        or preview.get("status") != "SYNTHETIC_TECHNICAL_ENERGY_ONLY_NOT_FOR_FAMILY_USE"
        or (
            preview.get("days"),
            preview.get("meal_events"),
            preview.get("individual_servings"),
        )
        != (7, 21, 42)
        or preview.get("shopping_status") != "COMPLETE"
        or preview.get("pantry_state") != "EXPLICIT_EMPTY_TEST_PANTRY"
        or preview.get("serving_basis") != "DECIMAL_RECIPE_SERVINGS_NOT_COOKED_MASS"
        or preview.get("batch_storage_safety") != "UNKNOWN"
        or preview.get("price_status") != "UNKNOWN"
        or preview.get("prep_state") != "UNREVIEWED_NO_EXECUTABLE_INSTRUCTIONS"
        or preview.get("gate2_pass") is not False
        or len(preview.get("menu", [])) != 21
        or not preview.get("shopping")
    ):
        raise WeekPreviewBlocked("Malformed or overclaimed product preview")
    if (
        len({(row["date"], row["role"]) for row in preview["menu"]}) != 21
        or len({row["date"] for row in preview["menu"]}) != 7
        or sum(len(row["servings"]) for row in preview["menu"]) != 42
    ):
        raise WeekPreviewBlocked("Missing, duplicate or inconsistent meal servings")
    lines = [
        "# FamilyFoodOS — демонстрационная неделя",
        "",
        "**Только внутренний синтетический пример. Не готовый рацион и не инструкция к приготовлению.**",
        "",
        "Источник: настоящая генерация Planner → сохранённый MealPlan/Serving →",
        "проверенный RecipeVersion → детерминированный Shopping Engine.",
        "",
        "- 7 дней, 21 приём пищи, 42 индивидуальные доли рецептов.",
        "- Пищевая ценность неполная: подтверждена лишь техническая основа по энергии.",
        "- Доли рецепта — не граммы готовой порции. Массу не предполагаем.",
        "- Цены отсутствуют: бюджет и стоимость корзины неизвестны.",
        "- Pantry в этой тестовой неделе пуст по заданным входным данным.",
        "- Заготовки и инструкции не допущены к исполнению; безопасные сроки хранения неизвестны.",
        "",
        "## Неделя",
    ]
    for date in sorted({row["date"] for row in preview["menu"]}):
        lines.extend(
            [
                "",
                "### " + _cell(date),
                "",
                "| Приём | Блюдо | Доли рецепта по участникам |",
                "| --- | --- | --- |",
            ]
        )
        for row in (r for r in preview["menu"] if r["date"] == date):
            if row["role"] not in _ROLES_RU or row["nutrition_status"] != "INCOMPLETE":
                raise WeekPreviewBlocked("Unreviewed display or nutrition promotion")
            serving = "; ".join(
                "№" + str(s["member_ordinal"]) + ": " + _cell(s["portion_servings"])
                for s in row["servings"]
            )
            lines.append(
                f"| {_ROLES_RU[row['role']]} | {_cell(row['title_ru'])} | {serving} |"
            )
    lines.extend(
        [
            "",
            "## Купить — расчёт по исходным ингредиентам",
            "",
            "Количество в исходных единицах. Округление до 0,001 — правило Shopping Engine.",
            "",
            "| Продукт | Нужно | Дома | Купить |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in preview["shopping"]:
        name = _cell(item["title_ru"])
        unit = _cell(item["unit"])
        lines.append(
            f"| {name} | {_cell(item['required'])} {unit} | "
            f"{_cell(item['at_home'])} {unit} | {_cell(item['to_buy'])} {unit} |"
        )
    lines.extend(
        [
            "",
            "## Заготовки",
            "",
            "**Пока недоступны.** Исходные шаги рецептов не имеют независимого допуска",
            "для исполнительного Prep. Нельзя выводить из этого примера время, заморозку,",
            "хранение, фактическую готовность блюда или экономию.",
            "",
            "Это исследовательский просмотр существующего backend, а не Gate2 и не",
            "разрешение на использование меню реальной семьёй.",
            "",
        ]
    )
    return "\n".join(lines)
