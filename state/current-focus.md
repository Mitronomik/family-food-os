# Current focus

Updated: `2026-09-24`.

## Accepted state

PR87 is merged into `main` at
`6ec1069d867388e5d1f4782ce6cdeed08c017694`.

Russian-data integration Steps 1–6 are accepted.

## Current bounded state

**Step 7 transformation applicability Contract Gate is review-ready in PR88.**

Verified contract head:
`7068b4d7af9d0b8817e933daeaa89a08f68feb26`.

Canonical gate:
`docs/family-food/transformation-applicability-contract.md`.

## Frozen Step 7 decisions

- preserve historical V1 `CompositionCalculator` and V1 retention writer/reader;
- preserve historical retention snapshot shape and hashes;
- no automatic V1→V2 retention carry-forward;
- introduce one dependent `TransformationApplicability` per immutable
  `FoodTransformation`;
- bind exact FoodIngredient, explicit season/source evidence scope and exact
  retention registry;
- reject late applicability after transformation use in composition history;
- add explicit registry-aware V2 retention read/write seams;
- add explicit applicability-aware V2 transformed publication/calculation paths;
- expected additive migration `0038_transformation_applicability`;
- initial runtime publishes zero production numeric loss/yield/retention factors
  from the supplied corpus.

## Contract Gate verification

On `7068b4d7af9d0b8817e933daeaa89a08f68feb26`:

- Docs #335 — SUCCESS;
- DC1 #197 — SUCCESS;
- scope is one canonical contract + three state files;
- 0 runtime/schema/data/API/UI changes;
- 0 behind main;
- unresolved review threads 0.

Final review:
`#5299903757` — READY TO MERGE CONTRACT GATE.

## Hard boundaries

No Step 7 runtime / migration 0038 yet.

No Step 8 food batch, Step 9 RecipeVersion publication, Step 10 Planner
integration, numeric source-loss publication, API/UI/Retail/AI/Auth/PostgreSQL.

Reserved `0033_recipe_template_catalogue` remains unconsumed.

## Stop boundary

PR88 may be merged after final proportional state-head verification.

After merge: stop. Step 7 runtime requires separate explicit authorization.
