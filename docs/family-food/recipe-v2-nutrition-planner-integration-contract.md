# Step 10 — Recipe V2 Nutrition / Planner Integration Contract

**Status:** Implementation Contract Gate / docs-only  
**Decision date:** 2026-09-26  
**Accepted base:** d0a1a217d3e23b0b930f14de37405a7ca7ba3d16 — merged PR #93 / accepted Step 9 runtime  
**Bounded step:** Russian-data integration Step 10 — reusable composition-backed RecipeVersion nutrition consumption and Planner integration  
**Runtime/schema implementation authorized by this document:** no — review and merge this gate first

## 1. Goal

Step 10 closes the architectural gap between accepted V2 Composition truth and ordinary RecipeVersion Nutrition / Planner consumption.

The target is:

~~~text
immutable RecipeVersion
→ immutable RecipeIngredient
→ explicit exact FoodCompositionVersion binding
→ RU_NUTRIENT_REGISTRY_V2 calculation
→ canonical RecipeVersion nutrient result
→ Planner-safe energy projection
~~~

The target is not to turn the Step 9 butter portion into a standalone meal.

The production Step 9 Recipe remains inactive in Step 10.

## 2. FACT — accepted base

PR #93 is merged into main at d0a1a217d3e23b0b930f14de37405a7ca7ba3d16.

Accepted production truth includes:

- FoodIngredient BUTTER_PEASANT_72_5_UNSALTED;
- non-current FIC DB/533 FoodNutritionProfile;
- sealed 17-value RU_NUTRIENT_REGISTRY_V2 vector;
- exact FoodCompositionVersion v1 / ATOMIC / INPUT;
- inactive Recipe SCHOOL2022_53_19Z_BUTTER_PORTION;
- immutable SOURCE_VERIFIED RecipeVersion v1;
- one required 10 g RecipeIngredient;
- two material RecipeSteps;
- institutional holding and 14 °C quarantined as source context;
- WATER unknown;
- canonical total carbohydrate unknown.

Migration head is 0038_transformation_applicability.

0033_recipe_template_catalogue remains reserved and unconsumed.

## 3. FACT — current general Nutrition cannot consume Step 9 authority safely

Current NutritionService.recipe_version() resolves RecipeIngredient nutrition through the legacy current-profile / B1 assessment path.

The Step 8 butter profile is intentionally non-current.

Therefore Step 10 must not:

- mark the Step 8 profile current;
- replace or retire the accepted generic current butter profile;
- invent a B1 assessment;
- reinterpret legacy current-profile semantics;
- fill missing nutrients from School2022 declared recipe totals.

## 4. FACT — current Planner composition

Current authoritative Planner composition performs:

~~~text
FoodRecipeCatalogueService.list_active()
→ get_current_verified()
→ NutritionService.recipe_version()
→ PlannerCandidate
~~~

Recipe activation is therefore a material Planner input change.

The pure Planner also rejects candidates when recipe classification is incompatible with MealRole or when its current bounded Nutrition contract is unavailable.

## 5. FACT — Recipe classification is not MealRole

Canonical architecture freezes:

~~~text
RecipeVersion.meal_type_code != MealRole
~~~

Current compatibility intentionally treats MealTypeCode.OTHER as compatible with no automatic MealRole.

The Step 9 Recipe has meal_type_code = other.

No accepted evidence establishes that a 10 g butter portion is a standalone breakfast, lunch, dinner or snack.

## 6. FACT — RecipeIngredient does not pin Composition

The persisted RecipeIngredient stores FoodIngredient identity, exact source quantity/unit and source/normalization metadata.

It does not persist which FoodCompositionVersion is authoritative for that immutable recipe row.

Composition supports multiple immutable versions per FoodIngredient.

Selecting latest, current, or version 1 by convention in general Nutrition would make historical RecipeVersion calculation depend on mutable application policy rather than persisted authority.

That is not acceptable for deterministic replay.

## 7. DECISION — Step 10 does not activate the Step 9 Recipe

The Step 9 handoff allowed Step 10 to consider activation and V2 Planner integration.

Preflight proves those are separate capabilities.

Activating the butter Recipe would place it in authoritative active-recipe enumeration while its classification remains intentionally unsuitable as a standalone meal.

Therefore Step 10 integrates reusable V2 Recipe Nutrition and the Planner consumption seam but keeps SCHOOL2022_53_19Z_BUTTER_PORTION inactive.

A later bounded production-data operation may activate a Recipe only when its suitability and Nutrition authority are independently ready.

