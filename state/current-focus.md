# Current focus

Updated: 2026-10-03.

## Accepted state

PR #134 / R2-D is merged into `main` at:

`99a579e35b0a0fa6d09947b80ffecb222a45bf96`.

Current ordinary active exact-energy Planner pool remains:

- BREAKFAST: 6 RecipeVersions / capacity 18 opportunities per week;
- MAIN: 5 RecipeVersions / capacity 15 opportunities per week;
- `max_recipe_repetitions=3`.

Under hard `MILK_2_5` exclusion only `HARD_BOILED_EGG` remains active, so
BREAKFAST capacity is 3/week and a seven-BREAKFAST week is infeasible.

R2-D also established that School2022 54-1т has exact same-card prepared energy
301.2 kcal / 150 g; menu 301.3 kcal is QA-only.

## Current bounded operation

**R2-E — School2022 54-1т identity + household-applicability Contract Gate.**

Issue: `#135`.

Branch: `docs/r2e-cottage-casserole-gate`.

Accepted base:

`99a579e35b0a0fa6d09947b80ffecb222a45bf96`.

Status:

`READY_FOR_FINAL_REVIEW`.

## Frozen candidate

`SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE` — Запеканка из творога — 150 g / 301.2 kcal.

New identity-only FoodIngredients:

- `TVOROG_5`;
- `SEMOLINA_GROATS`;
- `SOUR_CREAM_15`;
- `VANILLIN`.

Exact existing identities reused:

- `SUGAR`;
- `BREADCRUMBS`;
- `EGG`;
- `BUTTER_PEASANT_72_5_UNSALTED`;
- `SALT_IODIZED`;
- `WATER`.

No Nutrition/Composition is granted to the four new identities.

54-1т is reviewed `HOUSEHOLD_APPLICABLE`; institutional serving temperature
and paraconvection context remain provenance-only.

## Product boundary

A future runtime activation would increase hard-`MILK_2_5` unaffected
BREAKFAST capacity only from 3 → 6/week.

It does **not** close seven-BREAKFAST feasibility.

## Scope boundaries

Do not:

- publish/activate runtime data in this gate;
- add migration 0043 or schema changes;
- change Planner scoring/roles/repetition;
- grant Nutrition/Composition to the four new foods;
- repair 54-4т/54-6т quantities;
- admit medical-scope 54-7т;
- open a new SANDWICH source authority;
- start DC4/Gate1-CLOSE/PR9.

## Next step

Contract/evidence package is frozen on evidence head:

`444651459e64b9699a034fb4c67d95a45b98b464`.

Verification:

- pinned archive source-card/variant/process/10 ingredient-demand hashes — PASS;
- medical-scope 54-7т record/hash — PASS;
- evidence JSON parse — PASS;
- Docs verification #795 — SUCCESS;
- DC1 corpus verification #652 — SUCCESS;
- changed scope — docs/data/state only;
- runtime/schema/migration diff — none.

Independent final review of PR #136 is next. Do not start runtime implementation
before review and merge.
