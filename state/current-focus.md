# Current focus

Updated: 2026-10-03.

## Accepted state

PR #136 / R2-E Contract Gate is merged into `main` at:

`ea30ae82a253ee712d211b3b19caf53e9d2ccc45`.

Merged contract:

`docs/family-food/r2e-cottage-casserole-gate.md`.

Current ordinary active exact-energy Planner pool before R2-E runtime remains:

- BREAKFAST: 6 RecipeVersions / capacity 18 opportunities per week;
- MAIN: 5 RecipeVersions / capacity 15 opportunities per week;
- `max_recipe_repetitions=3`.

Under hard `MILK_2_5` exclusion only `HARD_BOILED_EGG` is currently
unaffected, so capacity is 3/week.

## Current bounded operation

**R2-E runtime — publish School2022 54-1т cottage-cheese casserole.**

Issue: `#137`.

Branch: `feat/r2e-cottage-casserole-runtime`.

Accepted base:

`ea30ae82a253ee712d211b3b19caf53e9d2ccc45`.

Status:

`R2E_RUNTIME_ACTIVE`.

## Frozen runtime scope

Publish exactly:

`SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE` —
Запеканка из творога — 150 g / exact same-card 301.2 kcal.

Create identity-only FoodIngredients:

- `TVOROG_5`;
- `SEMOLINA_GROATS`;
- `SOUR_CREAM_15`;
- `VANILLIN`.

Reuse exact existing identities:

- `SUGAR`;
- `BREADCRUMBS`;
- `EGG`;
- `BUTTER_PEASANT_72_5_UNSALTED`;
- `SALT_IODIZED`;
- `WATER`.

Runtime must reuse `PREPARED_OUTPUT_V1`, keep the other 53 frozen nutrients
UNKNOWN, publish RecipeVersion + prepared authority atomically, and activate only
through the existing guarded boundary.

## Required proof

- fresh publication + guarded activation;
- exact replay is zero-write;
- deliberate deactivation remains deactivated;
- contract tamper / identity conflict / partial state / wrong 301.3 authority
  fail closed;
- four new identities have no Nutrition/Composition;
- ordinary seven-BREAKFAST production planning remains successful;
- hard `MILK_2_5` exclusion leaves `HARD_BOILED_EGG + 54-1т` unaffected but
  the seven-BREAKFAST week fails boundedly with no partial MealPlan because
  capacity is only 6/week;
- migration head remains 0042;
- `AI_ENABLED=false`.

## Scope boundaries

Do not:

- add migration 0043 or schema changes;
- change Planner scoring/role compatibility/repetition;
- grant Nutrition/Composition to the four new foods;
- repair 54-4т/54-6т;
- admit medical-scope 54-7т;
- start another SANDWICH/source-family operation;
- start DC4/Gate1-CLOSE/PR9;
- start API/UI/Prep/Retail/Auth/PostgreSQL/AI.

## Next step

Implement the merged contract, run focused/affected verification on the exact
runtime head, update progress/handoff with the verification receipt, create the
review-ready PR, and stop for independent review.
