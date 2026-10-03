# Current focus

Updated: 2026-10-03.

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

Accepted base:

`e152b357528bb000cf5cf16e792a0d31b983f117`.

Status:

`IN_PROGRESS`.

Canonical contract:

`docs/family-food/r3a-school2022-main-batch-gate.md`.

## Runtime scope

Publish exactly the ten frozen MAIN RecipeVersions from the merged gate:

- `54-1р`, `54-2р`, `54-3р`;
- `54-10р`, `54-11р`;
- `54-4м`, `54-6м`, `54-7м`, `54-8м`, `54-11м`.

Create/reconcile exactly three identity-only FoodIngredients:

- `COD_FILLET_RAW`;
- `PARSLEY_ROOT_RAW`;
- `WHEAT_BREAD_STALE_UNSPECIFIED_GRADE`.

No NutritionProfile or Composition authority is granted to these identities.

## Transaction contract — option B

One runtime PR owns all ten recipes.

Publication:

1. each inactive RecipeVersion + prepared authority publishes atomically per recipe;
2. a failure may leave an exact inactive subset;
3. rerun is zero-write for exact rows and converges missing rows;
4. publication never activates recipes.

Activation:

1. starts only after all ten exact publications reconcile;
2. all inactive -> activate all ten in one caller-owned UoW / one commit;
3. all active -> zero-write replay;
4. mixed active/inactive -> fail closed with zero writes;
5. any pre-commit failure rolls back the full activation UoW;
6. the existing commit-owning single-recipe activation guard must not be looped.

The runtime may extract/add the minimum transaction-neutral activation seam while
preserving existing single-recipe behavior.

## Source/process preservation

- runtime consumes the hash-pinned repository package; no live web/Library dependency;
- `54-8м` pre-soak liquid remains UNKNOWN; do not infer water placement;
- `54-11м` preserves the 5–10 minute weak boil and covered
  160 °C / 30–40 minute oven finish without an invented water split;
- excluded/deferred `54-5м/54-9р/54-12м/54-15м/54-18м` must not be published.

## Scope boundaries

Do not:

- split recipes into separate PRs;
- create a separate activation PR;
- publish the superseded PR #145 batch;
- add migration 0043 or schema changes;
- change Planner mapping/scoring/repetition;
- add a new Nutrition authority;
- add Nutrition/Composition to the three new identities;
- start DC4/Gate1-CLOSE/PR9;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.

## Verification target

Before review-ready prove:

- exactly 3 identity-only foods, no Nutrition/Composition;
- exactly 10 immutable SOURCE_VERIFIED MAIN RecipeVersions;
- ENERGY_KCAL only + 53 UNKNOWN for each;
- per-recipe publication atomicity and resumable convergence;
- full-batch one-UoW activation and rollback;
- mixed-state fail-closed / all-active zero-write replay;
- existing R2-F single-recipe activation regression;
- Planner deterministic admission under unchanged v0.4;
- migration head remains 0042;
- `AI_ENABLED=false`;
- dedicated R3-A workflow and required broad exact-head verification green.

Do not merge autonomously. After runtime review/merge, stop and reassess DC3
coverage before authorizing another batch or DC4.
