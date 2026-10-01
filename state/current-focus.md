# Current focus

Updated: 2026-10-01.

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
- guarded prepared-Recipe activation boundary that exact-replays reviewed authority,
  requires exact-energy readiness and only the reversible INACTIVE Planner blocker;
- canonical prepared 54-code projection where absent nutrients are explicit UNKNOWN;
- R1-F publication/orchestration seed;
- focused end-to-end runtime/migration/Planner/adversarial tests.

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

Review blockers found after the original runtime freeze were fixed without a new
migration or Planner algorithm change.

Current runtime head:

`ac647a9fd0546876db743faf545d64ef2622c595`.

Proven on this runtime head:

- R1-F runtime — SUCCESS; 122 focused/affected tests passed;
- Ruff check — SUCCESS;
- Ruff format check — SUCCESS;
- Docs verification — SUCCESS;
- DC1 corpus verification — SUCCESS;
- R1-D Planner admission — SUCCESS;
- Russian nutrition methodologies — SUCCESS;
- Partial nutrition profiles — SUCCESS, including all backend regression shards
  and launcher regression;
- Nutrient registry V2 — SUCCESS, including focused, all backend regression shards
  and full launcher regression;
- Partial nutrition profiles — SUCCESS, including focused, all backend regression
  shards and full launcher regression.

Review corrections now prove:

- prepared canonical Nutrition always exposes the frozen 54-code vector;
- only reviewed values are AVAILABLE; absent codes are UNKNOWN, never synthetic zero;
- an explicit numeric zero remains AVAILABLE(0), distinct from UNKNOWN;
- PARTIAL canonical Nutrition with exact positive ENERGY_KCAL remains ordinary
  Planner-eligible;
- reviewed prepared specs explicitly partition all 54 codes into AVAILABLE vs
  UNKNOWN; an unreviewed nutrient cannot silently move into AVAILABLE;
- the Recipe catalogue exposes no public unchecked activation command; prepared
  activation passes only through the guarded authority/admission boundary;
- wrong output/source/hash/rights, soft/medium egg, category-I chicken,
  697/824 + 144 kcal and missing/zero/negative ENERGY_KCAL are explicitly rejected.

Runtime changes after the old `a20d13...` receipt make that older receipt
historical only. The runtime acceptance receipt is now complete at `ac647a9f...`.

PR119 is **READY FOR FINAL REVIEW**. Do not merge without explicit authorization.
Later state-only commits do not invalidate the byte-identical runtime receipt and
do not require another full broad regression.

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

Final review PR119.

After PR119 is explicitly reviewed and merged, the next bounded operation is
catalogue-capacity expansion using the proven authority seam, including
USSR82-467 / 492 / 1081 where exact source authority permits plus enough MAIN
capacity for R1-C.

Do not start that follow-up automatically.