## 8. DECISION — immutable RecipeIngredient composition binding

Step 10 runtime requires a new dependent persisted authority concept:

RecipeIngredientCompositionBinding.

Recommended table:

food_recipe_ingredient_composition_bindings

Minimum fields:

~~~text
recipe_ingredient_id          PK / FK → food_recipe_ingredients.id
composition_version_id        FK → food_composition_versions.id
registry_version              FK → nutrient_registry_snapshots.version
calculation_policy_version    nonblank string
created_at                    UTC instant
~~~

Exact runtime names may vary only if semantics remain identical.

Binding invariants:

- zero bindings means no Composition authority is published for the row;
- exactly one binding means immutable Composition authority is frozen;
- more than one binding is forbidden;
- UPDATE is forbidden;
- DELETE is forbidden;
- REPLACE semantics are forbidden;
- RecipeIngredient.food_ingredient_id must equal FoodCompositionVersion.food_ingredient_id.

A future correction may not repoint old history silently. It requires a separately reviewed immutable-history strategy.

## 9. DECISION — migration 0039

Step 10 runtime is expected to add migration id 0039, named approximately:

0039_recipe_ingredient_composition_binding.

Rules:

- the custom SQLite migration runner remains sole SQLite schema authority;
- migrations 0001–0038 remain an exact historical prefix;
- reserved 0033 remains unconsumed;
- existing Recipe, RecipeVersion and RecipeIngredient rows are preserved;
- existing profile, vector, Composition and source-corpus rows are preserved;
- no bulk binding backfill occurs.

If the bounded dependent-table model proves insufficient, STOP and amend this Contract Gate before runtime work continues.

## 10. DECISION — first production binding

Step 10 runtime publishes exactly one production binding:

~~~text
Recipe:
SCHOOL2022_53_19Z_BUTTER_PORTION

RecipeVersion:
source ru-school2022:recipe:53-19з
version_number = 1

RecipeIngredient:
required 10 g BUTTER_PEASANT_72_5_UNSALTED

Composition:
BUTTER_PEASANT_72_5_UNSALTED
FoodCompositionVersion version = 1
kind = ATOMIC
input_state = INPUT

registry:
RU_NUTRIENT_REGISTRY_V2
~~~

The publisher resolves UUIDs from accepted semantic identities and never hardcodes database-specific UUIDs.

## 11. DECISION — fresh, replay and conflict semantics

### Fresh

Allowed only when all of the following hold:

- exact Step 9 Recipe identity and provenance exist;
- Recipe remains inactive;
- exact required RecipeIngredient exists;
- exact Step 8 FoodIngredient is active;
- exact FoodCompositionVersion v1 exists and matches the row FoodIngredient;
- kind/input state are ATOMIC / INPUT;
- sealed V2 calculation succeeds;
- binding is absent.

Then exactly one binding is inserted.

### Exact replay

Allowed only when the existing binding resolves to the same RecipeIngredient, FoodIngredient, CompositionVersion, registry version and calculation policy.

Replay performs zero writes.

Recipe activation state is never rewritten by binding replay.

### Conflict

Fail closed if identity, source quantity/unit, food/composition relation, registry, calculation policy or accepted dependency differs; if Composition is missing/corrupt; if the FoodIngredient is missing/inactive; or if V2 calculation fails.

There is no latest-Composition fallback.

## 12. DECISION — general Nutrition authority resolution

Legacy V1 behavior remains accepted historical behavior.

General canonical RecipeVersion Nutrition follows:

### No required-row bindings

Use existing legacy Nutrition behavior unchanged.

### All required rows explicitly bound

Use the composition-backed canonical path only when:

- every required RecipeIngredient is bound;
- all required bindings use one compatible registry version;
- exact row mass is available;
- every binding matches the row FoodIngredient;
- every Composition calculation succeeds.

### Partial required-row binding

Fail closed.

Step 10 does not silently mix some V2 Composition rows with some legacy current-profile rows in one required recipe total.

Optional RecipeIngredients remain separate optional contributions.

## 13. DECISION — exact row mass authority

Step 10 adds no new quantity-conversion policy.

- g is exact recipe input mass;
- ml and pcs require the already accepted exact assessment/evidence path;
- estimate-only or blocked conversion remains non-authoritative;
- raw, gross, purchase or cooked mass is not substituted for recipe input mass.

The Step 9 row is exact 10 g and needs no conversion evidence.

## 14. DECISION — canonical V2 RecipeVersion result

