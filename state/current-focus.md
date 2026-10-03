# Current focus

Updated: 2026-10-04.

## Accepted state

PR #148 / R3-A ten-recipe MAIN runtime is merged into `main` at:

`69c68f4153b25ac4e51cbe9ff54fb080201f08bd`.

DATA-CORPUS-V1 / DC3 remains active.

Current deterministic exact-energy catalogue is approximately 23 active usable
recipes: 15 MAIN, 7 BREAKFAST and 1 SANDWICH. The breakfast-compatible pool is 8.

The `50–80+` DATA-CORPUS-V1 baseline is not met, so DC4 remains blocked.

## Current bounded operation

**R3-B — School2022 ten-recipe BREAKFAST Contract Gate.**

Issue: `#149`.

Branch: `docs/r3b-school2022-breakfast-batch-gate`.

Accepted base: `69c68f4153b25ac4e51cbe9ff54fb080201f08bd`.

Status: `GATE_CONTENT_FROZEN_PENDING_VERIFICATION`.

Canonical gate:

`docs/family-food/r3b-school2022-breakfast-batch-gate.md`.

## Exact selected set

- `ru-school2022:recipe:54-2о` — Омлет с зеленым горошком;
- `ru-school2022:recipe:54-3о` — Омлет с морковью;
- `ru-school2022:recipe:54-4о` — Омлет с сыром;
- `ru-school2022:recipe:54-2т` — Запеканка из творога с морковью;
- `ru-school2022:recipe:54-3т` — Суфле из моркови с творогом;
- `ru-school2022:recipe:54-1к` — Каша жидкая молочная кукурузная;
- `ru-school2022:recipe:54-6к` — Каша вязкая молочная пшенная;
- `ru-school2022:recipe:54-16к` — Каша «Дружба»;
- `ru-school2022:recipe:54-21к` — Каша вязкая молочная ячневая;
- `ru-school2022:recipe:54-23к` — Каша жидкая молочная пшеничная;

New identity-only demand is exactly:

- `CHEESE_SEMI_HARD_UNSPECIFIED`;
- `CORN_GROATS`;
- `MILLET_GROATS`;
- `BARLEY_GROATS`;

No NutritionProfile or Composition authority.

## Scope boundaries

Do not start runtime before independent gate review/merge.
Do not split recipes into separate PRs.
Do not create a separate activation PR.
Do not add migration 0043/schema/Planner/new Nutrition authority changes.
Do not start R3-C, DC4, Gate1-CLOSE or PR9.

## Source receipt

Independent Library materialize/hash readback on 2026-10-04:

- ZIP 206692075 bytes / `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- PDF 4102547 bytes / `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.

Gate cross-file and Docs/DC1 verification pending.
