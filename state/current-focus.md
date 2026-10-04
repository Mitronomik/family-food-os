# Current focus

Updated: 2026-10-04.

## Accepted state

PR #154 / R3-C post-R3B catalogue Contract Gate is MERGED into `main` at:

`3c5740b319e453715c5a58f5b65e6d216b7c4fdb`.

DATA-CORPUS-V1 / DC3 remains active.

## Current bounded operation

**R3-C runtime — frozen eight-recipe MAIN batch.**

Issue: `#155`.

PR: `#156`.

Branch:

`feat/r3c-school2022-main-batch-runtime`.

Accepted base:

`3c5740b319e453715c5a58f5b65e6d216b7c4fdb`.

Runtime freeze:

`c9e985eaad876fbc66519488d995d6e65975308a`.

Status:

`READY_FOR_FINAL_REVIEW`.

Canonical contract:

`docs/family-food/r3c-post-r3b-catalogue-gate.md`.

## Delivered runtime scope

Exactly eight frozen MAIN RecipeVersions are published/activated:

- `SCHOOL2022_54_21M_BOILED_CHICKEN`;
- `SCHOOL2022_54_3M_LAZY_CABBAGE_ROLLS`;
- `SCHOOL2022_54_26M_POTATO_BEEF_CASSEROLE`;
- `SCHOOL2022_54_1M_BOILED_BEEF_STROGANOFF`;
- `SCHOOL2022_54_30M_BEEF_RICE_QUENELLES`;
- `SCHOOL2022_54_20M_BOILED_BEEF`;
- `SCHOOL2022_54_15R_SALMON_IN_MILK`;
- `SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES`.

Exactly one new identity-only FoodIngredient is reconciled:

- `ATLANTIC_SALMON_FILLET_RAW`.

It has no NutritionProfile, NutrientVector or Composition authority.

Every RecipeVersion uses exact prepared `ENERGY_KCAL`; the other 53 frozen
nutrient codes remain UNKNOWN.

## Transaction result — reused option B

Publication:

1. per-recipe atomic inactive RecipeVersion + prepared authority;
2. exact replay is zero-write;
3. exact inactive subset is resumable;
4. conflicting/partial persisted truth fails closed;
5. publication never activates.

Activation:

1. begins only after all eight exact publications reconcile;
2. all-inactive batch activates in one caller-owned UoW / one commit;
3. all-active replay is zero-write;
4. mixed active/inactive fails closed;
5. injected activation failure rolls back all staged writes.

No new activation architecture was introduced.

## Product / source preservation

- runtime consumes only the hash-pinned merged R3-C package;
- no live web/Library runtime dependency;
- consumer Recipe Steps remain Russian-only;
- `54-30м` publishes only the selected steam branch 15–20 minutes;
- its water-poaching alternative remains provenance-only;
- no unsupported per-step fat/water quantity is invented;
- prior R3-B deliberate deactivation is not silently repaired.

## Exclusion / catalogue result

After R3-C:

- exact-energy catalogue: 41;
- breakfast: 17;
- MAIN: 23;
- sandwich: 1;
- hard `MILK_2_5` breakfast proof remains 3 unaffected / capacity 9 / seven-breakfast success;
- exact `BEEF_CATEGORY_1_RAW`: 12 of 23 MAIN, 11 unaffected / capacity 33;
- gap to DATA-CORPUS-V1 lower baseline 50: 9;
- DC4 remains blocked.

## Runtime-freeze verification

Exact runtime freeze `c9e985eaad876fbc66519488d995d6e65975308a`:

- R3-C runtime #37202224299 — SUCCESS, 22/22 focused tests;
- R3-C gate #37202224233 — SUCCESS;
- Docs #37202224257 — SUCCESS;
- DC1 #37202224207 — SUCCESS;
- R1-C #37202224245 — SUCCESS;
- R2 #37202224250 — SUCCESS;
- R2-B #37202224294 — SUCCESS;
- R2-C #37202224239 — SUCCESS;
- R2-E #37202224235 — SUCCESS;
- R2-F #37202224202 — SUCCESS;
- R3-A #37202224232 — SUCCESS;
- R3-B #37202224209 — SUCCESS;
- Russian methodologies #37202224243 — SUCCESS;
- Nutrient registry V2 #37202224305 — SUCCESS including full backend/launcher regression;
- Partial nutrition profiles #37202224282 — SUCCESS including full backend/launcher regression;
- Ruff check/format and scope/whitespace — PASS;
- migration head remains `0042_recipe_prepared_output_nutrition`;
- `AI_ENABLED=false`.

## Scope boundaries

Do not:

- merge PR #156 autonomously;
- add migration 0043 or schema changes;
- change Planner mapping/scoring/repetition;
- add a new Nutrition authority;
- publish deferred/rejected candidates;
- start DC4 / Gate1-CLOSE / PR9;
- start Shopping / Prep / PDF / PWA / Retail / Auth / PostgreSQL / AI.

Only state/PR metadata may change after the runtime freeze unless independent
review explicitly reopens runtime behavior. After merge, reassess DC3 catalogue
coverage/readiness before authorizing another batch or DC4.
