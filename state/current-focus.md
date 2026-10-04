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

Accepted base:

`dcc5f37f57a83283e4dee0d3c2957ed0704e9a46`.

Status:

`IN_PROGRESS`.

Canonical contract:

`docs/family-food/r3b-school2022-breakfast-batch-gate.md`.

## Exact runtime scope

Publish exactly:

- `54-2о`, `54-3о`, `54-4о`;
- `54-2т`;
- `54-1к`, `54-2к`, `54-6к`, `54-16к`, `54-23к`, `54-24к`.

Create/reconcile exactly three identity-only FoodIngredients:

- `CHEESE_SEMI_HARD_UNSPECIFIED`;
- `CORN_GROATS`;
- `MILLET_GROATS`.

No NutritionProfile or Composition authority.

## Required preservation

- all ten RecipeVersions are `breakfast`;
- source quantities/output/ENERGY_KCAL remain exact;
- other 53 frozen nutrients remain UNKNOWN;
- consumer Recipe Steps remain Russian-only;
- omelets `54-2о/3о/4о` publish only oven branch `180–200 °C / 8–10 минут`;
- steam `25–30 минут` remains provenance-only;
- excluded `54-3т/54-21к/54-22к/54-7т` remain unpublished.

## Transaction semantics

Reuse merged R3-A option B:

1. per-recipe atomic inactive publication;
2. partial exact inactive subset may remain after failure;
3. rerun zero-write for exact rows and converges missing rows;
4. activation starts only after all ten reconcile exactly;
5. all inactive -> one batch UoW / one commit;
6. all active -> zero-write replay;
7. mixed active/inactive -> fail closed;
8. activation failure -> rollback all staged activation writes.

No new activation architecture.

## Hard milk proof

All ten R3-B recipes depend on `MILK_2_5`.

Runtime must prove exact hard exclusion:

- rejects all 10 R3-B RecipeVersions with `MEMBER_EXCLUDED_INGREDIENT`;
- no R3-B RecipeVersion enters the plan;
- unaffected set remains exactly:
  `HARD_BOILED_EGG`,
  `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`,
  `SAD28_SANDWICH_CHEESE_20_10`;
- count 3 / repetition capacity 9;
- authoritative seven-breakfast generation succeeds.

## Scope boundaries

Do not:

- split recipes into separate PRs;
- create a separate activation PR;
- add migration 0043 or schema changes;
- change Planner mapping/scoring/repetition;
- add a new Nutrition authority;
- start R3-C or DC4;
- start Gate1-CLOSE/PR9/Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.

Verification pending on runtime implementation. Do not merge autonomously.
