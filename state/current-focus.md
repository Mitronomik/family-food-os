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

Status: `READY_FOR_FINAL_REVIEW`.

Canonical gate:

`docs/family-food/r3b-school2022-breakfast-batch-gate.md`.

## Exact selected set

- `ru-school2022:recipe:54-2о` — Омлет с зеленым горошком;
- `ru-school2022:recipe:54-3о` — Омлет с морковью;
- `ru-school2022:recipe:54-4о` — Омлет с сыром;
- `ru-school2022:recipe:54-2т` — Запеканка из творога с морковью;
- `ru-school2022:recipe:54-1к` — Каша жидкая молочная кукурузная;
- `ru-school2022:recipe:54-2к` — Каша вязкая молочная кукурузная;
- `ru-school2022:recipe:54-6к` — Каша вязкая молочная пшенная;
- `ru-school2022:recipe:54-16к` — Каша «Дружба»;
- `ru-school2022:recipe:54-23к` — Каша жидкая молочная пшеничная;
- `ru-school2022:recipe:54-24к` — Каша жидкая молочная пшенная;

Adversarial process audit rejected `54-3т` and `54-21к` for quantified sugar without technology placement; they are replaced by source-clean `54-2к` and `54-24к`. `54-22к` remains deferred for quantified butter without technology placement.

New identity-only demand is exactly:

- `CHEESE_SEMI_HARD_UNSPECIFIED`;
- `CORN_GROATS`;
- `MILLET_GROATS`.

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

Content freeze:

`f72c7c51d6758dcb11573ab88e49d51272d80e73`.

Verification on content freeze:

- selection/spec/household/process/source alignment 10/10 — PASS;
- exact source gross/net ingredient rows 10/10 — PASS;
- exact source output + same-card ENERGY_KCAL 10/10 — PASS;
- exactly 3 identity-only foods, no Nutrition/Composition — PASS;
- process-placement adversarial audit — PASS;
- durable ZIP/PDF materialize + SHA-256 — PASS;
- Docs #876 — SUCCESS;
- DC1 #733 — SUCCESS.

Runtime remains blocked until independent review and merge of PR #150.
