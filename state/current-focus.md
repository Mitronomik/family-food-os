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

Branch: `feat/r2c-breakfast-grain-diversity`.

Accepted base:

`13a81d2497737f3b275b10055cd084548be02bf3`.

Status:

`IMPLEMENTATION_ACTIVE`.

## Batch decision

Selected School2022 cards:

- `54-13к` — Каша вязкая молочная пшеничная —
  200 g / exact 270.3 kcal;
- `54-20к` — Каша жидкая молочная гречневая —
  200 g / exact 187.3 kcal;
- `54-25.1к` — Каша жидкая молочная рисовая —
  200 g / exact 184.5 kcal.

New identity-only FoodIngredient:

- `WHEAT_GROATS` — Крупа пшеничная.

Reuse exact accepted identities:

- `BUCKWHEAT`;
- `RICE_GROATS`;
- `MILK_2_5`;
- `BUTTER_PEASANT_72_5_UNSALTED`;
- `SUGAR`;
- `SALT_IODIZED`;
- `WATER`.

Prepared Nutrition remains:

`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

Only ENERGY_KCAL is AVAILABLE; all remaining frozen nutrients are UNKNOWN.

## Product effect target

Ordinary active exact-energy BREAKFAST pool:

3 → 6 RecipeVersions.

Projected opportunity capacity under unchanged repetition=3:

9 → 18 BREAKFAST opportunities/week.

The persisted proof must show a seven-BREAKFAST week that selects all three new
grain-family recipes when preferred, with no RecipeVersion used more than 3 times.

A hard exclusion of `WHEAT_GROATS` must remove only the wheat porridge candidate
while the week remains feasible.

## Source / consumer boundary

Exact source-card / ingredient-row / process / energy-reconciliation hashes are
pinned for all three cards.

Institutional serving-temperature requirements remain provenance-only and are not
consumer RecipeSteps.

Source time ranges such as 20–30 minutes and 2–3 minutes stay in RecipeSteps; no
single cook-time scalar is invented when the source does not provide one.

## Scope boundaries

Do not:

- add migration 0043 or schema changes;
- add another Nutrition authority kind;
- add Nutrition/Composition to `WHEAT_GROATS`;
- infer wheat-groats equivalence to flour/bulgur/whole-wheat forms;
- replace exact `RICE_GROATS` with generic rice;
- change Planner algorithm/scoring/roles/repetition;
- publish side/salad/soup roles in this PR;
- add allergen automation;
- start another corpus batch;
- start DC4 / Gate1-CLOSE;
- start PR9 Shopping;
- start Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI.

## Verification target

R2-C must prove:

- exact hash-pinned source/publication contract;
- bounded household applicability for only the three named cards;
- fresh/replay/deactivation semantics;
- identity-only enforcement;
- tamper/partial/conflict fail-closed behavior;
- active exact-energy BREAKFAST count = 6;
- persisted grain-diverse seven-BREAKFAST week;
- hard wheat exclusion with successful fallback;
- migration head remains 0042;
- `AI_ENABLED=false`.

## Next step

Run exact-head focused R2-C verification, fix task-local defects only, freeze the
verified runtime/evidence head, then hand the PR to independent final review.

After merge, reassess the next R2/R3 batch. Do not start DC4, Gate1-CLOSE or PR9
automatically.
