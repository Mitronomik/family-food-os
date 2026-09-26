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

## 2. DECISION — runtime delivery is split into Step 10-A and Step 10-B

The accepted Step 10 capability is one architectural sequence but not one runtime PR.

### Step 10-A — Composition-backed Recipe Nutrition Authority

Owns:

- migration 0039 binding persistence;
- immutable RecipeIngredient → exact FoodCompositionVersion binding;
- Nutrition-owned Recipe Nutrition authority publication UoW;
- one exact production binding for the Step 9 butter row;
- canonical V2 RecipeVersion Nutrition calculation;
- neutral Nutrition consumption projection;
- legacy NutritionService preservation.

Does not change Planner or MealPlan behavior.

### Step 10-B — Planner / MealPlan Consumption Integration

Starts only after Step 10-A is reviewed and merged.

Owns:

- Planner use of the neutral Nutrition consumption/readiness projection;
- explicit V2 exact-energy readiness semantics;
- Planner algorithm version advance;
- MealPlan/Serving consumption of the same neutral projection;
- cross-context integration tests.

Adds no migration and no new production Recipe activation.

This split keeps schema/publication risk separate from Planner algorithm behavior and
preserves the project rule that one implementation PR has one bounded goal.

## 3. FACT — accepted base

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

## 4. FACT — current general Nutrition cannot consume Step 9 authority safely

Current NutritionService.recipe_version() resolves RecipeIngredient nutrition through the legacy current-profile / B1 assessment path.

The Step 8 butter profile is intentionally non-current.

Therefore Step 10 must not:

- mark the Step 8 profile current;
- replace or retire the accepted generic current butter profile;
- invent a B1 assessment;
- reinterpret legacy current-profile semantics;
- fill missing nutrients from School2022 declared recipe totals.

## 5. FACT — current Planner composition

Current authoritative Planner composition performs:

~~~text
FoodRecipeCatalogueService.list_active()
→ get_current_verified()
→ NutritionService.recipe_version()
→ PlannerCandidate
~~~

Recipe activation is therefore a material Planner input change.

The pure Planner also rejects candidates when recipe classification is incompatible with MealRole or when its current bounded Nutrition contract is unavailable.

## 6. FACT — Recipe classification is not MealRole

Canonical architecture freezes:

~~~text
RecipeVersion.meal_type_code != MealRole
~~~

Current compatibility intentionally treats MealTypeCode.OTHER as compatible with no automatic MealRole.

The Step 9 Recipe has meal_type_code = other.

No accepted evidence establishes that a 10 g butter portion is a standalone breakfast, lunch, dinner or snack.

## 7. FACT — RecipeIngredient does not pin Composition

The persisted RecipeIngredient stores FoodIngredient identity, exact source quantity/unit and source/normalization metadata.

It does not persist which FoodCompositionVersion is authoritative for that immutable recipe row.

Composition supports multiple immutable versions per FoodIngredient.

Selecting latest, current, or version 1 by convention in general Nutrition would make historical RecipeVersion calculation depend on mutable application policy rather than persisted authority.

That is not acceptable for deterministic replay.

## 8. DECISION — Step 10 does not activate the Step 9 Recipe

The Step 9 handoff allowed Step 10 to consider activation and V2 Planner integration.

Preflight proves those are separate capabilities.

Activating the butter Recipe would place it in authoritative active-recipe enumeration while its classification remains intentionally unsuitable as a standalone meal.

Therefore Step 10 integrates reusable V2 Recipe Nutrition and the Planner consumption seam but keeps SCHOOL2022_53_19Z_BUTTER_PORTION inactive.

A later bounded production-data operation may activate a Recipe only when its suitability and Nutrition authority are independently ready.

## 9. DECISION — immutable RecipeIngredient composition binding

Step 10 runtime requires a new dependent persisted authority concept:

RecipeIngredientCompositionBinding.

Recommended table:

food_recipe_ingredient_composition_bindings

Minimum fields:

