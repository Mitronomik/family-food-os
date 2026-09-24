# Current focus

Updated: `2026-09-24`.

## Accepted state

PR87 is merged into `main` at
`6ec1069d867388e5d1f4782ce6cdeed08c017694`.

Russian-data integration Steps 1–6 are accepted.

Current bounded work is **Step 7 — transformation applicability Implementation
Contract Gate only**.

Branch:
`docs/step7-transformation-applicability-contract`.

Canonical gate:
`docs/family-food/transformation-applicability-contract.md`.

## Step 7 preflight facts

- legacy `CompositionCalculator` and
  `SqlAlchemyFoodCompositionRepository.nutrient_definition(code)` remain
  intentionally V1-pinned;
- migration 0035 already stores `registry_version` on
  `food_retention_values` and pins all historical factors to V1;
- historical `NutrientRetentionProfile` / `RetentionValue` snapshot digests
  do not include registry identity and must not be rewritten;
- V2 is not universally definition-equivalent to V1:
  `CARBOHYDRATE_AVAILABLE` was deliberately redefined and three new equivalent
  definitions prohibit implicit conversion;
- canonical Russian methodology requires transformation applicability to bind
  exact food, season, operation and source and forbids double cold/heat loss;
- reviewed corpus transformation/loss packages are evidence only: Book2002 still
  requires separate production-rights review, School2022 assumptions are
  quarantined/unvalidated, and legacy recipe retention rows are explicitly not
  integration-ready.

## Frozen Contract Gate direction

The gate proposes one immutable dependent record per transformation:

`TransformationApplicability`.

It binds:

- exact `FoodTransformation`;
- exact `FoodIngredient`;
- exact retention registry when retention exists;
- explicit season scope/reference;
- exact reviewed evidence-scope identity;
- provenance + snapshot digest.

Applicability changes require a new transformation identity/version.

Late applicability after a transformation is already referenced by an immutable
composition step is forbidden.

Existing `CompositionCalculator` stays V1-pinned. Step 7 runtime, if separately
authorized after this gate merges, adds an explicit applicability-aware V2 path.

Expected next migration:
`0038_transformation_applicability`.

The initial runtime publishes zero production numeric transformation/yield/
retention factors from the supplied corpus.

## Hard boundaries

No Step 7 runtime/migration yet.

No:

- Step 8 recipe-dependency food publication;
- Step 9 RecipeVersion publication;
- Step 10 Planner integration;
- Book2002/School2022/legacy retention-factor promotion;
- automatic V1→V2 factor carry-forward;
- API/UI;
- Retail/AI/Auth/PostgreSQL.

Reserved `0033_recipe_template_catalogue` remains unconsumed.

## Stop boundary

Deliver/review the Step 7 Contract Gate. After gate merge, stop.
Step 7 runtime requires separate explicit authorization.
