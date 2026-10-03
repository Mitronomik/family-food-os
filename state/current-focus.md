# Current focus

Updated: 2026-10-03.

## Accepted state

PR #130 / R2-B is merged into `main` at:

`13a81d2497737f3b275b10055cd084548be02bf3`.

Before R2-C the ordinary active exact-energy Planner pool is:

- BREAKFAST: 3 RecipeVersions / capacity 9 opportunities per week;
- MAIN: 5 RecipeVersions / capacity 15 opportunities per week;
- `max_recipe_repetitions=3`;
- persisted seven-BREAKFAST and seven-DINNER paths are proven.

## Current bounded operation

**R2-C — Breakfast grain diversity batch.**

Issue: `#131`.

PR: `#132`.

Branch: `feat/r2c-breakfast-grain-diversity`.

Accepted base:

`13a81d2497737f3b275b10055cd084548be02bf3`.

Proof/runtime freeze:

`5dc3bda151d412662f75e7cd64ae7f1811bb25c7`.

Status:

`READY_FOR_FINAL_REVIEW`.

## R2-C result

Published/activated through the existing prepared-output path:

- `SCHOOL2022_54_13K_WHEAT_MILK_PORRIDGE` —
  Каша вязкая молочная пшеничная —
  200 g / exact 270.3 kcal;
- `SCHOOL2022_54_20K_BUCKWHEAT_MILK_PORRIDGE` —
  Каша жидкая молочная гречневая —
  200 g / exact 187.3 kcal;
- `SCHOOL2022_54_25_1K_RICE_MILK_PORRIDGE` —
  Каша жидкая молочная рисовая —
  200 g / exact 184.5 kcal.

New identity-only FoodIngredient:

- `WHEAT_GROATS` — Крупа пшеничная.

Neither Nutrition nor Composition authority is published for that identity.

Existing exact identities are reused for:

- `BUCKWHEAT`;
- `RICE_GROATS`;
- `MILK_2_5`;
- `BUTTER_PEASANT_72_5_UNSALTED`;
- `SUGAR`;
- `SALT_IODIZED`;
- `WATER`.

Prepared Nutrition remains:

`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

Only ENERGY_KCAL is AVAILABLE; all remaining frozen nutrient codes are UNKNOWN.

## Planner capacity after R2-C

Ordinary active exact-energy BREAKFAST count:

3 → 6 RecipeVersions.

Opportunity capacity under unchanged `max_recipe_repetitions=3`:

9 → 18/week.

A persisted seven-BREAKFAST production week with all three new grain recipes
preferred:

- succeeds;
- selects all three new RecipeVersions;
- uses no RecipeVersion more than 3 times;
- persists MealPlan and individualized Servings.

Hard exclusion of `WHEAT_GROATS` removes only the wheat porridge candidate while
the week remains feasible through the remaining breakfast pool.

## Source / consumer boundary

The R2-C package pins exact:

- corpus archive and School2022 PDF identity;
- source-card hashes;
- required ingredient-row hashes;
- process-text hashes;
- energy-reconciliation hashes.

Institutional serving-temperature requirements remain provenance-only.

Source time ranges are preserved inside Russian RecipeSteps. No exact scalar
cook-time is invented where the source provides only ranges.

The rice RecipeIngredient preserves the exact Russian source text:

`крупа рисовая: брутто 30,8 г; нетто 30,8 г`

while the canonical numeric quantity remains Decimal 30.8.

## Failure / replay semantics

Verified:

- fresh publication;
- exact zero-write replay;
- deliberate deactivation remains deactivated;
- tampered frozen publication contract fails closed;
- partial Recipe without prepared authority fails closed;
- conflicting `WHEAT_GROATS` identity fails closed.

## Verification

Exact proof/runtime-freeze verification at `5dc3bda1...`:

- focused/affected R2-C suite — **136 passed**;
- Ruff check — SUCCESS;
- Ruff format --check — SUCCESS;
- scope/whitespace — SUCCESS;
- six exact-energy BREAKFAST candidates / capacity eighteen — PASS;
- persisted grain-diverse seven-BREAKFAST proof — PASS;
- hard wheat FoodIngredient exclusion — PASS;
- `AI_ENABLED=false`;
- migration head remains `0042_recipe_prepared_output_nutrition`;
- migration 0043 is absent.

The first R2-C run already passed all 136 functional tests and failed only Ruff
format. The subsequent provenance correction preserved exact Russian
`source_amount_text` for rice and is covered by a regression assertion. The
corrected exact head above is fully green.

## Scope boundaries

Do not:

- add migration 0043 or schema changes;
- add another Nutrition authority kind;
- add Nutrition/Composition to `WHEAT_GROATS`;
- infer wheat-groats equivalence to flour/bulgur/whole-wheat;
- replace `RICE_GROATS` with generic rice;
- change Planner algorithm/scoring/roles/repetition;
- publish side/salad/soup roles in this PR;
- add allergen automation;
- start another corpus batch;
- start DC4 / Gate1-CLOSE;
- start PR9 Shopping;
- start Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI.

## Next step

Independent final review of PR #132.

After explicit review and merge, reassess the next R2/R3 corpus batch by maximum
marginal realistic weekly variety and corpus closure.

Do not start DC4, Gate1-CLOSE or PR9 automatically.
