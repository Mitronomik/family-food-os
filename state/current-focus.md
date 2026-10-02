# Current focus

Updated: 2026-10-02.

## Accepted state

PR #126 / R1-C is merged into `main` at:

`8995e85e4cda2ae30fc62fdc63daaf441f4226bd`.

R1-C proved the ordinary production Planner path end to end.

## Current bounded operation

**R2 — Breakfast Planner-capacity runtime batch.**

Issue: `#127`.

PR: `#128`.

Branch: `feat/r2-breakfast-capacity`.

Accepted base:

`8995e85e4cda2ae30fc62fdc63daaf441f4226bd`.

Proof/runtime freeze:

`1d93631b07a25a260b7d45cc0b91f3437865fd8a`.

Status:

`READY_FOR_FINAL_REVIEW`.

## R2 result

R2 closes the current BREAKFAST capacity bottleneck without changing Planner
rules, schema or Nutrition authority mechanics.

Published/activated through the existing prepared-output path:

- `SCHOOL2022_54_1O_NATURAL_OMELET` —
  Омлет натуральный — 150 g / exact 225.5 kcal;
- `SCHOOL2022_54_9K_MILK_OAT_PORRIDGE` —
  Каша вязкая молочная овсяная — 200 g / exact 272.9 kcal.

New identity-only FoodIngredients:

- `MILK_2_5` — Молоко 2,5%;
- `OAT_GROATS` — Крупа овсяная.

Neither receives Nutrition or Composition authority.

The exact milk identity deliberately does not claim a pasteurization subtype:
School2022 pins 2.5% fat but allows multiple heat-treatment modes. Oat groats are
kept distinct from existing `OATS_ROLLED`.

Prepared Nutrition remains:

`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

Only ENERGY_KCAL is AVAILABLE for each new RecipeVersion; all other frozen
nutrient codes remain UNKNOWN.

## Planner capacity after R2

Ordinary active exact-energy BREAKFAST pool:

- `HARD_BOILED_EGG`;
- `SCHOOL2022_54_1O_NATURAL_OMELET`;
- `SCHOOL2022_54_9K_MILK_OAT_PORRIDGE`.

With unchanged `max_recipe_repetitions=3`:

- active exact-energy breakfast count: 1 → 3;
- breakfast opportunity capacity: 3 → 9/week;
- a persisted seven-BREAKFAST production week is feasible and proven;
- all three candidates are used and none exceeds repetition 3.

Hard exclusion of `MILK_2_5` removes both new breakfast candidates, restores
explicit bounded infeasibility, and persists no partial MealPlan.

## Evidence / failure semantics

The R2 package pins:

- accepted private corpus archive SHA-256;
- School2022 PDF SHA-256;
- exact source card / source variant / source process / selected route hashes;
- exact energy-reconciliation hashes;
- bounded household-applicability decisions for only these two cards;
- exact FoodIngredient identity decisions.

Runtime proves:

- fresh publication;
- exact zero-write replay;
- deliberate deactivation preservation;
- tampered frozen contract fails closed;
- partial Recipe without prepared authority fails closed;
- conflicting FoodIngredient identity fails closed.

## Verification

Exact proof/runtime-freeze verification at `1d93631...`:

- focused/affected R2 suite — **120 passed**;
- Ruff check — SUCCESS;
- Ruff format --check — SUCCESS;
- scope/whitespace — SUCCESS;
- `AI_ENABLED=false`;
- migration head remains `0042_recipe_prepared_output_nutrition`;
- migration 0043 is absent.

Earlier red runs were task-local lint/connector-format defects only. They did not
require runtime, schema, Planner or authority changes.

## Scope boundaries

Do not:

- add migration 0043 or schema changes;
- add a new Nutrition authority kind;
- add Nutrition/Composition to `MILK_2_5` or `OAT_GROATS`;
- infer milk heat-treatment subtype or rolled-oats equivalence;
- change Planner algorithm/scoring/roles/repetition;
- publish School2022 54-1р in this PR;
- infer closure of USSR82 467/492/1081;
- start DC4 / Gate1-CLOSE;
- start PR9 Shopping;
- start Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI.

## Next step

Independent final review of PR #128.

After explicit review and merge, reassess the next R2/R3 corpus batch by maximum
marginal realistic weekly variety and corpus closure.

Do not start DC4, Gate1-CLOSE or PR9 automatically.