Composition-backed Recipe Nutrition must expose canonical nutrient truth rather than only the legacy five-field projection.

The result must preserve at least:

- RecipeVersion identity;
- registry version;
- calculation policy version;
- exact binding identities;
- required total nutrient values by canonical nutrient code;
- per-base-serving nutrient values;
- explicit unknown nutrients;
- calculation issues/warnings;
- deterministic status.

Exact class/function names are implementation details.

## 15. DECISION — truthful compatibility projection

For the Step 9 10 g Recipe, accepted known values include:

- ENERGY_KCAL = 66.09;
- PROTEIN = 0.08 g;
- FAT_TOTAL = 7.25 g;
- FIBER_TOTAL_DIETARY = 0.00 g;
- the remaining accepted V2 values from Step 9.

WATER remains unknown.

Canonical total carbohydrate remains unknown.

STARCH plus SUGARS_TOTAL is not silently promoted to canonical total or available carbohydrate.

If a compatibility projection into legacy NutritionValues exists:

- kcal may map from ENERGY_KCAL;
- protein may map from PROTEIN;
- fat may map from FAT_TOTAL;
- fiber may map from FIBER_TOTAL_DIETARY;
- carbohydrate stays None unless the exact required canonical concept exists.

A sparse V2 result must not be mislabeled as legacy five-field COMPLETE.

## 16. DECISION — preserve NutritionService.recipe_version()

Existing callers of NutritionService.recipe_version() retain accepted historical behavior in Step 10.

Step 10 adds a new explicit canonical/composition operation or equivalent authority resolver rather than silently redefining the legacy V1 method.

This protects historical PR6 calculations, B1 assessment semantics, current-profile behavior and accepted audit/test receipts.

## 17. DECISION — Planner gets an explicit V2-safe projection

Planner v0.2 currently needs exact energy per serving for its bounded algorithm.

Step 10 may add an application-level Nutrition projection that distinguishes:

~~~text
full nutrient completeness
!=
exact energy authority available for current Planner algorithm
~~~

For composition-backed authority, Planner energy is usable only when:

- required binding coverage is complete;
- V2 calculation succeeds without authority/corruption issues;
- ENERGY_KCAL is present, finite and positive;
- per-base-serving scaling is exact.

Unknown carbohydrate and WATER remain unknown.

Step 10 must not globally reinterpret legacy NutritionStatus.INCOMPLETE recipes as Planner-eligible just because a kcal value exists.

Existing legacy candidate behavior remains unchanged.

## 18. DECISION — no meal-role compatibility expansion

Step 10 does not modify:

- ROLE_COMPATIBILITY_V1;
- PlannerConfig.compatibility_version;
- Recipe meal_type_code;
- MealPattern programs;
- member meal-pattern selections.

MealTypeCode.OTHER does not become breakfast, lunch, dinner or snack.

No butter-specific meal-role exception is permitted.

## 19. DECISION — production candidate pool remains unchanged by Step 9 Recipe

Step 10 does not activate SCHOOL2022_53_19Z_BUTTER_PORTION.

Therefore that Recipe remains:

- outside active Recipe enumeration;
- outside the production Planner candidate pool;
- outside selected production MealPlans.

Planner integration is proven with bounded test fixtures using a compatible active test Recipe classification.

Test fixtures are not production catalogue publication.

## 20. DECISION — future activation gate

A later production Recipe activation requires:

- verified immutable RecipeVersion;
- explicit Nutrition authority suitable for Planner consumption;
- recipe classification compatible with intended MealRole under current versioned compatibility, or a separately approved compatibility change;
- no applicability quarantine preventing automatic use;
- explicit bounded production-data authorization.

Nutrition calculation success alone never implies activation.

## 21. Transaction boundary

Step 10 requires no binding-plus-activation cross-context transaction because production activation is out of scope.

Binding publication uses one project-owned transaction.

Injected failure after an attempted binding write must roll back the binding publication.

Existing RecipeVersion and Composition history is read-only.

## 22. Preservation matrix

| Accepted truth | Step 10 requirement |
| --- | --- |
| migrations 0001–0038 | exact historical prefix |
| reserved 0033 | unchanged / unconsumed |
| Step 9 Recipe/Version/ingredient/steps | unchanged |
| Step 9 Recipe active state | remains inactive |
| Step 8 food/profile/vector/composition | unchanged |
| source-corpus rows | unchanged |
| legacy NutritionService.recipe_version | unchanged behavior |
| B1 assessments/evidence | unchanged |
| current-profile selector | unchanged |
| V1 registry/history | unchanged |
| V2 registry | unchanged |
| Planner compatibility map | unchanged |
| MealPattern selections | unchanged |
| production candidate pool | unchanged by Step 9 Recipe |
| WATER / canonical carbohydrate | remain unknown |
| School2022 declared nutrition | reference-only |
| AI_ENABLED=false | supported |

