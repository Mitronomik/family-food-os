# Current focus

Updated: 2026-10-02.

## Accepted state

PR #128 / R2-A is merged into `main` at:

`1e4a0e137dee87f2aaef7d885481fef17f6e324c`.

Before R2-B the ordinary active exact-energy Planner pool is:

- BREAKFAST: 3 RecipeVersions / capacity 9 opportunities per week;
- MAIN: 3 RecipeVersions / capacity 9 opportunities per week;
- `max_recipe_repetitions=3`;
- persisted seven-BREAKFAST and seven-DINNER paths are proven.

## Current bounded operation

**R2-B — Fish MAIN diversity batch.**

Issue: `#129`.

PR: `#130`.

Branch: `feat/r2b-fish-main-diversity`.

Accepted base:

`1e4a0e137dee87f2aaef7d885481fef17f6e324c`.

Proof/runtime freeze:

`b7691b45f05f3f5e873df53cb02d0cc769f8db79`.

Status:

`READY_FOR_FINAL_REVIEW`.

## R2-B result

Published/activated through the existing prepared-output path:

- `SCHOOL2022_54_6R_PINK_SALMON_IN_MILK` —
  Рыба, припущенная в молоке (горбуша) —
  80 g / exact 144.8 kcal;
- `SCHOOL2022_54_7R_POLLOCK_IN_MILK` —
  Рыба, припущенная в молоке (минтай) —
  80 g / exact 105.3 kcal.

New identity-only FoodIngredients:

- `PINK_SALMON_FILLET_RAW`;
- `POLLOCK_FILLET_RAW`.

Neither receives Nutrition or Composition authority.

Existing exact identities are reused for:

- `MILK_2_5`;
- `ONION_BULB_FRESH`;
- `SUNFLOWER_OIL`;
- `SALT_IODIZED`.

Prepared Nutrition remains:

`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

Only ENERGY_KCAL is AVAILABLE; all remaining frozen nutrient codes are UNKNOWN.

## Planner capacity after R2-B

Ordinary active exact-energy MAIN pool:

- `BOILED_CHICKEN_MAIN_PRODUCT`;
- `SCHOOL2022_54_29M_BEEF_MEATBALLS`;
- `SCHOOL2022_54_2M_BEEF_GOULASH`;
- `SCHOOL2022_54_6R_PINK_SALMON_IN_MILK`;
- `SCHOOL2022_54_7R_POLLOCK_IN_MILK`.

Result:

- active exact-energy MAIN count: 3 → 5;
- opportunity capacity: 9 → 15/week under unchanged repetition=3;
- persisted seven-DINNER production proof selects both preferred fish recipes;
- no RecipeVersion exceeds repetition 3;
- hard exclusion of `PINK_SALMON_FILLET_RAW` removes only the pink-salmon
  candidate while the week remains feasible and pollock remains available.

## Source / consumer boundary

Exact source-card / source-variant / source-process / selected-route /
energy-reconciliation hashes are pinned.

The source route includes a thawing alternative. One route is frozen for
deterministic provenance only.

Consumer RecipeSteps begin with already-thawed fillet. Thawing logistics,
paraconvection references and institutional serving-temperature requirements are
not promoted to consumer execution.

The older School2022 54-1р cod-cutlet follow-up remains deferred because its exact
retained source supports only generic wheat bread, while older R1-G evidence
proposed the narrower `WHEAT_BREAD_HIGH_GRADE_STALE` without exact cod-card
grade/stale evidence.

## Failure / replay semantics

Verified:

- fresh publication;
- exact zero-write replay;
- deliberate deactivation remains deactivated;
- tampered frozen contract fails closed;
- partial Recipe without prepared authority fails closed;
- conflicting fish FoodIngredient identity fails closed.

## Verification

Exact proof/runtime-freeze verification at `b7691b45...`:

- focused/affected R2-B suite — **128 passed**;
- Ruff check — SUCCESS;
- Ruff format --check — SUCCESS;
- scope/whitespace — SUCCESS;
- `AI_ENABLED=false`;
- migration head remains `0042_recipe_prepared_output_nutrition`;
- migration 0043 is absent.

The first R2-B run already had **128 passed** and failed only Ruff format. The
format-only correction did not change product/runtime semantics.

## Scope boundaries

Do not:

- add migration 0043 or schema changes;
- add another Nutrition authority kind;
- add Nutrition/Composition to fish identities;
- infer whole-fish→fillet equivalence;
- publish cod cutlet 54-1р;
- infer a narrower bread form;
- change Planner algorithm/scoring/roles/repetition;
- add allergen automation;
- start another corpus batch;
- start DC4 / Gate1-CLOSE;
- start PR9 Shopping;
- start Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI.

## Next step

Independent final review of PR #130.

After explicit review and merge, reassess the next R2/R3 corpus batch by maximum
marginal realistic weekly variety and corpus closure.

Do not start DC4, Gate1-CLOSE or PR9 automatically.
