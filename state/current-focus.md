# Current focus

Updated: `2026-09-24`.

## Accepted state

PR88 / Step 7 Transformation Applicability Contract Gate is merged into `main`
at `71e4cfc63908440a54631e68b7507e94311980d2`.

Russian-data integration Steps 1–6 and the Step 7 Contract Gate are accepted.

## Current bounded state

**Step 7 transformation applicability runtime is review-ready in PR89.**

Branch:
`feat/step7-transformation-applicability-runtime`.

Verified runtime/test/workflow head:
`e481b6cda42afa2f33e5239262dae3f3c6780797`.

Canonical contract:
`docs/family-food/transformation-applicability-contract.md`.

## Delivered Step 7 runtime

- dependent immutable `TransformationApplicability` for exact
  `FoodTransformation`;
- additive migration `0038_transformation_applicability`;
- exact FoodIngredient / season / evidence-scope applicability;
- explicit registry-aware V2 retention read/write seams;
- explicit applicability-aware V2 Composition publication path;
- separate `ApplicabilityAwareCompositionCalculator`;
- legacy V1 `CompositionCalculator`, retention snapshots/digests and
  legacy read/write/publication paths preserved;
- no automatic V1→V2 retention carry-forward;
- no production numeric Book2002 / School2022 / legacy loss-factor publication.

## Verification on runtime head

- Russian nutrition methodologies #113 — SUCCESS;
- Nutrient Registry V2 #169 focused — **280 passed**;
- Partial nutrition profiles #130 — **SUCCESS**:
  - focused **228 passed**;
  - backend shards **1252 / 768 / 582 / 962 passed**;
  - launcher **643 passed, 2 skipped**;
- Nutrient Registry V2 launcher — **643 passed, 2 skipped**;
- `AI_ENABLED=false`;
- GitHub patch scope/whitespace/conflict audit — clean.

The container could not run a literal local `git diff --check` because direct
GitHub DNS resolution was unavailable; no such shell check is claimed.

## Hard boundaries

No Step 8 food batch, Step 9 RecipeVersion publication, Step 10 Planner
integration, production numeric transformation/loss-factor publication,
API/UI/Retail/AI/Auth/PostgreSQL.

Reserved `0033_recipe_template_catalogue` remains unconsumed.

## Stop boundary

PR89 is ready for final review. Do not merge autonomously.

After PR89 merge: stop. Step 8 requires separate explicit authorization.
