# Current focus

Updated: 2026-10-03.

## Accepted state

PR #142 / R2-F runtime is merged into `main` at:

`da6d1e05fd44ecc2733e1a6f472eae3e54b60604`.

R2-F delivered:

- active `breakfast` classification: 7;
- active MAIN classification: 5;
- active `sandwich` classification: 1;
- hard exact `MILK_2_5` unaffected BREAKFAST-compatible pool:
  egg + cottage casserole + cheese sandwich;
- capacity = 3 × repetition 3 = 9/week;
- persisted seven-BREAKFAST exact-MILK exclusion week succeeds.

## Current bounded operation

**R3-A — School2022 10-recipe DATA-CORPUS-V1 / DC3 Contract Gate.**

Issue: `#143`.

Branch:

`docs/r3a-school2022-10-recipe-batch-gate`.

Accepted base:

`da6d1e05fd44ecc2733e1a6f472eae3e54b60604`.

Status:

`READY_FOR_FINAL_REVIEW`.

Canonical detail:

`docs/family-food/r3a-school2022-10-recipe-batch-gate.md`.

## Scope

Freeze one larger School2022 batch:

- 10 future RecipeVersions;
- 5 BREAKFAST + 5 MAIN;
- two new identity-only foods:
  `CHEESE_SEMI_HARD_UNSPECIFIED`, `PARSLEY_ROOT_FRESH`;
- reuse `PREPARED_OUTPUT_V1`;
- no schema/migration/Planner/new-Nutrition-authority change.

Do not start runtime, DC4/Gate1-CLOSE/PR9 or another R3 batch before this gate is
independently reviewed and merged.

## Gate verification

Evidence/content freeze:

`aa8d46aed4d7283d1fe95090996eff76cf396624`.

Verified:

- 6 evidence JSON files parse — PASS;
- exactly 10 unique RecipeVersions / 10 unique source IDs — PASS;
- role split 5 BREAKFAST / 5 MAIN — PASS;
- exact two new identity-only FoodIngredients — PASS;
- all 19 reused FoodIngredient codes have repository-local evidence — PASS;
- all 21 demanded ingredient identities are mapped — PASS;
- per-card independent household corroboration for all 10 candidates — PASS;
- exact ingredient quantities are positive, gross >= net and no duplicate food identity exists within a card — PASS;
- exact same-card output/ENERGY_KCAL frozen for all 10 — PASS;
- exact frozen nutrient partition = ENERGY_KCAL + 53 UNKNOWN — PASS;
- macro 4/9/4 QA arithmetic recomputes — PASS;
- known-deferred cards do not overlap selected scope — PASS;
- Docs #835 — SUCCESS;
- DC1 #692 — SUCCESS.

Do not start R3-A runtime before independent review and merge of PR #145.
