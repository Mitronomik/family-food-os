"""Read-only source audit for the actual synthetic Planner week.

RecipeVersion.source_output_g is a raw source field, never proof of physically
feasible individual mass. This file cannot approve portions, Prep or a release.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext


class PortionAuditBlocked(ValueError):
    """An individual Serving cannot be reconciled with its trusted sources."""


SCHEMA = "PR10_FF_PORTION_REALITY_AUDIT_V1"
STATUS = "PHYSICAL_FEASIBILITY_NOT_PROVEN"


def positive(value, label):
    if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
        raise PortionAuditBlocked(f"Invalid {label}")
    return value


def inspect(*, plan, semantic_events, details, candidate_inputs, member_ordinals):
    """Read only. Ordinals come from accepted generation witness, not sorted UUIDs."""
    by_slot = {(e.local_date.isoformat(), e.position): e for e in plan.events}
    if len(by_slot) != len(plan.events) or len(by_slot) != len(semantic_events):
        raise PortionAuditBlocked("Missing or duplicate persisted meal slot")
    if not member_ordinals or len(set(member_ordinals.values())) != len(
        member_ordinals
    ):
        raise PortionAuditBlocked("Unbound member semantics")
    by_code = {c["canonical_code"]: c for c in candidate_inputs}
    if len(by_code) != len(candidate_inputs):
        raise PortionAuditBlocked("Ambiguous candidate identity")
    ids = {e.id for e in plan.events}
    actual = {}
    for s in plan.servings:
        ordinal = member_ordinals.get(s.member_id)
        key = (s.event_id, ordinal)
        if s.event_id not in ids or ordinal is None or key in actual:
            raise PortionAuditBlocked("Unknown, orphan or duplicate member Serving")
        actual[key] = positive(s.portion_servings, "persisted Serving")

    rows = []
    seen_slots = set()
    output_present = 0
    for item in semantic_events:
        key = (item["date"], item["position"])
        if key in seen_slots:
            raise PortionAuditBlocked("Repeated semantic meal slot")
        seen_slots.add(key)
        event = by_slot.get(key)
        if event is None or event.role.value != item["role"]:
            raise PortionAuditBlocked("Semantic/persisted role mismatch")
        detail = details.get(event.recipe_version_id)
        if detail is None or detail.version.id != event.recipe_version_id:
            raise PortionAuditBlocked("Exact pinned RecipeVersion is missing")
        code = detail.recipe.canonical_code
        if (
            code != item["recipe"]["code"]
            or detail.version.version_number != item["recipe"]["version"]
        ):
            raise PortionAuditBlocked("Source recipe pin mismatch")
        candidate = by_code.get(code)
        if (
            candidate is None
            or candidate["nutrition_status"] != "INCOMPLETE"
            or candidate["exact_energy_ready"] is not True
            or candidate["recipe_version_id"] != str(detail.version.id)
        ):
            raise PortionAuditBlocked("Missing technical energy-only candidate pin")
        try:
            kcal = Decimal(candidate["kcal_per_base_serving"])
        except (InvalidOperation, TypeError) as exc:
            raise PortionAuditBlocked("Invalid technical kcal pin") from exc
        positive(kcal, "technical recipe kcal")
        base = positive(detail.version.base_servings, "recipe base servings")
        original_base = positive(
            detail.version.source_original_servings, "original source servings"
        )
        source_output = detail.version.source_output_g
        if source_output is not None:
            positive(source_output, "raw source output")
            output_present += 1
        output_status = (
            "MISSING_SOURCE_OUTPUT"
            if source_output is None
            else (
                "RAW_OUTPUT_DIFFERENT_BASE_UNREVIEWED"
                if base != original_base
                else "RAW_OUTPUT_APPLICABILITY_UNREVIEWED"
            )
        )
        expected = {v["member_ordinal"]: v for v in item["servings"]}
        if len(expected) != len(item["servings"]):
            raise PortionAuditBlocked("Duplicate semantic member")
        event_servings = {
            ordinal: factor
            for (event_id, ordinal), factor in actual.items()
            if event_id == event.id
        }
        if not event_servings or set(expected) != set(event_servings):
            raise PortionAuditBlocked("Incomplete individual member coverage")
        for ordinal, factor in sorted(event_servings.items()):
            try:
                stated = Decimal(expected[ordinal]["portion_servings"])
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise PortionAuditBlocked("Invalid frozen member factor") from exc
            if stated != factor:
                raise PortionAuditBlocked(
                    "Frozen factor differs from persisted Serving"
                )
            with localcontext() as ctx:
                ctx.prec = 50
                energy = (kcal * factor).quantize(
                    Decimal("0.001"), rounding=ROUND_HALF_EVEN
                )
            rows.append(
                {
                    "date": item["date"],
                    "position": item["position"],
                    "role": item["role"],
                    "recipe_code": code,
                    "recipe_title_ru": detail.recipe.canonical_name,
                    "member_ordinal": ordinal,
                    "portion_factor": format(factor, ".6f"),
                    "technical_energy_kcal": format(energy, "f"),
                    "source_output_g_raw": (
                        format(source_output, "f")
                        if source_output is not None
                        else None
                    ),
                    "source_output_status": output_status,
                    "physical_feasibility": "NOT_PROVEN",
                }
            )

    if len(rows) != len(plan.servings):
        raise PortionAuditBlocked("Unattributed persisted Serving")
    factors = [Decimal(row["portion_factor"]) for row in rows]
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "meal_events": len(semantic_events),
        "individual_servings": len(rows),
        "source_output_present_events": output_present,
        "source_output_missing_events": len(semantic_events) - output_present,
        "physically_reviewed_servings": 0,
        "factor_min": format(min(factors), ".6f"),
        "factor_max": format(max(factors), ".6f"),
        "rows": rows,
    }


def render_markdown(audit):
    """A diagnostic worklist, not a physical serving-quality verdict."""
    if (
        audit.get("schema") != SCHEMA
        or audit.get("status") != STATUS
        or audit.get("physically_reviewed_servings") != 0
        or not audit.get("rows")
        or len(audit["rows"]) != audit.get("individual_servings")
    ):
        raise PortionAuditBlocked("Physical readiness is not established")
    rows = audit["rows"]
    factors = [Decimal(row["portion_factor"]) for row in rows]
    if (
        format(min(factors), ".6f") != audit["factor_min"]
        or format(max(factors), ".6f") != audit["factor_max"]
        or any(row["physical_feasibility"] != "NOT_PROVEN" for row in rows)
    ):
        raise PortionAuditBlocked("Portion audit contradicts its evidence")
    lines = [
        "# FamilyFoodOS — проверка реальности порций",
        "",
        "**Внутренний синтетический аудит, не готовый рацион.**",
        "",
        (
            "Доля рецепта — не граммы блюда и не физиологическая норма. "
            "Техническая энергия рассчитана по утверждённому energy-only входу Planner; "
            "белки/жиры/углеводы неполны."
        ),
        (
            "Встречающееся поле source_output_g — исходные данные каталога, "
            "а не проверенная масса съедобной индивидуальной порции."
        ),
        "",
        f"- Приёмов пищи: {audit['meal_events']}; порций: {audit['individual_servings']}.",
        f"- Коэффициенты: ×{audit['factor_min']}–×{audit['factor_max']}.",
        (
            f"- Исходный output_g есть у {audit['source_output_present_events']} "
            f"MealEvents, отсутствует у {audit['source_output_missing_events']}."
        ),
        (
            "- **Физически подтверждённых порций: 0.** Нет подтверждённых "
            "индивидуальных физических границ и применимости готового выхода."
        ),
        "",
        "## Первые для проверки по коэффициенту (не рейтинг опасности)",
        "",
        "| Дата | Блюдо | Участник | Доля | Техническая энергия, ккал | Выход |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    sorted_rows = sorted(
        rows,
        key=lambda r: (
            -Decimal(r["portion_factor"]),
            r["date"],
            r["position"],
            r["member_ordinal"],
        ),
    )
    for row in sorted_rows[:10]:
        name = row["recipe_title_ru"].replace("|", r"\|")
        lines.append(
            f"| {row['date']} | {name} | №{row['member_ordinal']} | "
            f"×{row['portion_factor']} | {row['technical_energy_kcal']} "
            f"| {row['source_output_status']} |"
        )
    lines.extend(
        [
            "",
            "## Что нужно для настоящих порций",
            "",
            (
                "1. Проверить оригинальный съедобный выход блюда и базис порций "
                "для конкретного RecipeVersion, не выводя его из сырого веса."
            ),
            (
                "2. Утвердить применимую физическую политику порций для участников "
                "и блюд; не вводить универсальный максимум коэффициента."
            ),
            (
                "3. Лишь затем проверять новое правило отбора Planner на полной "
                "семейной неделе; сохранённые планы не переписывать."
            ),
            "",
            "**PORTION_RELEASE_READY=NOT_PROVEN. Prep/Gate2 не разрешены.**",
            "",
        ]
    )
    return "\n".join(lines)
