# Current focus

Updated: `2026-09-26`.

## Accepted state

PR92 / corrected Step 9 Contract Gate is merged into `main` at
`2c50782b17584a5708a946e497d6a628977420e9`.

Russian-data integration Steps 1–8 and the Step 9 Contract Gate are accepted.

## Current bounded state

**PR93 / Step 9 transaction/replay blocker correction is verified and ready for final re-review/merge authorization.**

Branch:
`feat/step9-school2022-recipe-runtime`.

Verified corrected runtime head:
`99f3d2b9ae592e9370a0f432316828da7a3b6cfb`.

The earlier runtime receipt
`31751069adec7ada062c8b4b7fcb291f4cd89bed` is superseded by this corrected runtime.

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

On corrected runtime head `99f3d2b9ae592e9370a0f432316828da7a3b6cfb`:

- Docs #360 — SUCCESS;
- DC1 #222 — SUCCESS;
- Russian nutrition methodologies #123 — SUCCESS;
- Nutrient Registry V2 #201 — SUCCESS;
- Partial nutrition profiles #152 — SUCCESS;
- Registry focused — 328 passed;
- Partial focused — 276 passed;
- backend shards — 1202 / 751 / 650 / 991 passed;
- launcher — 643 passed, 2 skipped;
- `AI_ENABLED=false`;
- two new adversarial transaction/replay tests are included in focused verification.

The corrected runtime bytes are frozen at this head. Later state-only receipt commits
do not invalidate this runtime verification.

## Hard boundary

No Step 10 work is authorized by PR93.

## Stop boundary

PR93 is ready for final re-review and explicit merge authorization.

Do not merge autonomously.
