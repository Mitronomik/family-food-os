# Current focus

Updated: 2026-10-04.

## Accepted state

PR #154 / R3-C post-R3B catalogue Contract Gate is MERGED into `main` at:

`3c5740b319e453715c5a58f5b65e6d216b7c4fdb`.

DATA-CORPUS-V1 / DC3 remains active.

## Current bounded operation

**R3-C runtime — publish frozen eight-recipe MAIN batch.**

Issue: `#155`.

Branch:

`feat/r3c-school2022-main-batch-runtime`.

Accepted base:

`3c5740b319e453715c5a58f5b65e6d216b7c4fdb`.

Status:

`IMPLEMENTATION_ACTIVE`.

Canonical contract:

`docs/family-food/r3c-post-r3b-catalogue-gate.md`.

## Authorized runtime scope

Publish/activate exactly eight frozen MAIN RecipeVersions:

- `SCHOOL2022_54_21M_BOILED_CHICKEN`;
- `SCHOOL2022_54_3M_LAZY_CABBAGE_ROLLS`;
- `SCHOOL2022_54_26M_POTATO_BEEF_CASSEROLE`;
- `SCHOOL2022_54_1M_BOILED_BEEF_STROGANOFF`;
- `SCHOOL2022_54_30M_BEEF_RICE_QUENELLES`;
- `SCHOOL2022_54_20M_BOILED_BEEF`;
- `SCHOOL2022_54_15R_SALMON_IN_MILK`;
- `SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES`.

Exactly one new identity-only FoodIngredient is authorized:

- `ATLANTIC_SALMON_FILLET_RAW`.

No NutritionProfile, NutrientVector or Composition authority is allowed.

Reuse R3-A/R3-B option B:

- per-recipe atomic inactive publication;
- resumable exact inactive subset;
- zero-write exact replay;
- one-UoW full-batch activation;
- mixed-state fail closed;
- activation rollback.

## Expected result

After successful runtime activation:

- exact-energy catalogue: 33 -> 41;
- MAIN: 15 -> 23;
- breakfast: 17;
- sandwich: 1;
- gap to DATA-CORPUS-V1 lower baseline 50: 9;
- DC4 remains blocked.

## Scope boundaries

Do not:

- add migration 0043 or schema changes;
- change Planner mapping/scoring/repetition;
- add a new Nutrition authority;
- publish deferred/rejected candidates;
- start DC4 / Gate1-CLOSE / PR9;
- start Shopping / Prep / PDF / PWA / Retail / Auth / PostgreSQL / AI.

After this runtime PR is review-ready, stop for independent review. After merge,
reassess DC3 catalogue readiness before authorizing another batch or DC4.
