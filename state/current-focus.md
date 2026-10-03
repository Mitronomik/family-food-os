# Current focus

Updated: 2026-10-04.

## Accepted state

PR #146 / R3-A School2022 ten-recipe MAIN Contract Gate is merged into `main` at:

`e152b357528bb000cf5cf16e792a0d31b983f117`.

PR #145 was superseded and closed without merge.

DATA-CORPUS-V1 / DC3 remains active.

## Current bounded operation

**R3-A runtime — publish School2022 ten-recipe MAIN batch.**

Issue: `#147`.

Branch:

`feat/r3a-school2022-main-batch-runtime`.

PR:

`#148`.

Accepted base:

`e152b357528bb000cf5cf16e792a0d31b983f117`.

Runtime freeze:

`6887b58e2331c1324a8269c4f8778a4ef3a0b143`.

Status:

`READY_FOR_FINAL_REVIEW`.

Canonical contract:

`docs/family-food/r3a-school2022-main-batch-gate.md`.

## Delivered runtime scope

Published and activated exactly the ten frozen MAIN RecipeVersions:

- `54-1р`, `54-2р`, `54-3р`;
- `54-10р`, `54-11р`;
- `54-4м`, `54-6м`, `54-7м`, `54-8м`, `54-11м`.

Created/reconciled exactly three identity-only FoodIngredients:

- `COD_FILLET_RAW`;
- `PARSLEY_ROOT_RAW`;
- `WHEAT_BREAD_STALE_UNSPECIFIED_GRADE`.

No NutritionProfile or Composition authority is granted to them.

Each new RecipeVersion uses exact prepared `ENERGY_KCAL` authority; the other
53 frozen nutrient codes remain UNKNOWN.

## Transaction result — option B

Publication:

1. each inactive RecipeVersion + prepared authority publishes atomically per recipe;
2. a failure may leave only an exact inactive subset;
3. rerun is zero-write for exact rows and converges missing rows;
4. publication never activates recipes.

Activation:

1. starts only after all ten exact publications reconcile;
2. all inactive -> all ten activate in one caller-owned UoW / one commit;
3. all active -> zero-write replay;
4. mixed active/inactive -> fail closed with zero writes;
5. injected activation failure rolls back all staged activation writes.

The runtime adds a transaction-neutral in-scope activation seam; the existing
single-recipe prepared activation behavior remains regression-safe.

## Source/process preservation

- runtime consumes the hash-pinned repository package; no live web/Library dependency;
- `54-8м` pre-soak liquid remains UNKNOWN;
- `54-11м` preserves the 5–10 minute weak boil and covered
  160 °C / 30–40 minute oven finish without an invented water split;
- excluded/deferred `54-5м/54-9р/54-12м/54-15м/54-18м` are not published.

## Runtime verification on exact freeze

`R3-A School2022 MAIN batch runtime #13` — SUCCESS:

- focused/affected suite: **95 passed**;
- Ruff check: PASS;
- Ruff format: PASS;
- scope/whitespace: PASS;
- exactly 3 identity-only foods / no Nutrition or Composition: PASS;
- exactly 10 MAIN RecipeVersions + prepared authority: PASS;
- per-recipe atomic inactive publication + resumable convergence: PASS;
- one-UoW batch activation + rollback: PASS;
- mixed-state fail-closed / all-active replay: PASS;
- `54-8м` / `54-11м` reviewed process semantics: PASS;
- migration head 0042 / no 0043: PASS;
- `AI_ENABLED=false`: PASS.

Same runtime freeze also has SUCCESS for:

- Docs #873;
- DC1 #730;
- R1-D #90;
- R1-F #85;
- R1-H #30;
- R1-C #130;
- R2 breakfast #114;
- R2-B #104;
- R2-C #92;
- R2-E #75;
- R2-F #47;
- Russian nutrition methodologies #473;
- Nutrient registry V2 #929, including broad backend/launcher regression;
- Partial nutrition profiles #685, including broad backend/launcher regression.

## Scope boundaries

Do not:

- merge PR #148 autonomously;
- split recipes into separate PRs;
- create a separate activation PR;
- add migration 0043 or schema changes;
- change Planner mapping/scoring/repetition;
- add a new Nutrition authority;
- start DC4/Gate1-CLOSE/PR9;
- start another recipe batch before independent review/merge and reassessment.

Only state/PR metadata may change after the runtime freeze unless a review finding
requires reopening runtime verification.