~~~text
recipe_ingredient_id          PK / FK → food_recipe_ingredients.id
composition_version_id        FK → food_composition_versions.id
registry_version              FK → nutrient_registry_snapshots.version
calculation_policy_version    exact FOOD_COMPOSITION_APPLICABILITY_V2
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

### Ownership and repository boundary

RecipeIngredientCompositionBinding is **Nutrition-owned platform calculation
authority**.

It is not:

- Recipe Catalogue source/culinary truth;
- Food Catalogue / Composition truth;
- Household-owned state.

Recipe Catalogue continues to own Recipe / RecipeVersion / RecipeIngredient.
Food Catalogue / Composition continues to own FoodIngredient /
FoodCompositionVersion / NutrientVector truth. Nutrition owns the reviewed
binding that selects which immutable Composition authority is consumed for one
immutable RecipeIngredient calculation.

Step 10-A must introduce one focused driver-independent binding repository
contract and one Nutrition-owned authority UoW. The UoW uses one active
connection/transaction and exposes only the dependencies needed by the command:

- read-only Recipe / RecipeVersion / RecipeIngredient resolution;
- read-only FoodIngredient resolution;
- read-only Composition resolution;
- read-only NutrientVector / nutrient-registry resolution;
- RecipeIngredientCompositionBinding read/write;
- commit / rollback.

No Recipe, RecipeVersion, RecipeIngredient, FoodIngredient,
FoodCompositionVersion, profile, NutrientVector or registry write is authorized
through this UoW.

The SQLAlchemy adapter may compose existing repository implementations over the
same active project UoW connection; application/domain code must not import
SQLAlchemy or open a second persistence scope.

## 10. DECISION — migration 0039

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

## 11. DECISION — first production binding

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

calculation_policy_version:
FOOD_COMPOSITION_APPLICABILITY_V2
~~~

The publisher resolves UUIDs from accepted semantic identities and never hardcodes database-specific UUIDs.

The policy value is the existing
`APPLICABILITY_CALCULATION_VERSION = "FOOD_COMPOSITION_APPLICABILITY_V2"`.
Step 10-A does not invent a second recipe-specific alias for the same calculator.
Every accepted calculation must return
`CompositionResult.calculation_version == "FOOD_COMPOSITION_APPLICABILITY_V2"`.

## 12. DECISION — fresh, replay and conflict semantics

External preflight is optional fail-fast validation only. It is never
authoritative for publication outcome.

Fresh / exact-replay / conflict classification is authoritative only inside the
same Nutrition-owned binding UoW that may write the binding.

Immediately before accepting either FRESH or EXACT_REPLAY, that UoW must
re-resolve and validate from its own active transaction:

- exact Recipe identity;
- exact RecipeVersion provenance/version;
- exact required RecipeIngredient identity, quantity and unit;
- exact FoodIngredient identity and `is_active=true`;
- exact FoodCompositionVersion identity/version and matching FoodIngredient;
- exact registry `RU_NUTRIENT_REGISTRY_V2`;
- sealed NutrientVector dependencies;
- deterministic applicability-aware Composition calculation;
- `CompositionResult.calculation_version ==
  "FOOD_COMPOSITION_APPLICABILITY_V2"`.

No classification may rely on a stale result produced by an earlier independent
read scope.

### Fresh

Allowed only when all of the following hold:

- exact Step 9 Recipe identity and provenance exist;
- Recipe remains inactive;
- exact required RecipeIngredient exists;
- exact Step 8 FoodIngredient is active;
- exact FoodCompositionVersion v1 exists and matches the row FoodIngredient;
- kind/input state are ATOMIC / INPUT;
- sealed V2 calculation succeeds inside the binding UoW;
- the calculation result reports exactly
  `FOOD_COMPOSITION_APPLICABILITY_V2`;
- binding is absent.

Then exactly one binding is inserted by that same UoW and committed once.

### Exact replay

