# Current focus

Updated: `2026-09-21`.

## Accepted state

PR76 is merged at `011f4b74abd29f7b5ec77ab0f15998f781f43c43`.

The user-approved Russian-data integration sequence remains:

`partial profile storage → registry/adapters → transactional publication → first
Russian food batch → Russian reference table → persisted methodology selection →
transformation applicability → recipe-dependency food batch → executable Russian
recipes → Planner integration`.

Step 1 is accepted. Current bounded work is **step 2: nutrient registry V2 and
Russian method/reference adapters**.

## Current authorized boundary

Step 2:

- preserves immutable `PR6_NUTRIENT_VECTOR_A_V1` definitions, values, seals and
  existing ATOMIC/Composition semantics;
- introduces `RU_NUTRIENT_REGISTRY_V2` as a complete reviewed definition
  snapshot;
- changes persisted nutrient-definition identity to
  `(registry_version, nutrient_code)` through
  `0035_versioned_nutrient_registry`;
- migrates existing V1 value rows by copying the registry version already pinned
  by their seal; V1 amounts/provenance/seals are unchanged;
- makes V2 `CARBOHYDRATE_AVAILABLE` definition independent from the observation
  method and requires an explicit supported method in V2 value provenance;
- adds distinct V2 concepts `VITAMIN_A_RE`, `NIACIN_EQUIVALENT` and
  `VITAMIN_E_TOCOPHEROL_EQUIVALENT`;
- authorizes no implicit RE↔RAE, NE↔niacin, tocopherol-equivalent↔alpha-tocopherol
  or unspecified-folate conversion;
- keeps legacy Composition nutrient-definition reads explicitly pinned to V1;
- exposes a new version-aware registry read port for later publication/target
  consumers.

Reserved `0033_recipe_template_catalogue` remains unused. Forward migration
history is `... → 0032 → 0034 → 0035`; a future reserved 0033 implementation
must append after already accepted later migrations.

## Acceptance

Review-ready requires:

- exact V1 snapshot/definition/value/seal preservation through 0035;
- simultaneous storage/read of the same stable code under V1 and V2;
- V2 available-carbohydrate methods accepted only from explicit provenance;
- incompatible vitamin/carbohydrate definitions never substitute by equal unit;
- migration failure rolls back schema/data/marker;
- existing V1 vector/Composition/Nutrition behavior remains green;
- full backend and launcher regression with `AI_ENABLED=false`.

## Stop boundary

After review/merge, stop before step 3: transactional publication of a reviewed
`FoodIngredient → profile → V2 NutrientVector → ATOMIC` bundle.

Do not publish Russian food profiles/values, target tables, methodology selection,
Planner/API/UI defaults, recipes, DC4/Gate1 or Shopping automatically.