## 23. Adversarial acceptance tests

Runtime Step 10 must prove at least:

1. accepted base is a descendant of merged PR #93;
2. migrations 0001–0038 remain unchanged;
3. reserved 0033 remains unconsumed;
4. migration 0039 creates only bounded binding persistence;
5. populated upgrade preserves accepted Recipe/Composition/Nutrition rows;
6. migration failure is atomic;
7. exactly one Step 9 production binding is published;
8. binding resolves exact Step 8 FoodIngredient and Composition v1;
9. registry is exactly RU_NUTRIENT_REGISTRY_V2;
10. wrong FoodIngredient/composition relation fails;
11. missing/corrupt Composition fails;
12. binding UPDATE fails;
13. binding DELETE fails;
14. exact replay is zero-write;
15. conflicting binding fails closed;
16. partial required-row binding fails closed;
17. mixed required-row registry versions fail closed;
18. gram quantity uses exact RecipeIngredient input mass;
19. unaccepted ml/pcs estimate cannot become V2 authority;
20. Step 9 canonical result reproduces all accepted 17 values;
21. WATER remains unknown;
22. canonical total carbohydrate remains unknown;
23. School2022 declared nutrition cannot fill a missing canonical value;
24. existing legacy NutritionService.recipe_version() fixtures are unchanged;
25. legacy current-profile behavior is unchanged;
26. a synthetic fully bound compatible active Recipe yields Planner-safe exact energy;
27. legacy INCOMPLETE candidates are not globally enabled;
28. production Step 9 Recipe remains inactive;
29. production Step 9 Recipe stays outside authoritative Planner candidates;
30. ROLE_COMPATIBILITY_V1 is unchanged;
31. Planner compatibility version is unchanged;
32. accepted production Planner fixture outputs remain unchanged;
33. no Recipe/RecipeVersion/source-corpus publication occurs;
34. no API/UI/Retail/Auth/PostgreSQL/AI scope occurs;
35. AI_ENABLED=false.

## 24. Verification tier

Step 10 is a cross-context Nutrition / persistence / Planner integration.

Runtime review-ready evidence must include:

- migration fresh/upgrade/failure/replay tests;
- binding domain/repository tests;
- Step 8 and Step 9 preservation tests;
- canonical V2 Recipe Nutrition tests;
- legacy Nutrition regression;
- Planner application and pure-core regression;
- Planner Gate fixtures;
- migration lineage/coexistence/rebuild tests;
- focused Registry V2 and Partial Nutrition workflows;
- Russian nutrition methodology workflow;
- Docs / DC1;
- full backend shards;
- launcher regression;
- exact-head scope/whitespace audit;
- AI_ENABLED=false.

A later state/docs-only receipt does not invalidate byte-identical verified runtime evidence.

## 25. Explicit non-goals

Step 10 does not authorize:

- production activation of School2022 53-19з;
- changing meal_type=other;
- changing MealRole compatibility;
- new MealPattern programs/selections;
- a second Recipe or RecipeVersion;
- a second FoodIngredient;
- source-corpus expansion;
- source-declared nutrition authority;
- carbohydrate inference;
- WATER inference;
- current-profile selector changes;
- fake B1 assessment;
- bulk binding backfill;
- automatic latest/current Composition selection;
- mixed V1/V2 required-row authority;
- Recipe Assembly;
- Shopping / Prep / Retail;
- API / UI;
- Auth / PostgreSQL;
- AI authority.

## 26. Runtime handoff after gate merge

After this gate is reviewed and merged, a separate explicit authorization may implement:

~~~text
0039 binding persistence
→ exact Step 9 binding publication
→ canonical V2 RecipeVersion Nutrition operation
→ Planner composition seam
→ preservation verification
~~~

The production Step 9 Recipe stays inactive.

After runtime review/merge, stop before any real Recipe activation or next production data publication.

## 27. Stop boundary

This PR is docs/state only.

No migration, table, runtime service, binding row, Recipe activation, Planner code change or production write belongs in this gate PR.

After review-ready delivery:

1. stop;
2. obtain review and merge of this gate;
3. runtime Step 10 requires separate explicit authorization.