Allowed only after the same in-UoW dependency re-resolution above succeeds and
the existing binding resolves to the same RecipeIngredient, FoodIngredient,
CompositionVersion, registry version and exact calculation policy
`FOOD_COMPOSITION_APPLICABILITY_V2`.

The deterministic calculation is re-evaluated against the pinned immutable
Composition/vector authority and its returned calculation version must match the
persisted policy.

Replay performs zero writes.

Recipe activation state is never rewritten by binding replay.

### Conflict

Fail closed if identity, source quantity/unit, food/composition relation,
registry, calculation policy or accepted dependency differs; if Composition is
missing/corrupt; if the FoodIngredient is missing/inactive; if the vector/registry
dependency is unavailable/corrupt; if V2 calculation fails; or if the returned
calculation version is not exactly
`FOOD_COMPOSITION_APPLICABILITY_V2`.

There is no latest-Composition fallback and no arbitrary nonblank policy value.

## 13. DECISION — general Nutrition authority resolution

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

## 14. DECISION — exact row mass authority

Step 10 adds no new quantity-conversion policy.

- g is exact recipe input mass;
- ml and pcs require the already accepted exact assessment/evidence path;
- estimate-only or blocked conversion remains non-authoritative;
- raw, gross, purchase or cooked mass is not substituted for recipe input mass.

The Step 9 row is exact 10 g and needs no conversion evidence.

## 15. DECISION — canonical V2 RecipeVersion result

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

## 16. DECISION — truthful compatibility projection

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

## 17. DECISION — preserve NutritionService.recipe_version()

Existing callers of NutritionService.recipe_version() retain accepted historical behavior in Step 10.

Step 10 adds a new explicit canonical/composition operation or equivalent authority resolver rather than silently redefining the legacy V1 method.

This protects historical PR6 calculations, B1 assessment semantics, current-profile behavior and accepted audit/test receipts.

## 18. DECISION — Planner gets an explicit V2-safe readiness projection

Planner currently needs exact energy per serving for its bounded algorithm.

Step 10 adds an explicit Nutrition consumption/readiness projection that
distinguishes:

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

The PlannerCandidate boundary may add an explicit readiness/authority field or
equivalent reviewed value. The additive default for existing callers must preserve
the current legacy rule exactly.

Existing legacy candidates continue to treat NutritionStatus.INCOMPLETE as
NUTRITION_UNAVAILABLE. Step 10 must not globally reinterpret them as eligible
merely because a kcal number exists.

A composition-backed candidate may carry truthful canonical/legacy status
INCOMPLETE while separately proving exact-energy readiness for the bounded Planner
algorithm.

### Planner versioning

This changes candidate Nutrition eligibility semantics for the new authority path.

Therefore PlannerConfig.version must advance from planner-v0.2 to a new explicit
version, expected planner-v0.3 or an equivalent reviewed identifier.

PlannerConfig.compatibility_version remains meal-role-recipe-v2 because meal-role
compatibility does not change.

Existing production selected outputs must remain unchanged for the accepted
fixture even though new traces correctly record the new planner version.

## 19. DECISION — MealPlan / Serving compatibility must not split from Planner

Planner eligibility and downstream Serving nutrition must consume the same
canonical authority without pretending sparse V2 data is legacy-complete.

Step 10 must not fabricate legacy current-profile contributions merely to fit the
existing RecipeVersionNutrition class.

Instead, Nutrition exposes a neutral immutable consumption projection (exact name
is an implementation detail) with at least:

- exact RecipeVersion id;
- compatibility NutritionValues for known legacy concepts;
- truthful legacy completeness status;
- canonical authority/readiness metadata;
- registry/calculation-policy identity.

Both legacy RecipeVersionNutrition and the new canonical V2 result can be adapted
to this small consumption contract without changing their underlying authority.

For a fully bound V2 RecipeVersion:

- version identity remains exact;
- known kcal/protein/fat/fiber values project exactly;
- carbohydrate stays None when the canonical concept is unavailable;
- legacy completeness remains INCOMPLETE when a required legacy field is unknown;
- canonical V2 values remain available separately and are not collapsed into the
  five-field compatibility projection.

Planner uses the explicit V2-safe exact-energy readiness from section 18.
MealPlan/Serving uses the compatibility values/status to scale known values while
preserving unknown propagation.

The MealPlan calculation boundary may be generalized from the concrete
RecipeVersionNutrition type to this narrow read-only consumption contract.
Existing callers and results must remain behavior-compatible.

This prevents a split-brain state where Planner can select a composition-backed
Recipe but Serving/day/week Nutrition cannot represent its accepted truth.

No MealPlan persistence schema change is required in Step 10 because the immutable
RecipeIngredient Composition binding and calculation-policy pin make the bounded
RecipeVersion Nutrition authority reproducible.

If implementation proves historical MealPlan replay additionally requires a
separate persisted nutrition-authority snapshot, STOP and amend this Contract Gate
before runtime work continues.

### Required integration proof

A bounded synthetic compatible active Recipe fixture must demonstrate the full
technical chain:

~~~text
canonical V2 Recipe Nutrition
→ neutral consumption projection
→ Planner exact-energy readiness
→ MealPlan COOK_RECIPE event
→ Serving scaling
→ member day/week Nutrition
~~~

Known nutrients scale exactly; unknown carbohydrate remains unknown; aggregate
legacy status remains truthful rather than being upgraded to COMPLETE.

## 20. DECISION — no meal-role compatibility expansion

Step 10 does not modify:

- ROLE_COMPATIBILITY_V1;
- PlannerConfig.compatibility_version;
- Recipe meal_type_code;
- MealPattern programs;
- member meal-pattern selections.

MealTypeCode.OTHER does not become breakfast, lunch, dinner or snack.

No butter-specific meal-role exception is permitted.

## 21. DECISION — production candidate pool remains unchanged by Step 9 Recipe

Step 10 does not activate SCHOOL2022_53_19Z_BUTTER_PORTION.

Therefore that Recipe remains:

- outside active Recipe enumeration;
- outside the production Planner candidate pool;
- outside selected production MealPlans.

Planner integration is proven with bounded test fixtures using a compatible active test Recipe classification.

Test fixtures are not production catalogue publication.

## 22. DECISION — future activation gate

A later production Recipe activation requires:

- verified immutable RecipeVersion;
- explicit Nutrition authority suitable for Planner consumption;
- recipe classification compatible with intended MealRole under current versioned compatibility, or a separately approved compatibility change;
- no applicability quarantine preventing automatic use;
- explicit bounded production-data authorization.

Nutrition calculation success alone never implies activation.

## 23. Transaction boundary

Step 10 requires no binding-plus-activation cross-context transaction because
production activation is out of scope.

Step 10-A binding publication is one **Nutrition-owned application command** with
one focused Recipe Nutrition authority UoW, one active connection and one
transaction.

Within that same transaction the command:

1. resolves Recipe / RecipeVersion / RecipeIngredient read-only dependencies;
2. resolves the exact active FoodIngredient;
3. resolves exact Composition / vector / registry dependencies;
4. executes the deterministic applicability-aware calculation and verifies
   `FOOD_COMPOSITION_APPLICABILITY_V2`;
5. classifies FRESH / EXACT_REPLAY / CONFLICT;
6. writes at most the one binding row;
7. commits once for FRESH or performs zero writes for EXACT_REPLAY.

Repositories participating in the command must use that UoW connection. They do
not open independent read/write connections while it is active.

An external preflight may fail early, but its observations never substitute for
the authoritative in-UoW recheck.

Injected failure after any attempted binding write must roll back the entire
binding command. The failed operation leaves no binding row or partial state.

Existing RecipeVersion, RecipeIngredient, FoodIngredient, Composition, profile,
vector and registry history is read-only in this command.

