# Current focus

Updated: 2026-10-03.

## Accepted state

PR #132 / R2-C is merged into `main` at:

`463fe46f7c40156c1b8ebab5402ca45698d8c2bc`.

Current ordinary active exact-energy Planner pool:

- BREAKFAST: 6 RecipeVersions / capacity 18 opportunities per week;
- MAIN: 5 RecipeVersions / capacity 15 opportunities per week;
- `max_recipe_repetitions=3`;
- persisted seven-BREAKFAST and seven-DINNER paths are proven.

Under hard `MILK_2_5` exclusion, five of six BREAKFAST recipes are removed.
Only `HARD_BOILED_EGG` remains, so BREAKFAST capacity becomes 3/week and a
seven-BREAKFAST week is bounded-infeasible.

## Current bounded operation

**R2-D — Milk-exclusion breakfast resilience Contract Gate.**

Issue: `#133`.

Branch: `docs/r2d-milk-exclusion-breakfast-gate`.

Accepted base:

`463fe46f7c40156c1b8ebab5402ca45698d8c2bc`.

Status:

`CORRECTION_VERIFYING`.

## Evidence result

The nearest retained candidates are not runtime-ready:

- School2022 54-1т / Запеканка из творога:
  prepared energy is **READY_SAME_CARD_EXACT** at 301.2 kcal / 150 g under the
  accepted `PREPARED_OUTPUT_V1` rule; retained 301.3 kcal menu rows are
  non-blocking QA evidence only. Runtime publication remains
  `REVIEW_REQUIRED_FOOD_IDENTITY_AND_HOUSEHOLD_APPLICABILITY`;
- School2022 54-4т / Пудинг из творога с яблоками:
  `BLOCKED_REQUIRED_PROCESS_QUANTITY_UNRESOLVED`
  because process water for dissolving vanillin is not quantified;
- School2022 54-6т / Сырники:
  the same `BLOCKED_REQUIRED_PROCESS_QUANTITY_UNRESOLVED` blocker;
- USSR82-459 fallback remains `PRODUCTION_RECONCILIATION_REQUIRED`; its retained
  secondary nutrient row has `EnergyQA=CHECK` and is not prepared-output authority.

No runtime RecipeVersion/FoodIngredient publication is authorized by this gate.

## Scope boundaries

Do not:

- publish/activate an R2-D RecipeVersion;
- create new FoodIngredient identities;
- choose 301.2 vs 301.3 implicitly;
- invent/default/omit unquantified process water;
- add migration 0043 or schema changes;
- change Planner scoring, role compatibility or repetition;
- add another Nutrition authority kind;
- start DC4 / Gate1-CLOSE;
- start PR9 Shopping;
- start Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI.

## Next step

Independent final review found one contract blocker: 54-1т was incorrectly
treated as blocked by 301.2/301.3 cross-record energy variance. The correction
restores the accepted same-card prepared-output authority rule: 301.2 kcal is the
exact source-card candidate value; 301.3 kcal is QA-only.

Correction verification is now required on the new exact head before returning
PR #134 to final review.

After review and merge, make one separate bounded evidence decision:

1. close School2022 quantity/energy authority gaps; or
2. investigate a clean BREAKFAST/SANDWICH source family for higher role coverage.

Do not start either follow-up automatically.
