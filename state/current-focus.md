# Current focus

Updated: `2026-09-25`.

## Accepted state

PR90 / corrected Step 8 Contract Gate is merged into `main` at
`76ca8f8ffba589576af4e0fad4d7a4817a84089f`.

Russian-data integration Steps 1–7 and the Step 8 Contract Gate are accepted.

## Current bounded state

**Step 8 runtime/data publication is review-ready in PR91.**

Branch:
`feat/step8-recipe-dependency-butter-runtime`.

Verified runtime/test/workflow head:
`068847f4a3b886e6b8133558f2d4820a6a01474e`.

Canonical contract:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

## Delivered Step 8 runtime/data

- new exact `BUTTER_PEASANT_72_5_UNSALTED`;
- licensed FIC RU-NUT-DB code 1417 / DB/533;
- exact raw record SHA-256
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- `salt_ad=0.0` retained source-only as no-added-salt form evidence;
- sodium does not infer salinity;
- non-zero/null/missing salt evidence fails closed;
- all 26 FIC source fields retained;
- `water=null` remains source-not-reported;
- sealed V2 vector contains exactly 17 values and no WATER value;
- source profile is non-current;
- ATOMIC v1 / INPUT;
- generic `BUTTER_UNSALTED` / USDA FDC 173430 remains unchanged/current;
- zero YieldModel/retention/FoodTransformation/TransformationApplicability rows;
- zero RecipeVersion rows added;
- no migration/schema change; head remains 0038 and 0033 remains reserved.

The implementation reuses the accepted Step 3/4 publication service and project
UoW; no shared publication-service semantics changed.

## Exact runtime verification

On `068847f4a3b886e6b8133558f2d4820a6a01474e`:

- Nutrient Registry V2 #180 — SUCCESS:
  - focused: **310 passed**;
  - backend shards: **1205 / 798 / 614 / 959 passed**;
  - launcher: **643 passed, 2 skipped**;
- Partial nutrition profiles #139 — SUCCESS:
  - focused: **258 passed**;
  - backend shards: **1205 / 798 / 614 / 959 passed**;
  - launcher: **643 passed, 2 skipped**;
- Russian nutrition methodologies #116 — SUCCESS;
- Docs #347 — SUCCESS;
- DC1 #209 — SUCCESS;
- `AI_ENABLED=false`;
- PR patch whitespace/conflict audit — clean.

Focused workflows explicitly execute both Step 4 and Step 8 production
publication suites.

## Hard boundaries

No Step 9 RecipeVersion, Step 10 Planner integration, additional FIC foods,
production transformation factors, API/UI/Retail/AI/Auth/PostgreSQL.

## Stop boundary

PR91 is ready for final review after state-only receipt verification.

Do not merge autonomously. After merge, stop; Step 9 requires separate explicit
authorization.