## 24. Preservation matrix

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
| Recipe/Composition ownership | unchanged; new binding is Nutrition-owned derived authority |
| Planner compatibility map | unchanged |
| Planner algorithm version | advances explicitly for new V2 readiness semantics |
| MealPattern selections | unchanged |
| production candidate pool | unchanged by Step 9 Recipe |
| WATER / canonical carbohydrate | remain unknown |
| School2022 declared nutrition | reference-only |
| AI_ENABLED=false | supported |

## 25. Adversarial acceptance tests

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
31. Planner compatibility version remains meal-role-recipe-v2;
32. Planner config/version advances explicitly for the new Nutrition eligibility semantics;
33. accepted production Planner selected outputs remain unchanged;
34. legacy PlannerCandidate callers with no new readiness authority retain the old
    NutritionStatus.INCOMPLETE rejection behavior;
35. a synthetic V2-bound compatible Recipe selected by Planner can be represented
    by MealPlan/Serving through the neutral Nutrition consumption projection;
36. Serving scaling preserves exact known kcal/protein/fat/fiber values;
37. missing canonical carbohydrate remains unknown through Serving/day/week aggregation;
38. sparse V2 MealPlan Nutrition is not upgraded to legacy COMPLETE;
39. canonical V2 nutrient truth is not replaced by the five-field compatibility projection;
40. no Recipe/RecipeVersion/source-corpus publication occurs;
41. no API/UI/Retail/Auth/PostgreSQL/AI scope occurs;
42. AI_ENABLED=false;
43. binding repository is Nutrition-owned and Recipe/Composition dependencies are
    read-only through the same binding UoW connection;
44. external preflight can observe the Step 8 FoodIngredient active, then the
    dependency can be deactivated before the binding UoW, and publication must
    fail closed with zero binding writes;
45. the same in-UoW active/dependency validation applies to exact replay, not only
    fresh publication;
46. accepted fresh/replay policy is exactly
    FOOD_COMPOSITION_APPLICABILITY_V2;
47. another/nonblank calculation policy value fails closed;
48. calculated CompositionResult.calculation_version must equal the persisted
    policy value;
49. injected late binding write failure rolls back the binding and leaves all
    Recipe/Composition/Nutrition dependencies unchanged.

## 26. Verification tier

Step 10 is a cross-context Nutrition / persistence / Planner integration,
delivered as two bounded runtime PRs.

Step 10-A review-ready evidence must include migration/binding/canonical-Nutrition
checks and broad regression required by its authoritative data publication,
including the post-preflight deactivation race, exact-replay in-UoW dependency
recheck, exact calculation-policy identity, and injected late binding rollback.

Step 10-B review-ready evidence must include Planner/MealPlan integration checks,
planner versioning evidence and broad regression for changed algorithm behavior.

Across the two runtime PRs, required evidence includes:

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

## 27. Explicit non-goals

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

## 28. Runtime handoff after gate merge

After this gate is reviewed and merged, runtime proceeds only by separate explicit
authorization in this order:

### Step 10-A

~~~text
0039 binding persistence
→ exact Step 9 binding publication
→ canonical V2 RecipeVersion Nutrition operation
→ neutral consumption projection
→ preservation verification
~~~

Stop after Step 10-A review/merge.

### Step 10-B

~~~text
Planner readiness projection
→ planner version advance
→ MealPlan/Serving neutral-consumption integration
→ cross-context regression
~~~

Step 10-B has no migration and no production Recipe activation.

The production Step 9 Recipe stays inactive through both substeps.

After Step 10-B review/merge, stop before any real Recipe activation or next
production data publication.

## 29. Stop boundary

This PR is docs/state only.

No migration, table, runtime service, binding row, Recipe activation, Planner code change or production write belongs in this gate PR.

After review-ready delivery:

1. stop;
2. obtain review and merge of this gate;
3. Step 10-A runtime requires separate explicit authorization;
4. Step 10-B remains unauthorized until Step 10-A is reviewed and merged.
