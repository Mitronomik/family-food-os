# Current focus

Updated: 2026-10-04.

## Accepted state

PR #150 / R3-B School2022 ten-recipe BREAKFAST Contract Gate is merged into `main` at:

`dcc5f37f57a83283e4dee0d3c2957ed0704e9a46`.

DATA-CORPUS-V1 / DC3 remains active.

## Current bounded operation

**R3-B runtime — publish School2022 ten-recipe BREAKFAST batch.**

Issue: `#151`.

Branch:

`feat/r3b-school2022-breakfast-batch-runtime`.

PR:

`#152`.

Accepted base:

`dcc5f37f57a83283e4dee0d3c2957ed0704e9a46`.

Runtime freeze:

`bf4580684140b00404bc91d16b8c7fcda016acb4`.

Status:

`READY_FOR_FINAL_REVIEW`.

Canonical contract:

`docs/family-food/r3b-school2022-breakfast-batch-gate.md`.

## Delivered runtime scope

Exactly ten frozen School2022 BREAKFAST RecipeVersions are published/activated:

- `54-2о`, `54-3о`, `54-4о`;
- `54-2т`;
- `54-1к`, `54-2к`, `54-6к`, `54-16к`, `54-23к`, `54-24к`.

Exactly three identity-only FoodIngredients are reconciled:

- `CHEESE_SEMI_HARD_UNSPECIFIED`;
- `CORN_GROATS`;
- `MILLET_GROATS`.

No NutritionProfile or Composition authority is granted to them.

Every new RecipeVersion uses exact prepared `ENERGY_KCAL`; the other 53 frozen
nutrient codes remain UNKNOWN.

## Transaction result — reused option B

Publication:

1. each inactive RecipeVersion + prepared authority publishes atomically per recipe;
2. a failure may leave only an exact inactive subset;
3. rerun is zero-write for exact rows and converges missing rows;
4. partial/conflicting state fails closed;
5. publication never activates recipes.

Activation:

1. begins only after all ten exact publications reconcile;
2. all inactive -> all ten activate in one caller-owned UoW / one commit;
3. all active -> zero-write replay;
4. mixed active/inactive -> fail closed with zero writes;
5. injected activation failure rolls back all staged activation writes.

R3-B reuses the merged R3-A transaction-neutral activation seam; no new
activation architecture is introduced. R3-B seeding also preserves deliberate
deactivation in the prior R3-A batch.

## Source/product preservation

- runtime consumes only the hash-pinned repository package;
- no live web/Library dependency;
- consumer Recipe Steps remain Russian-only;
- omelets `54-2о/3о/4о` publish only oven branch `180–200 °C / 8–10 минут`;
- steam branch `25–30 минут` remains provenance-only;
- excluded `54-3т/54-21к/54-22к/54-7т` remain unpublished.

## Hard milk proof

All ten R3-B recipes depend on `MILK_2_5`.

Verified hard exclusion:

- all 10 R3-B RecipeVersions rejected with `MEMBER_EXCLUDED_INGREDIENT`;
- no R3-B RecipeVersion enters the plan;
- unaffected breakfast-compatible set remains exactly:
  `HARD_BOILED_EGG`,
  `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`,
  `SAD28_SANDWICH_CHEESE_20_10`;
- count 3 / repetition capacity 9;
- authoritative seven-breakfast generation succeeds.

## Runtime verification on exact freeze

`R3-B School2022 BREAKFAST batch runtime #8` — SUCCESS:

- focused/affected suite: **114 passed**;
- Ruff check: PASS;
- Ruff format: PASS — 4 files already formatted;
- scope/whitespace: PASS;
- exactly 3 identity-only foods / no Nutrition or Composition: PASS;
- exactly 10 BREAKFAST RecipeVersions + prepared authority: PASS;
- per-recipe atomic inactive publication + resumable convergence: PASS;
- one-UoW batch activation + rollback: PASS;
- mixed-state fail-closed / all-active replay: PASS;
- Russian consumer steps + explicit omelet oven branch: PASS;
- hard `MILK_2_5` exclusion / unaffected capacity 9: PASS;
- migration head 0042 / no 0043: PASS;
- `AI_ENABLED=false`: PASS.

Same runtime freeze also has SUCCESS for:

- Docs #892;
- DC1 #749;
- Russian nutrition methodologies #482;
- R1-C #149;
- R2 breakfast #133;
- R2-B #123;
- R2-C #111;
- R2-E #94;
- R2-F #66;
- R3-A #32;
- Nutrient registry V2 #949 including full backend/launcher regression;
- Partial nutrition profiles #704 including full backend/launcher regression.

## Scope boundaries

Do not:

- merge PR #152 autonomously;
- split recipes into separate PRs;
- create a separate activation PR;
- add migration 0043 or schema changes;
- change Planner mapping/scoring/repetition;
- add a new Nutrition authority;
- start R3-C or DC4;
- start Gate1-CLOSE/PR9/Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.

Only state/PR metadata may change after the runtime freeze unless an independent
review finding explicitly reopens runtime verification.
