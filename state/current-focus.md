# Current focus

Updated: `2026-09-26`.

## Accepted state

PR92 / corrected Step 9 Contract Gate is merged into `main` at
`2c50782b17584a5708a946e497d6a628977420e9`.

Russian-data integration Steps 1–8 and the Step 9 Contract Gate are accepted.

## Current bounded state

**PR93 / Step 9 transaction/replay blocker correction is implemented; exact-head verification is pending.**

Branch:
`feat/step9-school2022-recipe-runtime`.

Previous runtime receipt:
`31751069adec7ada062c8b4b7fcb291f4cd89bed` — superseded by the transaction/replay correction.

Correction closes:
- required Step 8 FoodIngredient activity is rechecked inside strict Recipe Catalogue write UoW;
- exact replay fails closed if that dependency becomes inactive after external preflight;
- loader postconditions use the actual transactional reconcile result rather than stale external disposition;
- concurrent exact publication after a FRESH preflight resolves successfully as zero-write replay.

Canonical contract:
`docs/family-food/russian-recipe-version-publication-contract.md`.

## Delivered Step 9 runtime

```text
School2022 53-19з
→ inactive SCHOOL2022_53_19Z_BUTTER_PORTION Recipe
→ immutable SOURCE_VERIFIED RecipeVersion v1
→ exact 10 g BUTTER_PEASANT_72_5_UNSALTED
→ two material RecipeSteps
→ deterministic 17-value V2 validation
```

## Frozen runtime boundaries

- package/source lineage is hash-pinned before DB creation;
- institutional refrigerated holding + 14 °C remain source context only;
- home storage remains not granted;
- fresh Recipe is inactive;
- historical trusted seeds retain active default behavior;
- exact replay never mutates activation;
- strict Recipe history is rechecked inside the write UoW;
- same-provenance revision drift fails closed;
- inactive Step 9 Recipe is absent from Planner candidate enumeration;
- Step 8 ATOMIC v1 / V2 composition is required;
- WATER/carbohydrate remain unknown;
- legacy NutritionService/current-profile behavior is unchanged;
- source-declared School2022 nutrition remains reference-only;
- no schema/migration/source-corpus expansion;
- no Step 10 activation/Planner integration.

## Verification

The prior exact-head verification below remains historical evidence for the pre-correction runtime and is not a current runtime receipt.

On runtime head `31751069adec7ada062c8b4b7fcb291f4cd89bed`:

- Docs #358 — SUCCESS;
- DC1 #220 — SUCCESS;
- Russian nutrition methodologies #121 — SUCCESS;
- Nutrient Registry V2 #198 — SUCCESS;
- Partial nutrition profiles #150 — SUCCESS;
- Registry focused — 326 passed;
- Partial focused — 274 passed;
- backend shards — 1202 / 751 / 648 / 991 passed;
- launcher — 643 passed, 2 skipped;
- semantic review #5325378822 — READY TO MERGE;
- mergeable=true;
- 0 behind main;
- unresolved review threads=0;
- package checksum receipt independently re-hashed and matched;
- patch whitespace/conflict audit clean.

## Hard boundary

No Step 10 work is authorized by PR93.

## Stop boundary

Do not merge until the corrected runtime receives exact-head verification and final re-review.

Do not merge autonomously.
