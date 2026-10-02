# Current focus

Updated: 2026-10-02.

## Accepted state

PR #128 / R2-A is merged into `main` at:

`1e4a0e137dee87f2aaef7d885481fef17f6e324c`.

Accepted ordinary active exact-energy Planner pool before this batch:

- BREAKFAST: 3 RecipeVersions / capacity 9 opportunities per week;
- MAIN: 3 RecipeVersions / capacity 9 opportunities per week;
- `max_recipe_repetitions=3`;
- persisted seven-BREAKFAST and seven-DINNER paths are proven.

## Current bounded operation

**R2-B — Fish MAIN diversity batch.**

Issue: `#129`.

Branch: `feat/r2b-fish-main-diversity`.

Accepted base:

`1e4a0e137dee87f2aaef7d885481fef17f6e324c`.

Status:

`IMPLEMENTATION_ACTIVE`.

## Batch decision

Selected School2022 cards:

- `54-6р` — Рыба, припущенная в молоке (горбуша) —
  80 g / exact 144.8 kcal;
- `54-7р` — Рыба, припущенная в молоке (минтай) —
  80 g / exact 105.3 kcal.

New identity-only FoodIngredients:

- `PINK_SALMON_FILLET_RAW`;
- `POLLOCK_FILLET_RAW`.

Reuse:

- `MILK_2_5`;
- `ONION_BULB_FRESH`;
- `SUNFLOWER_OIL`;
- `SALT_IODIZED`.

No Nutrition/Composition is published for the new fish identities.

Prepared Nutrition remains:

`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

Only ENERGY_KCAL is AVAILABLE; all remaining frozen nutrients are UNKNOWN.

## Product effect target

Ordinary active exact-energy MAIN pool:

3 → 5 RecipeVersions.

Projected opportunity capacity under unchanged repetition=3:

9 → 15 MAIN opportunities/week.

The persisted proof must show a seven-DINNER week that selects both fish recipes
when both are preferred, with no RecipeVersion used more than 3 times.

A hard exclusion of one fish identity must remove only that candidate while the
week remains feasible through the remaining MAIN pool.

## Source / UX boundary

The retained source contains thawing alternatives, paraconvection references and
institutional serving-temperature requirements.

One source route is pinned for deterministic corpus closure, but consumer
RecipeSteps begin with already-thawed fillet. Thawing logistics, paraconvection
and institutional serving temperature remain provenance only.

The older R1-G cod-cutlet follow-up is not used in this batch because the exact cod
card supports only generic wheat bread while the old note proposed the narrower
`WHEAT_BREAD_HIGH_GRADE_STALE`. That unresolved form narrowing is not carried
into production.

## Scope boundaries

Do not:

- add migration 0043 or schema changes;
- add another Nutrition authority kind;
- publish Nutrition/Composition for fish identities;
- reuse whole-fish identities as exact fillet authority;
- publish cod cutlet 54-1р;
- infer a narrower bread form;
- change Planner algorithm/scoring/roles/repetition;
- add allergen automation;
- start DC4 / Gate1-CLOSE;
- start PR9 Shopping;
- start Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI.

## Verification target

R2-B must prove:

- exact hash-pinned source/publication contract;
- bounded household applicability for only the two named cards;
- fresh/replay/deactivation semantics;
- identity-only enforcement;
- tamper/partial/conflict fail-closed behavior;
- active exact-energy MAIN count = 5;
- persisted fish-diverse seven-DINNER week;
- hard fish exclusion with successful fallback;
- migration head remains 0042;
- `AI_ENABLED=false`.

## Next step

Run exact-head focused R2-B verification, fix task-local defects only, freeze the
verified runtime/evidence head, then hand the PR to independent final review.

After merge, reassess the next R2/R3 batch. Do not start DC4, Gate1-CLOSE or PR9
automatically.
