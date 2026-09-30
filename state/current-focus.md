# Current focus

Updated: 2026-09-30.

## Accepted state

PR117 / R1-F cooked prepared-output Nutrition contract gate is merged into `main` at:

`e138d615802f7928946e419156f8c6905f04075b`.

The merged gate authorizes one bounded runtime/data implementation using:

- `PREPARED_OUTPUT_V1`;
- `RECIPE_PREPARED_OUTPUT_NUTRITION_V1`;
- migration `0042_recipe_prepared_output_nutrition`;
- source-neutral, portion-neutral production Recipe identities;
- exact source receipts already pinned by PR117;
- explicit activation only after exact-energy + Planner admission proof.

## Current bounded operation

**R1-F runtime — prepared-output Nutrition pilot and Planner activation.**

Issue:

`#118`.

PR:

`#119`.

Branch:

`feat/r1f-prepared-output-runtime`.

Accepted base:

`e138d615802f7928946e419156f8c6905f04075b`.

## Implemented on current branch

Runtime now includes:

- migration `0042_recipe_prepared_output_nutrition`;
- immutable `recipe_prepared_nutrition_authorities`;
- immutable sparse `recipe_prepared_nutrient_values`;
- Recipe Nutrition authority kind `PREPARED_OUTPUT_V1`;
- exact-replay/fail-closed prepared publication;
- prepared-vs-Composition double-authority rejection;
- identity-only FoodIngredient publication for
  `CHICKEN_CATEGORY_2_RAW / Курица II категории, сырая`;
- explicit Recipe activation command;
- R1-F publication/orchestration seed;
- focused end-to-end runtime/migration/Planner tests.

Pilot production Recipes:

### Breakfast

`HARD_BOILED_EGG / Яйцо куриное вкрутую`

- source: MR 2.4.0162-19 Appendix 5 card 4.1;
- RecipeVersion source output: 40 g;
- prepared ENERGY_KCAL: 63;
- canonical EGG ingredient retained;
- output mass is not Recipe identity.

### Main

`BOILED_CHICKEN_MAIN_PRODUCT / Курица отварная без гарнира`

- source: 1988 recipe 303 Variant III;
- input: `CHICKEN_CATEGORY_2_RAW` 107 g;
- RecipeVersion source output: 75 g;
- prepared ENERGY_KCAL: 167.7;
- no inferred onion row;
- no 1986 697/824 144 kcal reuse.

Historical:

`USSR82_697_BOILED_CHICKEN / Курица отварная`

remains immutable/inactive.

## Nutrition authority boundary

R1-F runtime deliberately publishes only exact source ENERGY_KCAL for both pilot
RecipeVersions.

Protein/fat/carbohydrate source values are not promoted automatically. They remain
UNKNOWN until exact frozen-registry semantic mapping is separately proven.

Unknown is never converted to zero.

## Replay / activation behavior

Fresh publication:

`inactive Recipe + SOURCE_VERIFIED RecipeVersion + prepared authority`

is one caller-owned transaction and verifies exact prepared energy before commit.

Activation is a separate application command.

Publication replay:

- exact authority replay = zero-write;
- active Recipe may replay immutable authority;
- a deliberately deactivated Recipe is not silently reactivated by rerunning the
  publication seed;
- partial persisted state fails closed.

## Verification status

Current exact head:

`9283a647e24c0c8c03b72005eb8255a07590a1b1`.

Focused `R1-F runtime` workflow:

- focused R1-F tests — SUCCESS;
- Recipe Nutrition V2 affected tests — SUCCESS;
- migration/lineage/rebuild/coexistence affected tests — SUCCESS;
- Planner application boundary affected tests — SUCCESS;
- Ruff — SUCCESS.

Broad exact-head workflows are still running and must be green before final
review readiness.

## Hard boundaries

Do not:

- merge PR119 without final review/authorization;
- infer raw→cooked Nutrition;
- add retention/transformation runtime;
- publish source carbohydrate as a canonical code without reviewed method mapping;
- mutate historical USSR82-697;
- bulk-activate recipes;
- add 467/492/1081 in PR119;
- change Planner algorithm/scoring/roles/repetition limits;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI;
- start R2/R3 before successful R1-C.

## Next step

Finish broad exact-head verification, resolve any concrete failures, update the PR
receipt, then stop for final review of PR119.

After PR119 merges, the next bounded operation is expansion of the proven authority
path toward enough breakfast/main capacity for R1-C; do not start automatically.
