"""One real-home-LUNCH, three independent courses: developer-only composition.

DOES NOT: create a new MealEvent, change Planner v0.5, reallocate missing
energy, prescribe physical portions, plan outside meals, or create Shopping.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, localcontext

from app.domain.meal_plans import MealSourceKind
from app.domain.units import UnitCode

SCHEMA = "PR10_FF_ONE_HOME_LUNCH_THREE_COURSES_V1"
DAY = date(2026, 11, 3)
COURSES = (
    ("FIRST", "MR2019_1_2A_VEGETARIAN_CABBAGE_SOUP", Decimal("1.000000")),
    ("SECOND", "SCHOOL2022_54_26M_POTATO_BEEF_CASSEROLE", Decimal("1.000000")),
    ("DESSERT_STUDY", "SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE", Decimal("0.500000")),
)
STEP = Decimal("0.000001")
KCAL_STEP = Decimal("0.000001")


class LunchBlocked(ValueError):
    """An untrusted fact would make the one-lunch preview misleading."""


def _decimal(value, label):
    try:
        number = Decimal(str(value))
    except (ValueError, TypeError, ArithmeticError) as exc:
        raise LunchBlocked(f"Invalid {label}") from exc
    if not number.is_finite() or number <= 0:
        raise LunchBlocked(f"Missing or invalid {label}")
    return number


def selected_home_lunch(members, weekday):
    """Only explicitly selected LUNCH; do not invent/record meals away from home."""
    if weekday not in range(1, 8) or not isinstance(members, list) or not members:
        raise LunchBlocked("Invalid accepted member schedule")
    result = {}
    for member in members:
        ordinal = member.get("ordinal")
        if type(ordinal) is not int or ordinal < 1 or ordinal in result:
            raise LunchBlocked("Invalid/duplicate semantic member")
        opportunities = member.get("opportunities")
        if not isinstance(opportunities, list):
            raise LunchBlocked("Untrusted accepted meal opportunities")
        daily = [row for row in opportunities if row.get("weekday") == weekday]
        if not daily or any(
            row.get("role")
            not in {
                "BREAKFAST",
                "LUNCH",
                "DINNER",
                "SNACK",
                "PRE_WORKOUT",
                "POST_WORKOUT",
                "OTHER",
            }
            for row in daily
        ):
            raise LunchBlocked("Incomplete/unsupported home schedule")
        if len({(row.get("position"), row.get("role")) for row in daily}) != len(daily):
            raise LunchBlocked("Duplicate home meal opportunity")
        shares = [_decimal(row.get("energy_share"), "accepted share") for row in daily]
        if sum(shares, Decimal(0)) > 1:
            raise LunchBlocked("Home meal shares exceed daily reference")
        lunch = [row for row in daily if row["role"] == "LUNCH"]
        if len(lunch) > 1:
            raise LunchBlocked("Ambiguous same-day lunch in bounded case")
        if lunch:
            result[ordinal] = (member, lunch[0], sum(shares, Decimal(0)))
    return result


def _verified_component(detail, pinned, food_by_id, label, factor):
    """Check independently persisted Recipe/Ingredients and accepted input pins."""
    version = detail.version
    if (
        detail.recipe.canonical_code != pinned.get("canonical_code")
        or str(version.id) != pinned.get("recipe_version_id")
        or version.version_number != pinned.get("version_number")
        or version.source_document_sha256 != pinned.get("source_document_sha256")
        or version.source_recipe_id != pinned.get("source_recipe_id")
        or version.source_name != pinned.get("source_name")
        or version.verification_status.value != "SOURCE_VERIFIED"
        or version.rights_review_status.value != "REVIEWED"
        or pinned.get("nutrition_status") != "INCOMPLETE"
        or pinned.get("exact_energy_ready") is not True
    ):
        raise LunchBlocked("Candidate/source version or energy authority mismatch")
    base = _decimal(version.base_servings, "recipe scaling base")
    kcal = _decimal(pinned.get("kcal_per_base_serving"), "pinned kcal per base serving")
    stored = detail.ingredients
    if not stored or len(stored) != len(pinned.get("ingredient_codes", [])):
        raise LunchBlocked("RecipeIngredient coverage differs from pinned source")
    codes = []
    for ingredient in stored:
        food = food_by_id.get(ingredient.food_ingredient_id)
        if (
            food is None
            or food.id != ingredient.food_ingredient_id
            or not food.is_active
            or ingredient.recipe_version_id != version.id
            or ingredient.optional is not False
            or ingredient.unit is not food.default_unit
            or ingredient.unit
            not in {UnitCode.GRAM, UnitCode.MILLILITER, UnitCode.PIECE}
            or not isinstance(ingredient.quantity, Decimal)
            or not ingredient.quantity.is_finite()
            or ingredient.quantity <= 0
        ):
            raise LunchBlocked("Untrusted persisted ingredient/food mapping")
        codes.append(food.canonical_code)
    if len(codes) != len(set(codes)) or sorted(codes) != sorted(
        pinned["ingredient_codes"]
    ):
        raise LunchBlocked("Canonical ingredient identity differs from candidate")
    if not detail.recipe.canonical_name.strip():
        raise LunchBlocked("Missing Russian source title")
    with localcontext() as ctx:
        ctx.prec = 50
        component_kcal = (factor * kcal).quantize(KCAL_STEP)
    return {
        "course": label,
        "recipe_code": detail.recipe.canonical_code,
        "recipe_title_ru": detail.recipe.canonical_name,
        "source_recipe_id": version.source_recipe_id,
        "factor": format(factor, ".6f"),
        "energy_only_kcal": format(component_kcal, ".6f"),
        "recipe_base_servings": format(base, "f"),
        "physical_portion_status": "NOT_PROVEN",
        "dessert_role_status": (
            "UNREVIEWED_BREAKFAST_RECIPE_REUSE"
            if label == "DESSERT_STUDY" and version.meal_type_code == "breakfast"
            else "NOT_APPLICABLE"
        ),
        "ingredient_codes": sorted(codes),
    }


def build_lunch(*, plan, member_ordinals, members, candidate_inputs, details, foods):
    """Read the real 2026-11-03 lunch, project separate TEST portions for 3 courses."""
    selected = selected_home_lunch(members, DAY.isoweekday())
    if set(selected) != {1}:
        raise LunchBlocked("Frozen lunch must be selected only by member 1")
    member, opportunity, daily_share = selected[1]
    if (
        opportunity.get("position") != 2
        or opportunity.get("energy_share") != "0.35"
        or member.get("excluded_food_codes") != []
    ):
        raise LunchBlocked("Lunch/member selection differs from accepted fixture")
    events = [
        event
        for event in plan.events
        if event.local_date == DAY and event.role.value == "LUNCH"
    ]
    if len(events) != 1:
        raise LunchBlocked("Missing one persisted lunch event")
    event = events[0]
    if event.source_kind is not MealSourceKind.COOK_RECIPE:
        raise LunchBlocked("Expected pinned recipe-backed lunch")
    current = [serving for serving in plan.servings if serving.event_id == event.id]
    if len(current) != 1 or member_ordinals.get(current[0].member_id) != 1:
        raise LunchBlocked("Other member was improperly assigned a home lunch")
    old_factor = _decimal(current[0].portion_servings, "persisted lunch Serving")

    candidate_codes = {row["canonical_code"]: row for row in candidate_inputs}
    if len(candidate_codes) != len(candidate_inputs):
        raise LunchBlocked("Duplicate source candidate identity")
    detail_codes = {detail.recipe.canonical_code: detail for detail in details.values()}
    if len(detail_codes) != len(details):
        raise LunchBlocked("Ambiguous persisted RecipeVersion")
    if detail_codes[COURSES[1][1]].version.id != event.recipe_version_id:
        raise LunchBlocked("Second course is not the actual persisted lunch recipe")

    components = [
        _verified_component(
            detail_codes[code], candidate_codes[code], foods, label, factor
        )
        for label, code, factor in COURSES
    ]
    if components[2]["dessert_role_status"] != "UNREVIEWED_BREAKFAST_RECIPE_REUSE":
        raise LunchBlocked("Dessert applicability cannot be silently promoted")

    combined = {code for item in components for code in item["ingredient_codes"]}
    if set(member["excluded_food_codes"]) & combined:
        raise LunchBlocked("Hard member exclusion would be violated")

    reference = _decimal(member["reference_energy_kcal"], "reference energy")
    share = _decimal(opportunity["energy_share"], "accepted lunch share")
    target = reference * share
    computed = sum(
        (Decimal(item["energy_only_kcal"]) for item in components), Decimal(0)
    )
    with localcontext() as ctx:
        ctx.prec = 50
        delta = (target - computed).quantize(KCAL_STEP)
        old_computed = (
            old_factor
            * _decimal(
                candidate_codes[COURSES[1][1]]["kcal_per_base_serving"], "old kcal"
            )
        ).quantize(KCAL_STEP)
    if abs(target - old_computed) > Decimal("0.001"):
        raise LunchBlocked("Original lunch energy does not reconcile")
    return {
        "schema": SCHEMA,
        "status": "STRUCTURALLY_COMPOSED_DIAGNOSTIC_ONLY",
        "date": DAY.isoformat(),
        "meal_role": "LUNCH",
        "home_participant_ordinals": [1],
        "non_lunch_member_ordinals": sorted(
            {m["ordinal"] for m in members} - set(selected)
        ),
        "out_of_home_food_tracking": "NOT_COLLECTED",
        "original_meal_event_recipe_code": COURSES[1][1],
        "original_lunch_factor": format(old_factor, ".6f"),
        "energy_reference_kcal": format(target, ".6f"),
        "reference_allocated_share": format(share, "f"),
        "planned_daily_share": format(daily_share, "f"),
        "courses": components,
        "hypothetical_energy_only_kcal": format(computed, ".6f"),
        "reference_alignment_delta_kcal": format(delta, ".6f"),
        "delta_is_not_deficit_or_reallocation": True,
        "course_factors_are_test_inputs": True,
        "physical_serving_approval": "NOT_PROVEN",
        "dessert_course_approval": "NOT_PROVEN",
        "authoritative_mealplan": False,
        "shopping_authority": "NONE",
        "prep_approval": False,
        "gate2_pass": False,
    }


def render_markdown(result):
    if (
        result.get("schema") != SCHEMA
        or result.get("status") != "STRUCTURALLY_COMPOSED_DIAGNOSTIC_ONLY"
        or result.get("physical_serving_approval") != "NOT_PROVEN"
        or result.get("dessert_course_approval") != "NOT_PROVEN"
        or result.get("authoritative_mealplan") is not False
        or result.get("shopping_authority") != "NONE"
        or result.get("gate2_pass") is not False
        or result.get("home_participant_ordinals") != [1]
        or len(result.get("courses", [])) != 3
        or [c.get("course") for c in result["courses"]]
        != ["FIRST", "SECOND", "DESSERT_STUDY"]
    ):
        raise LunchBlocked("Provisional lunch cannot claim production authority")
    rows = [
        "# Один домашний обед из трёх компонентов — технический прототип",
        "",
        "**Дата 3 ноября 2026. Дома обедает только участник №1.**",
        (
            "Для остальных участников домашний обед не создаётся; питание вне "
            "дома не учитывается и не предполагается отсутствующим."
        ),
        "",
        (
            "Все коэффициенты компонентов — **явно заданные тестовые значения**, "
            "а не индивидуально разрешённые порции."
        ),
        "",
        "| Часть обеда | Рецепт | Доля базового рецепта | Технические ккал |",
        "| --- | --- | ---: | ---: |",
    ]
    names = {
        "FIRST": "Первое",
        "SECOND": "Второе",
        "DESSERT_STUDY": "Десерт (проверка)",
    }
    for c in result["courses"]:
        rows.append(
            f"| {names[c['course']]} | {c['recipe_title_ru']} | "
            f"{c['factor']} | {c['energy_only_kcal']} |"
        )
    rows.extend(
        [
            "",
            (
                f"**Энергия тестового обеда: {result['hypothetical_energy_only_kcal']} ккал.** "
                f"Ориентир принятой доли обеда: {result['energy_reference_kcal']} ккал."
            ),
            (
                f"Разница: {result['reference_alignment_delta_kcal']} ккал — "
                "**не дефицит и не повод увеличивать порции или переносить энергию**."
            ),
            "",
            (
                "Десертная роль творожной запеканки **не опубликована/не проверена**: "
                "в каталоге она классифицирована как завтрак. Никаких норм десертной "
                "порции здесь не установлено."
            ),
            (
                "Состав каждого источника сохраняется, но готовая масса, размер "
                "порций и полное КБЖУ **не подтверждены**."
            ),
            "",
            (
                "**Не изменены** Planner, MealPlan, Serving, Shopping и Pantry; "
                "данный обед не создаёт покупок или Prep-действий. "
                "Переход в производство требует отдельно согласованной модели "
                "компонентов приёма пищи."
            ),
            "",
        ]
    )
    return "\n".join(rows)
