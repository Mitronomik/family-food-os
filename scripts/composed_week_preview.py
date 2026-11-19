"""Internal mobile week + groceries view of an immutable composed MealPlan.

This is an explicit developer-only, read-only preview, not a consumer API,
nutrition/physical-portion approval, executable Prep instruction, or price quote.
All grocery math is delegated to the already accepted Shopping v1b engine.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from html import escape
from pathlib import Path
from uuid import UUID

from app.db.config import DatabaseConfig
from app.domain.meal_plans import MealSourceKind
from app.domain.shopping_composition_calculation import (
    calculate_shopping_composition,
    meal_plan_source_projection,
    validate_v2_provenance,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.shopping_uow import SqlAlchemyShoppingReadScope

SCHEMA = "COMPOSED_WEEK_INTERNAL_PREVIEW_V1"
_ROLES = {
    "BREAKFAST": "Завтрак",
    "LUNCH": "Обед",
    "DINNER": "Ужин",
    "SNACK": "Перекус",
}
_COURSES = {
    "FIRST": "Первое",
    "SECOND": "Второе",
    "DESSERT": "Десерт",
    "MAIN": "Основное",
    "SIDE": "Гарнир",
    "SNACK": "Перекус",
    "DRINK": "Напиток",
}
_NO_RECIPE = {
    MealSourceKind.ASSEMBLY: "Сборное блюдо (пока не рассчитано)",
    MealSourceKind.LEFTOVER: "Остатки (наличие не подтверждено)",
    MealSourceKind.PREPARED: "Заготовка (наличие не подтверждено)",
    MealSourceKind.READY_MEAL: "Готовая еда (данные не подтверждены)",
    MealSourceKind.ORDER_OUT: "Доставка или заказ вне дома",
    MealSourceKind.EAT_OUT: "Еда вне дома",
}


class ComposedWeekPreviewBlocked(ValueError):
    """Cannot render an independently source-consistent internal week."""


def _block(message: str) -> None:
    raise ComposedWeekPreviewBlocked(message)


def _recipe(recipes, version_id):
    result = recipes.get(version_id)
    if result is None or result.version.id != version_id:
        _block("Нет закреплённой версии рецепта.")
    if not result.recipe.canonical_name.strip():
        _block("У рецепта отсутствует русское отображаемое имя.")
    return result


def build_preview(
    *, plan, recipes, foods, pantry_items, household_timezone, captured_at
):
    """Produce complete seven-day cards and exact canonical grocery quantities.

    This function does not read persistence: the caller supplies one consistent
    immutable source snapshot. No serving mass or energy is inferred from
    ingredient inputs or a recipe's unreviewed source_output_g.
    """
    if not plan.compositions or len(plan.horizon_dates) != 7:
        _block("Требуется полный семидневный диагностический составной план.")
    calculation, provenance = calculate_shopping_composition(
        plan=plan,
        recipes=recipes,
        foods=foods,
        pantry_items=tuple(pantry_items),
        household_timezone=household_timezone,
        captured_at=captured_at,
    )
    validate_v2_provenance(provenance, calculation)
    expected = meal_plan_source_projection(plan)
    if any(provenance.get(k) != v for k, v in expected.items()):
        _block("Составной Shopping не совпадает с исходным MealPlan.")
    composition_by_event = {c.event_id: c for c in plan.compositions}
    if len(composition_by_event) != len(plan.compositions):
        _block("Повторяется составной MealEvent.")
    servings_by_event = {}
    for serving in plan.servings:
        servings_by_event.setdefault(serving.event_id, []).append(serving)
    cards_by_date = {day.isoformat(): [] for day in plan.horizon_dates}
    for event in sorted(
        plan.events, key=lambda x: (x.local_date, x.position, str(x.id))
    ):
        role = _ROLES.get(str(event.role), "Приём пищи")
        card = {
            "role_ru": role,
            "position": event.position,
            "source_kind": str(event.source_kind),
            "courses": [],
        }
        if event.source_kind is MealSourceKind.COOK_COMPOSITION:
            comp = composition_by_event.get(event.id)
            if comp is None:
                _block("Для составного MealEvent нет закреплённых компонентов.")
            for part in sorted(comp.components, key=lambda x: x.position):
                detail = _recipe(recipes, part.recipe_version_id)
                members = sorted(
                    (s for s in comp.servings if s.component_id == part.id),
                    key=lambda x: x.member_id.hex,
                )
                if not members:
                    _block("У компонента нет индивидуальных порций.")
                card["courses"].append(
                    {
                        "course_ru": _COURSES.get(str(part.course), "Блюдо"),
                        "recipe_ru": detail.recipe.canonical_name,
                        "version": detail.version.version_number,
                        "servings": [
                            {
                                "member_id": str(s.member_id),
                                "factor": format(s.portion_servings, ".6f"),
                            }
                            for s in members
                        ],
                    }
                )
        elif event.source_kind is MealSourceKind.COOK_RECIPE:
            detail = _recipe(recipes, event.recipe_version_id)
            servings = sorted(
                servings_by_event.get(event.id, ()),
                key=lambda x: x.member_id.hex,
            )
            if not servings:
                _block("Отсутствуют порции обычного рецепта.")
            card["courses"].append(
                {
                    "course_ru": "Блюдо",
                    "recipe_ru": detail.recipe.canonical_name,
                    "version": detail.version.version_number,
                    "servings": [
                        {
                            "member_id": str(s.member_id),
                            "factor": format(s.portion_servings, ".6f"),
                        }
                        for s in servings
                    ],
                }
            )
        else:
            label = _NO_RECIPE.get(event.source_kind)
            if label is None:
                _block("Неизвестный источник приёма пищи.")
            card["source_ru"] = label
        cards_by_date[event.local_date.isoformat()].append(card)

    grocery = []
    for item in calculation.items:
        food = foods.get(item.food_ingredient_id)
        if food is None or not food.canonical_name.strip():
            _block("У Shopping позиции отсутствует канонический продукт.")
        grocery.append(
            {
                "food_ru": food.canonical_name,
                "unit": str(item.unit),
                "required": format(item.required_quantity, "f"),
                "at_home": format(item.pantry_available_quantity, "f"),
                "to_buy": format(item.purchase_quantity, "f"),
            }
        )
    grocery.sort(key=lambda x: (x["food_ru"], x["unit"]))
    return {
        "schema": SCHEMA,
        "status": "DIAGNOSTIC_ONLY",
        "week_start": plan.plan.week_start.isoformat(),
        "revision": plan.plan.revision_number,
        "source_fingerprint": calculation.source_fingerprint,
        "content_fingerprint": calculation.content_fingerprint,
        "shopping_status": str(calculation.status),
        "price_status": str(calculation.price_status),
        "days": [
            {"date": date, "events": events}
            for date, events in sorted(cards_by_date.items())
        ],
        "grocery": grocery,
        "unresolved": [
            {"source_kind": str(x.source_kind), "reason": str(x.reason)}
            for x in calculation.unresolved
        ],
        "physical_portions": "NOT_PROVEN",
        "nutrition": "NOT_ASSESSED",
        "prep_safety": "NOT_PROVEN",
    }


def render_html(preview: dict) -> str:
    """Self-contained Russian mobile-first HTML; all source text is escaped."""
    if (
        preview.get("schema") != SCHEMA
        or preview.get("status") != "DIAGNOSTIC_ONLY"
        or preview.get("physical_portions") != "NOT_PROVEN"
        or preview.get("nutrition") != "NOT_ASSESSED"
        or preview.get("prep_safety") != "NOT_PROVEN"
    ):
        _block("Недопустимый статус демонстрационного плана.")

    def e(value):
        return escape(str(value), quote=True)

    days_html = []
    for day in preview["days"]:
        meals = []
        for event in day["events"]:
            courses = []
            for course in event["courses"]:
                members = ", ".join(
                    f"участник …{e(s['member_id'][-8:])}: ×{e(s['factor'])}"
                    for s in course["servings"]
                )
                courses.append(
                    "<li><strong>"
                    + e(course["course_ru"])
                    + ": "
                    + e(course["recipe_ru"])
                    + "</strong><small>Версия "
                    + e(course["version"])
                    + " · "
                    + members
                    + "</small></li>"
                )
            source = (
                "<p class='muted'>" + e(event["source_ru"]) + "</p>"
                if "source_ru" in event
                else "<ul>" + "".join(courses) + "</ul>"
            )
            meals.append(
                "<article><h3>" + e(event["role_ru"]) + "</h3>" + source + "</article>"
            )
        days_html.append(
            "<section class='day'><h2>"
            + e(day["date"])
            + "</h2>"
            + "".join(meals)
            + "</section>"
        )
    shopping = "".join(
        "<li><span>"
        + e(row["food_ru"])
        + "</span><strong>"
        + e(row["to_buy"])
        + " "
        + e(row["unit"])
        + "</strong><small>Нужно "
        + e(row["required"])
        + ", дома учтено "
        + e(row["at_home"])
        + "</small></li>"
        for row in preview["grocery"]
    )
    unresolved = (
        "<p class='warning'>Некоторые источники питания не обеспечены "
        "подтверждёнными продуктами. Список покупок неполный.</p>"
        if preview["unresolved"]
        else ""
    )
    return (
        "<!doctype html><html lang='ru'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Составная неделя — внутренний просмотр</title>"
        "<style>"
        ":root{font:16px/1.5 system-ui,sans-serif;color:#1e2924;"
        "background:#f7f9f5}*{box-sizing:border-box}body{margin:0}"
        "main{max-width:900px;margin:auto;padding:22px 16px}"
        "h1{font-size:clamp(24px,5vw,36px);line-height:1.15}"
        "h2{font-size:19px;margin:0 0 10px}h3{font-size:15px;margin:0;color:#26644e}"
        ".warning{padding:14px;border-radius:12px;background:#fff2d5;"
        "border:1px solid #d5b768}.muted,small{color:#53685b}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px}"
        ".day{background:white;border:1px solid #dde5dc;border-radius:16px;padding:16px}"
        "article{border-top:1px solid #e6ece5;padding-top:10px;margin-top:10px}"
        "ul{padding-left:20px;margin:6px 0}li{margin:7px 0}"
        "small{display:block;font-size:12px;font-weight:400}"
        ".buy{background:white;border:1px solid #dde5dc;border-radius:16px;padding:14px}"
        ".buy li{display:flex;flex-wrap:wrap;justify-content:space-between;gap:4px}"
        ".buy small{flex-basis:100%}.buy strong{white-space:nowrap}"
        "section{margin:16px 0}footer{margin-top:30px;color:#53685b;font-size:13px}"
        "</style></head><body><main>"
        "<h1>Неделя питания — составные блюда</h1>"
        "<p class='warning'><strong>Только внутренняя демонстрация.</strong> "
        "Реалистичность готовых порций, полноценность питания, безопасность "
        "заготовок и пригодность блюд для ролей ещё не подтверждены. "
        "Коэффициенты × — доли базового рецепта, не масса готового блюда. "
        "Стоимость и цены неизвестны.</p>"
        "<h2>Меню по дням</h2><div class='grid'>"
        + "".join(days_html)
        + "</div><h2>Купить — расчётные количества</h2>"
        + unresolved
        + "<ul class='buy'>"
        + shopping
        + "</ul><footer>Диагностический Shopping V2 · "
        + e(preview["shopping_status"])
        + " · ревизия "
        + e(preview["revision"])
        + ". Покупка, наличие и выполнение готовки не подтверждены.</footer>"
        "</main></body></html>"
    )


def preview_from_database(*, database_path, household_id, plan_id, captured_at):
    """Read-only single-scope source acquisition, with Household access filtering."""
    engine = create_sqlite_engine(DatabaseConfig(path=Path(database_path)))
    try:
        with SqlAlchemyShoppingReadScope(engine) as scope:
            household = scope.households.get_household(household_id)
            plan = scope.plans.get_detail(household_id, plan_id)
            if household is None or plan is None or not plan.compositions:
                _block("Диагностическая составная неделя не найдена.")
            version_ids = {
                event.recipe_version_id
                for event in plan.events
                if event.source_kind is MealSourceKind.COOK_RECIPE
            } | {
                part.recipe_version_id
                for comp in plan.compositions
                for part in comp.components
            }
            recipes = {
                version_id: scope.recipes.get_detail(version_id)
                for version_id in version_ids
            }
            if any(v is None for v in recipes.values()):
                _block("Недоступна закреплённая версия рецепта.")
            food_ids = {
                ingredient.food_ingredient_id
                for detail in recipes.values()
                for ingredient in detail.ingredients
            }
            foods = {food_id: scope.foods.get(food_id) for food_id in food_ids}
            if any(v is None for v in foods.values()):
                _block("Недоступен канонический ингредиент.")
            return build_preview(
                plan=plan,
                recipes=recipes,
                foods=foods,
                pantry_items=tuple(
                    scope.pantry.list_items(household_id, include_empty=True)
                ),
                household_timezone=household.timezone,
                captured_at=captured_at,
            )
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Internal composed-week HTML preview")
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--household", type=UUID, required=True)
    parser.add_argument("--plan", type=UUID, required=True)
    parser.add_argument("--captured-at", required=True, help="ISO aware datetime")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    captured = datetime.fromisoformat(args.captured_at)
    if captured.tzinfo is None or captured.utcoffset() is None:
        parser.error("--captured-at requires an explicit timezone")
    preview = preview_from_database(
        database_path=args.sqlite,
        household_id=args.household,
        plan_id=args.plan,
        captured_at=captured,
    )
    args.out.write_text(render_html(preview), encoding="utf-8")
    print(f"Saved internal diagnostic preview: {args.out}")


if __name__ == "__main__":
    main()
