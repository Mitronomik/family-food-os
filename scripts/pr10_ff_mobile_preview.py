"""Self-contained, mobile-first internal view of the accepted synthetic week.

Presentation only. No remote assets, real family UI, trusted Prep instructions,
price inference or changes to authoritative Planner / Shopping quantities.
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_CEILING, Decimal, InvalidOperation
from html import escape

from scripts.pr10_ff_week_preview import WeekPreviewBlocked, render_markdown

_WEEKDAY_RU = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
_ROLE_RU = {"BREAKFAST": "Завтрак", "LUNCH": "Обед", "DINNER": "Ужин"}
_UNITS = {"g": ("г", "кг"), "ml": ("мл", "л"), "pcs": ("шт.", None)}

_CSS = """
:root{color-scheme:light;--ink:#202a25;--muted:#65736b;--line:#e3e9e4;
--paper:#fcfcf9;--white:#fff;--accent:#185d41;--soft:#eaf4ed;--warn:#fff4df}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;
background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,-apple-system,
BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:inherit}button,input{font:inherit}.container{width:min(100% - 32px,900px);margin:auto}
header{padding:25px 0 16px}.brand{font-size:14px;letter-spacing:.08em;font-weight:800;
color:var(--accent)}.eyebrow{font-size:12px;color:var(--muted);text-transform:uppercase;
letter-spacing:.08em;font-weight:750}.hero{padding:24px;border-radius:22px;
background:var(--soft);margin-bottom:17px}.hero h1{margin:4px 0 8px;
font-size:clamp(25px,5vw,39px);letter-spacing:-.035em;line-height:1.13}
.hero p{margin:0;color:#44554c}.numbers{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}
.metric{background:#fff9;padding:8px 12px;border-radius:12px;font-size:13px}
.metric strong{font-size:18px;color:var(--accent)}.notice{padding:14px 16px;
border:1px solid #eccd8b;background:var(--warn);border-radius:13px;font-size:14px;
margin:15px 0}.nav{position:sticky;top:0;z-index:2;background:var(--paper);
padding:10px 0;display:flex;gap:8px;overflow-x:auto;border-bottom:1px solid var(--line)}
.nav a{white-space:nowrap;text-decoration:none;padding:9px 14px;background:#fff;
border:1px solid var(--line);border-radius:100px;font-size:14px;font-weight:650}
.nav a:hover,.nav a:focus-visible{border-color:var(--accent);color:var(--accent)}
section{scroll-margin-top:85px;margin:31px 0}h2{font-size:25px;letter-spacing:-.025em;
margin:0 0 8px}h3{font-size:18px;margin:0}p{margin:6px 0 14px}.muted{color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));
gap:12px;margin-top:16px}.day{background:var(--white);padding:17px;
border:1px solid var(--line);border-radius:17px}.day-title{display:flex;
justify-content:space-between;gap:10px;padding-bottom:12px;margin-bottom:4px;
border-bottom:1px solid var(--line)}.day-date{font-size:13px;color:var(--muted)}
.meal{padding:10px 0;border-bottom:1px solid #eff1ed}.meal:last-child{border:0}
.role{font-size:12px;color:var(--accent);font-weight:750}.dish{font-weight:650}
.servings{font-size:12px;color:var(--muted);margin-top:4px}.buy-controls{display:flex;
gap:8px;align-items:center;flex-wrap:wrap;margin:14px 0}
.search{width:min(100%,400px);min-width:200px;flex:1;
padding:12px 14px;border-radius:12px;border:1px solid #afbab0;background:#fff}
.counter{font-size:13px;color:var(--muted)}.shopping{display:grid;gap:8px}
.item{background:#fff;border:1px solid var(--line);border-radius:13px;
padding:12px 14px;display:flex;align-items:center;gap:13px;cursor:pointer}
.item:focus-within{outline:2px solid var(--accent);outline-offset:1px}
.item input{accent-color:var(--accent);width:20px;height:20px;flex-shrink:0}
.item-name{flex:1;min-width:0}.item-price{font-weight:750;white-space:nowrap}
.item.checked .item-name,.item.checked .item-price{text-decoration:line-through;
color:var(--muted)}[hidden]{display:none!important}
.grocery-row{border:1px solid var(--line);border-radius:13px;background:#fff;overflow:hidden}
.grocery-row .item{border:0;border-radius:0}
.origins{border:0;border-top:1px solid var(--line);margin:0;border-radius:0;
padding:10px 14px;background:#fcfcf9;font-size:13px}
.origins summary{color:var(--accent)}.origins ul{margin:8px 0;padding-left:20px}
.origins li{margin:5px 0}.origins p{margin:8px 0;color:var(--muted)}
.origin-water{border-left:3px solid #d49f31;padding-left:10px;color:#70521b!important}
details{background:#fff;
border:1px solid var(--line);padding:12px 16px;border-radius:12px;margin-top:16px}
summary{font-weight:650;cursor:pointer}table{border-collapse:collapse;width:100%;
font-size:12px;margin-top:12px}td,th{text-align:left;border-bottom:1px solid var(--line);
padding:7px 5px}td:nth-child(n+2),th:nth-child(n+2){text-align:right}
.table-scroll{overflow-x:auto}.locked{padding:17px;background:#fff;
border:1px solid var(--line);border-radius:14px}footer{padding:20px 0 35px;
font-size:12px;color:var(--muted);border-top:1px solid var(--line)}
@media(max-width:540px){.container{width:min(100% - 24px,900px)}
.hero{padding:18px}.day{padding:14px}.item-price{font-size:14px}}
@media print{.nav,.search,.counter,.item input{display:none}body{background:#fff}
.day,.item{break-inside:avoid}section{margin:15px 0}.grid{display:block}
.day{margin-bottom:8px}.item{padding:5px 0;border:0;border-bottom:1px solid #ddd}
.hero{padding:8px}.notice{border:1px solid #ddd}}
"""

_SCRIPT = """
(() => {
  const rows = Array.from(document.querySelectorAll('.grocery-row'));
  const search = document.querySelector('#search');
  const counter = document.querySelector('#counter');
  function update() {
    const needle = search.value.trim().toLocaleLowerCase('ru');
    let checked = 0;
    for (const row of rows) {
      const tick = row.querySelector('input[type=checkbox]');
      row.hidden = !row.dataset.label.toLocaleLowerCase('ru').includes(needle);
      row.querySelector('.item').classList.toggle('checked', tick.checked);
      if (tick.checked) checked++;
    }
    counter.textContent = 'Отмечено ' + checked + ' из ' + rows.length;
  }
  search.addEventListener('input', update);
  for (const row of rows) row.querySelector('input').addEventListener('change', update);
  update();
})();
"""


def _html(value):
    return escape(str(value), quote=True)


def _quantity(value, unit):
    """Monotonic display rounding; never understate the canonical buy amount."""
    if unit not in _UNITS or not isinstance(value, str):
        raise WeekPreviewBlocked("Unknown grocery unit or non-string quantity")
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise WeekPreviewBlocked("Invalid grocery quantity") from exc
    if not amount.is_finite() or amount < 0:
        raise WeekPreviewBlocked("Negative/nonfinite grocery quantity")
    rounded = amount.to_integral_value(rounding=ROUND_CEILING)
    if unit != "pcs" and amount >= 1000:
        number = f"{rounded / Decimal(1000):.3f}".replace(".", ",")
        return number + " " + _UNITS[unit][1]
    return str(rounded) + " " + _UNITS[unit][0]


def render_html(preview):
    """Build offline HTML after the exact same fail-closed contract as Markdown."""
    render_markdown(preview)
    menu = preview["menu"]
    groceries = preview["shopping"]
    if (
        preview.get("pantry_state") != "EXPLICIT_EMPTY_TEST_PANTRY"
        or preview.get("shopping_status") != "COMPLETE"
    ):
        raise WeekPreviewBlocked("Untrusted grocery and pantry claim")
    if len({row["food_code"] for row in groceries}) != len(groceries):
        raise WeekPreviewBlocked("Duplicate grocery identity")

    groceries_html = []
    raw_rows = []
    meal_codes = {
        (item["date"], item["position"], item["role"], item["recipe_code"]): item["title_ru"]
        for item in menu
    }
    if len(meal_codes) != len(menu):
        raise WeekPreviewBlocked("Ambiguous meal identity for Shopping sources")
    for i, row in enumerate(groceries, 1):
        required = Decimal(str(row["required"]))
        at_home = Decimal(str(row["at_home"]))
        purchase = Decimal(str(row["to_buy"]))
        if (
            any(not x.is_finite() or x < 0 for x in (required, at_home, purchase))
            or at_home != 0
            or purchase != required
        ):
            raise WeekPreviewBlocked("Grocery rows contradict explicit empty Pantry")
        display = _quantity(row["to_buy"], row["unit"])
        name = _html(row["title_ru"])
        sources = row.get("origins")
        if not isinstance(sources, list) or not sources:
            raise WeekPreviewBlocked("Shopping item lacks real source breakdown")
        origin_markup = []
        seen_origins = set()
        rounded_source_total = Decimal(0)
        for source in sources:
            identity = (
                source["date"],
                source["position"],
                source["role"],
                source["recipe_code"],
            )
            if (
                identity in seen_origins
                or meal_codes.get(identity) != source["recipe_title_ru"]
                or source["unit"] != row["unit"]
                or not isinstance(source["position"], int)
                or source["position"] < 1
            ):
                raise WeekPreviewBlocked("Unknown or duplicated Shopping meal origin")
            seen_origins.add(identity)
            try:
                amount = Decimal(source["source_demand_up_001"])
            except (InvalidOperation, ValueError, TypeError) as exc:
                raise WeekPreviewBlocked("Invalid Shopping origin amount") from exc
            if (
                not amount.is_finite()
                or amount <= 0
                or amount != amount.quantize(Decimal("0.001"))
            ):
                raise WeekPreviewBlocked("Unreliable Shopping origin precision")
            rounded_source_total += amount
            origin_markup.append(
                f"<li>{_html(source['date'])} · "
                f"{_html(source['recipe_title_ru'])}: "
                f"{_html(source['source_demand_up_001'])} {_html(row['unit'])}</li>"
            )
        # Each source event is rounded UP independently for explanation;
        # the canonical gross is CEILING(aggregate of UNROUNDED events).
        if (
            rounded_source_total < required
            or rounded_source_total - required
            >= Decimal("0.001") * len(sources)
        ):
            raise WeekPreviewBlocked("Displayed origin totals contradict Shopping gross")
        water_note = (
            '<p class="origin-water">Вода учтена как рецептурный ингредиент. '
            'Это не подтверждает необходимость покупать бутилированную воду.</p>'
            if row["food_code"] == "WATER"
            else ""
        )
        groceries_html.append(
            f'<div class="grocery-row" data-label="{name}">'
            f'<label class="item">'
            f'<input type="checkbox" aria-label="Отметить: {name}">'
            f'<span class="item-name">{name}</span>'
            f'<span class="item-price">{_html(display)}</span></label>'
            f'<details class="origins"><summary>Из каких блюд: {len(sources)}</summary>'
            '<p>На блюдо округлено вверх до 0,001. Итог считается отдельно '
            'по сумме исходных количеств.</p>'
            + water_note
            + "<ul>"
            + "".join(origin_markup)
            + "</ul></details></div>"
        )
        raw_rows.append(
            f"<tr><td>{name}</td><td>{_html(row['required'])} {_html(row['unit'])}</td>"
            f"<td>{_html(row['at_home'])} {_html(row['unit'])}</td>"
            f"<td>{_html(row['to_buy'])} {_html(row['unit'])}</td></tr>"
        )

    by_date = {}
    for row in menu:
        by_date.setdefault(row["date"], []).append(row)
    days_html = []
    for date_text, meals in sorted(by_date.items()):
        try:
            current = date.fromisoformat(date_text)
        except ValueError as exc:
            raise WeekPreviewBlocked("Invalid source week date") from exc
        label = _WEEKDAY_RU[current.weekday()]
        meal_html = []
        for row in meals:
            if row["role"] not in _ROLE_RU:
                raise WeekPreviewBlocked("Unknown meal role")
            servings = " · ".join(
                f"№{_html(s['member_ordinal'])}: ×{_html(s['portion_servings'])}"
                for s in row["servings"]
            )
            meal_html.append(
                '<div class="meal">'
                f'<div class="role">{_ROLE_RU[row["role"]]}</div>'
                f'<div class="dish">{_html(row["title_ru"])}</div>'
                f'<div class="servings">Доли рецепта: {servings}</div></div>'
            )
        days_html.append(
            '<article class="day">'
            f'<div class="day-title"><h3>{label}</h3>'
            f'<span class="day-date">{current.day:02d}.{current.month:02d}</span></div>'
            + "".join(meal_html)
            + "</article>"
        )

    if sum(len(x["servings"]) for x in menu) != 42 or len(days_html) != 7:
        raise WeekPreviewBlocked("Inconsistent individual servings/week")
    return (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow">'
        "<title>FamilyFoodOS — техническая демонстрационная неделя</title>"
        f'<style>{_CSS}</style></head><body><div class="container">'
        '<header><div class="brand">FAMILYFOODOS</div></header>'
        '<div class="hero"><div class="eyebrow">Внутренний прототип · без AI</div>'
        "<h1>Демонстрационная неделя</h1>"
        "<p>2–8 ноября 2026 · синтетическая семья, а не рекомендация рациона</p>"
        '<div class="numbers"><div class="metric"><strong>7</strong> дней</div>'
        '<div class="metric"><strong>21</strong> приём пищи</div>'
        '<div class="metric"><strong>42</strong> доли рецептов</div>'
        f'<div class="metric"><strong>{len(groceries)}</strong> продуктов</div></div></div>'
        '<div class="notice"><strong>Важные ограничения.</strong> Полная пищевая '
        "ценность и масса готовых порций не подтверждены. Цены неизвестны. "
        "Заготовки и хранение не разрешены. Это не готовое меню для семьи.</div>"
        '<nav class="nav" aria-label="Разделы">'
        '<a href="#week">Неделя</a><a href="#buy">Купить</a>'
        '<a href="#prep">Заготовки</a></nav>'
        '<main><section id="week"><h2>Неделя</h2>'
        '<p class="muted">Коэффициенты × показывают долю базового рецепта, '
        "а не граммы готового блюда.</p>"
        f'<div class="grid">{"".join(days_html)}</div></section>'
        '<section id="buy"><h2>Купить</h2>'
        '<p class="muted">Только исходные ингредиенты. Pantry в этом примере пуст. '
        "Для удобства масса и объём округлены <strong>вверх</strong> до целых "
        "граммов или миллилитров; исходные значения доступны ниже. "
        "Упаковки, штуки яиц и цены не определены.</p>"
        '<div class="notice">Отметки покупок действуют только на этой странице '
        "и <strong>не сохраняются</strong> в Pantry.</div>"
        '<div class="buy-controls"><input id="search" class="search" type="search" '
        'placeholder="Найти продукт" aria-label="Поиск по покупкам">'
        '<span class="counter" id="counter"></span></div>'
        f'<div class="shopping">{"".join(groceries_html)}</div>'
        "<details><summary>Точные расчётные количества</summary>"
        '<div class="table-scroll"><table><thead><tr><th>Ингредиент</th>'
        "<th>Нужно</th><th>Дома</th><th>Купить</th></tr></thead><tbody>"
        f"{''.join(raw_rows)}</tbody></table></div></details></section>"
        '<section id="prep"><h2>Заготовки</h2><div class="locked">'
        "<strong>Пока недоступны.</strong><p>Нет независимо проверенных "
        "исполняемых инструкций, сроков хранения или правил заморозки. "
        "Никаких готовых запасов не создано.</p></div></section></main>"
        "<footer>Техническая проверка существующего Planner и Shopping; "
        "не Gate2, не consumer PWA, не медицинская или пищевая рекомендация. "
        "Все отметки покупок локальные.</footer></div>"
        f"<script>{_SCRIPT}</script></body></html>"
    )
