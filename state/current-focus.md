# Current focus

Updated: 2026-10-03.

## Accepted state

PR #140 / R2-F cheese-sandwich Contract Gate is merged into `main` at:

`2e4278cb06c2f683d1113434d04396c723409003`.

The merged gate authorizes exactly one runtime candidate:

`SAD28_SANDWICH_CHEESE_20_10` — Бутерброд с сыром —
30 g / exact prepared `ENERGY_KCAL=83`.

Current production state before this runtime:

- active `breakfast` classification: 7 RecipeVersions;
- active MAIN classification: 5 RecipeVersions;
- hard exact `MILK_2_5` exclusion leaves
  `HARD_BOILED_EGG` + `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`;
- unaffected BREAKFAST-compatible capacity = 6/week;
- seven-BREAKFAST remains bounded-infeasible under that exact exclusion.

## Current bounded operation

**R2-F runtime — publish cheese sandwich and close exact-MILK resilience.**

Issue: `#141`.

Branch:

`feat/r2f-cheese-sandwich-runtime`.

Accepted base:

`2e4278cb06c2f683d1113434d04396c723409003`.

Status:

`IMPLEMENTATION_ACTIVE`.

Canonical contract:

`docs/family-food/r2f-sandwich-resilience-gate.md`.

## Runtime scope

Create/reconcile exactly two identity-only FoodIngredients:

- `WHEAT_BREAD_PLAIN`;
- `CHEESE_UNSPECIFIED`.

No NutritionProfile or Composition authority is granted.

Publish exactly one immutable SOURCE_VERIFIED RecipeVersion:

- code: `SAD28_SANDWICH_CHEESE_20_10`;
- meal type: `sandwich`;
- bread: 20 g net;
- cheese: 11 g gross / 10 g net;
- output: 30 g;
- prepared `ENERGY_KCAL=83`;
- other 53 frozen nutrients UNKNOWN.

Retained source document:

`data/curation/r2f-sandwich-resilience/raw-cheese-card.txt`

SHA-256:

`77bc74917305adb0d4fee7a54910c9675068b1ec093a051f7c58bd34cc7dd27c`.

## Required product proof

After guarded activation:

- active `breakfast` classification remains 7;
- one active `sandwich` classification exists;
- BREAKFAST-compatible pool becomes 8;
- hard exact `MILK_2_5` unaffected pool becomes exactly three:
  egg + cottage casserole + cheese sandwich;
- unchanged repetition=3 gives capacity 9/week;
- a persisted seven-BREAKFAST hard-`MILK_2_5` week succeeds.

This is exact canonical `MILK_2_5` resilience only, not a dairy-allergy claim.

## Scope boundaries

Do not:

- publish the rejected butter sandwich;
- create `BUTTER_CREAM_UNSPECIFIED`;
- add migration 0043 or schema changes;
- change Planner mapping/scoring/repetition;
- add a new Nutrition authority;
- add Nutrition/Composition for the two new foods;
- start another R2/R3 batch;
- start DC4/Gate1-CLOSE/PR9;
- start Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI.

After this runtime PR is independently reviewed and merged, reassess DATA-CORPUS
readiness and move to larger R3 recipe batches (target ~10–12 recipes first)
rather than returning to one-recipe publication by default.
