# Current focus

Updated: 2026-10-03.

## Accepted state

PR #138 / R2-E runtime is merged into `main` at:

`561c13aad6ce978de399dfd807071232af06b71c`.

Current exact-energy production state:

- active `breakfast` classification: 7 RecipeVersions;
- active MAIN classification: 5 RecipeVersions;
- `max_recipe_repetitions=3`;
- hard exact `MILK_2_5` exclusion leaves `HARD_BOILED_EGG` and
  `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`;
- unaffected BREAKFAST-compatible capacity = 6/week;
- seven-BREAKFAST remains bounded-infeasible under that exact exclusion.

## Current bounded operation

**R2-F — two-SANDWICH resilience-closure Contract Gate.**

Issue: `#139`.

Branch: `docs/r2f-sandwich-resilience-gate`.

Accepted base:

`561c13aad6ce978de399dfd807071232af06b71c`.

Status:

`READY_FOR_FINAL_REVIEW`.

## Frozen candidate batch

Future runtime batch is exactly:

- `SAD28_SANDWICH_BUTTER_25_5` — 30 g / 66.3 kcal;
- `SAD28_SANDWICH_CHEESE_20_10` — 30 g / 83 kcal.

Both use `meal_type_code=sandwich`.

Create identity-only:

- `WHEAT_BREAD_PLAIN`;
- `BUTTER_CREAM_UNSPECIFIED`;
- `CHEESE_UNSPECIFIED`.

No Nutrition/Composition is granted to those identities.

Bounded source authority:
`BOUNDED_INSTITUTION_PUBLISHED_TECH_CARD_REVIEW_V1`.

## Product boundary

Projected after later runtime:

- active `breakfast` classification remains 7;
- active `sandwich` classification +2;
- BREAKFAST-compatible pool becomes 9;
- hard exact `MILK_2_5` unaffected pool becomes 4 / capacity 12;
- LUNCH and SNACK each gain 2 compatible candidates.

This is exact `MILK_2_5` resilience only, not a dairy-allergy claim.

## Scope boundaries

Do not:

- publish/activate runtime data in this gate;
- add migration 0043 or schema changes;
- change Planner algorithm/mapping/repetition;
- add a new Nutrition authority;
- grant Nutrition/Composition to new identities;
- add the deferred povidlo card;
- bulk-import the website/PDF;
- start DC4/Gate1-CLOSE/PR9;
- start API/UI/Prep/Retail/Auth/PostgreSQL/AI.

## Next step

Evidence/content freeze:

`1aaada5c66c6781e7b8c5ef19a5ccf3a3d508822`.

Verification:

- all 8 evidence JSON files parse — PASS;
- reviewed derivative SHA-256 recomputation — PASS;
- both exact card SHA-256 recomputations — PASS;
- source-policy scope = exactly 2 cards — PASS;
- public-source verification receipt = PASS;
- exact macro QA = 66.30 / 82.75 kcal — PASS;
- exactly 3 identity-only foods; no Nutrition/Composition — PASS;
- nutrient partition = ENERGY_KCAL AVAILABLE + 53 UNKNOWN — PASS;
- projected hard-`MILK_2_5` capacity = 4 × 3 = 12 — PASS;
- Docs verification #806 — SUCCESS;
- DC1 corpus verification #663 — SUCCESS;
- changed scope remains docs/data/state only;
- runtime/schema/migration diff — none.

PR #140 is ready for independent final review. Do not start runtime publication
before review and merge.
