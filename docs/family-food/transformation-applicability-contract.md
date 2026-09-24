# Step 7 — Transformation Applicability Contract

**Status:** Implementation Contract Gate / docs-only
**Decision date:** 2026-09-24
**Accepted base:** `6ec1069d867388e5d1f4782ce6cdeed08c017694` (merged PR #87)
**Bounded step:** Russian-data integration Step 7 — transformation applicability
**Runtime implementation authorized by this document:** no — merge/review this gate first

## 1. Goal

Step 7 makes the existing Composition mass-state / transformation / yield /
retention model safely usable with `RU_NUTRIENT_REGISTRY_V2` **only when the
process evidence is explicitly applicable to the exact food/process context**.

The step must close this gap without changing historical V1 Composition truth:

```text
V2 ATOMIC NutrientVector
+ exact FoodTransformation
+ exact food applicability
+ explicit season applicability
+ exact source/review receipt
+ V2-bound retention factors where retention is used
→ deterministic transformed V2 composition result
```

Step 7 is infrastructure/calculation semantics. It is **not** authorization to
publish corpus loss coefficients, recipes, Step 8 foods, or Planner defaults.

## 2. FACT — accepted current state

Accepted main after PR87 includes:

- migration `0035_versioned_nutrient_registry`;
- `RU_NUTRIENT_REGISTRY_V2` with 54 definitions;
- versioned nutrient identity `(registry_version, code)`;
- migration `0036_member_reference_methodology_selection`;
- migration `0037_meal_plan_reference_methodology_pins`;
- Step 3 reviewed V2 profile/vector/ATOMIC publication;
- Step 4 first Russian food batch;
- Step 5 reviewed Russian reference table;
- Step 6A/6B persisted reference methodology history.

The existing `CompositionCalculator` remains intentionally V1-pinned.

## 3. FACT — current transformation/retention coupling

Current Composition runtime has:

- immutable/versioned `FoodTransformation`;
- immutable/versioned `YieldModel`;
- immutable/versioned `NutrientRetentionProfile`;
- nutrient-specific `RetentionValue`;
- explicit mass states;
- immutable Composition DAG/history.

Current `SqlAlchemyFoodCompositionRepository.nutrient_definition(code)` always
resolves the V1 registry.

Current `add_retention_profile(...)` likewise validates and writes retention
factors as V1.

Therefore a V2 ATOMIC vector may be persisted/read, but a transformed calculation
cannot be treated as V2-capable merely because the nutrient codes look familiar.

## 4. FACT — 0035 already stores registry identity on retention rows

Migration 0035 rebuilt `food_retention_values` with:

```text
registry_version
nutrient_code
FOREIGN KEY (registry_version, nutrient_code)
  → nutrient_definitions(registry_version, code)
```

Historical retention rows were explicitly pinned to V1.

However the original 0029 domain snapshot shape and
`food_retention_profiles.snapshot_sha256` do **not** include
`registry_version`.

Therefore adding registry identity directly to the existing
`RetentionValue` / `NutrientRetentionProfile` snapshot would invalidate
historical replay/digests.

**DECISION:** Step 7 does not rewrite the existing retention snapshot shape.

## 5. FACT — V1 and V2 code equality is not universal compatibility

Migration 0035 proves:

- 50 V1 definitions are retained unchanged in V2;
- `CARBOHYDRATE_AVAILABLE` is deliberately redefined as a
  method-independent component;
- V2 adds:
  - `VITAMIN_A_RE`;
  - `NIACIN_EQUIVALENT`;
  - `VITAMIN_E_TOCOPHEROL_EQUIVALENT`;
- the three new equivalent definitions explicitly prohibit implicit conversion.

Therefore:

> same nutrient code is not sufficient authority to reuse a retention factor
> across registry versions.

Even for an unchanged definition, Step 7 does not automatically copy or relabel
historical V1 retention evidence as V2 evidence.

## 6. FACT — source corpus is evidence, not automatic transformation authority

The supplied corpus contains transformation/loss material, but it is not a
ready-to-publish Step 7 numeric package.

Observed source states include:

- Book2002 appendix loss models:
  - source-average culinary models;
  - `production_rights_gate = separate_review`;
  - process conditions such as combined washing/cutting/thermal treatment,
    discarded broth and residue;
- School2022 generalized retention assumptions:
  - `normalized_quarantined`;
  - `independently_validated = false`;
  - `do_not_reapply_to_published_rows = true`;
- legacy recipe-interface retention rows:
  - `UNVERIFIED_LEGACY_EXTRACTION`;
  - `ready_for_integration = false`;
  - explicit notes that retained-nutrient calculation is deferred until
    raw/cooked state and yield evidence are complete.

**DECISION:** Contract Gate and initial Step 7 runtime publish **zero production
numeric transformation/yield/retention factors** from those packages.

Any later numeric publication requires its own reviewed source/right/applicability
receipt.

## 7. DECISION — applicability belongs to the immutable transformation version

Do not create a second independently versioned transformation aggregate.

Introduce one dependent record:

`TransformationApplicability`.

It is one-to-one with an immutable `FoodTransformation` identity.

Conceptual shape:

```text
TransformationApplicability
- transformation_id: UUIDv4          # PK/FK to FoodTransformation
- food_ingredient_id: UUIDv4         # exact canonical food identity
- retention_registry_version: nullable version code
- season_scope: ALL_SEASONS | EXACT_SOURCE_PERIOD
- season_reference: nullable non-empty reviewed token
- evidence_scope_id: non-empty stable process-evidence identity
- provenance: CompositionProvenance
- snapshot_sha256: canonical digest
```

The `FoodTransformation` already owns:

- transformation version;
- transformation type / operation;
- input mass state;
- output mass state;
- exact yield-model reference;
- exact retention-profile reference.

Therefore the applicability record does not duplicate those fields.

## 8. DECISION — applicability changes create a new transformation version

Applicability is part of transformation truth.

If exact food, season scope, source applicability or retention registry binding
changes:

- do not UPDATE an applicability row;
- do not attach a different applicability row to the same transformation;
- publish a new immutable `FoodTransformation` version/identity and its new
  applicability record.

This keeps historical replay stable.

## 9. DECISION — no late applicability after a transformation is in composition history

A transformation must not become newly executable after it has already been
embedded in an immutable `FoodCompositionVersion`.

Therefore Step 7 persistence rejects applicability insertion when the referenced
`transformation_id` is already present in `food_composition_steps`.

Publication order for a new applicability-aware transformed composition is:

```text
yield / retention evidence
→ FoodTransformation
→ TransformationApplicability
→ FoodCompositionVersion / steps
→ commit
```

No post-hoc applicability writer may change historical calculation semantics.

## 10. DECISION — exact food applicability

One applicability row authorizes one transformation version for one exact
`FoodIngredient`.

No automatic inheritance is allowed across:

- cultivar;
- cut;
- animal species/part;
- raw/cooked form;
- frozen/fresh form;
- generic food category;
- recipe/dish family.

A source/category model can become executable only after a reviewed mapping to
the exact canonical FoodIngredient and transformation version.

## 11. DECISION — season applicability

The Russian methodology review requires season applicability to remain explicit.

Step 7 uses:

```text
season_scope = ALL_SEASONS
```

only when review explicitly establishes season-independent applicability.

Otherwise:

```text
season_scope = EXACT_SOURCE_PERIOD
season_reference = <reviewed exact token>
```

Missing season evidence is not interpreted as `ALL_SEASONS`.

Step 7 does not derive season from Household date/calendar.

The V2 calculator accepts an optional exact `season_reference`; it performs only
exact matching. Calendar-to-season interpretation belongs to a later owning
product/data contract if required.

## 12. DECISION — source applicability and overlap

`CompositionProvenance` retains:

- source;
- source version;
- evidence reference;
- review reference.

`evidence_scope_id` identifies the exact reviewed process/loss scope.

Within one sequential transformation chain for one composition version, the same
`evidence_scope_id` must not be applied twice.

This prevents a combined cold/heat/source-average loss model from being split
across several steps and double-counted.

The same evidence scope may be used by independent sibling component chains only
when each has its own accepted exact applicability record.

## 13. DECISION — retention registry binding stays outside historical snapshot digest

For a transformation with no retention profile:

```text
retention_registry_version = null
```

For a transformation with a retention profile:

```text
retention_registry_version = exact registry version
```

and all `food_retention_values` in that profile must use exactly that registry.

Mixed-registry retention profiles fail closed.

Step 7 does not change the historical
`NutrientRetentionProfile.snapshot_sha256` representation.

The new applicability snapshot/digest is the replay receipt that binds an exact
transformation version to an exact retention registry.

## 14. DECISION — V2 retention publication and reading are explicit

Preserve existing behavior:

- `add_retention_profile(profile)` remains historical V1 write behavior;
- `retention_profile(profile_id)` remains the historical snapshot reader and
  does not change its domain/digest shape.

Step 7 adds explicit registry-aware seams, conceptually:

```text
add_retention_profile_for_registry(
  profile,
  registry_version
)

retention_profile_for_registry(
  profile_id,
  registry_version
)
```

The registry-aware reader returns the existing historical domain snapshot only
after proving that **every persisted retention row** for that profile has the
requested exact registry version. A missing, mixed or mismatched registry fails
closed.

This preserves old snapshot hashes while allowing the V2 calculator to validate
the SQL-level registry binding rather than trusting the applicability row alone.

Initial non-legacy use accepts only:

`RU_NUTRIENT_REGISTRY_V2`.

No registry is inferred from:

- nutrient code;
- source;
- unit;
- transformation type.

## 15. DECISION — no automatic V1 → V2 retention carry-forward

A V2 transformed calculation requires retention evidence explicitly published
under V2 when a retention factor is needed.

Do not automatically reuse V1 factors because:

- a code exists in both registries;
- the unit is unchanged;
- 50 definitions happen to be unchanged;
- the source factor appears nutrient-generic.

In particular:

- V1 `CARBOHYDRATE_AVAILABLE` retention is not relabelled V2;
- no retention is inferred for the three new equivalent definitions;
- absent V2 retention remains unknown.

An eventual reviewed V2 factor may reuse the same underlying source evidence,
but that is a new explicit publication decision, not an adapter shortcut.

## 16. DECISION — preserve the legacy calculator

Existing:

`CompositionCalculator`

remains V1-pinned and semantically unchanged.

It must continue to:

- resolve V1 definitions;
- read historical V1 retention profiles;
- reproduce historical Composition results;
- preserve all current tests/replay.

Step 7 does not silently upgrade existing callers.

## 17. DECISION — add explicit applicability-aware V2 publication and calculation paths

Existing `add_versions(...)` remains compatible with historical V1 Composition
publication and does **not** gain a universal applicability requirement.

Step 7 adds an explicit V2 transformed-composition publication seam. Before a
transformed V2 `FoodCompositionVersion` can be inserted, that path verifies for
every composition step that:

- an applicability row already exists for the exact transformation;
- `applicability.food_ingredient_id == composition.food_ingredient_id`;
- retention registry binding is valid when retention exists;
- season/source applicability data are internally valid.

ATOMIC compositions and legacy V1 composition publication do not require a Step 7
applicability row.

Step 7 runtime also introduces a separate explicit calculation path, conceptually:

`ApplicabilityAwareCompositionCalculator`.

Required input includes:

- root composition version;
- exact registry version;
- requested nutrient codes;
- optional exact season reference.

Initial supported registry:

`RU_NUTRIENT_REGISTRY_V2`.

It uses the existing version-aware `NutrientRegistryReader`, not
`CompositionReader.nutrient_definition(code)`.

## 18. DECISION — V2 calculator registry rules

For one V2 calculation:

1. every ATOMIC NutrientVector used by the DAG must have the requested exact
   registry version;
2. mixed V1/V2 atomic vectors fail closed;
3. each requested definition is resolved from the requested registry;
4. exact `NutrientDefinition.semantic_identity` must match;
5. each transformation step requires accepted exact applicability;
6. applicability food identity must equal the exact
   `FoodCompositionVersion.food_ingredient_id` whose step is being evaluated;
7. if retention is present, applicability retention registry must equal the
   requested vector registry and the registry-aware retention reader must prove
   every factor row uses that same registry;
8. missing requested retention factor makes that nutrient unknown;
9. no implicit retention of 100% exists;
10. missing yield keeps output mass unknown;
11. unknown remains unknown and never becomes numeric zero.

## 19. DECISION — source-published dish analysis remains separate

A source-published prepared-dish nutrient analysis is not a reusable
FoodTransformation retention profile merely because it shows before/after or
loss-like numbers.

The following remain distinct authorities:

```text
source-published dish analysis
!=
FoodTransformation applicability
!=
NutrientRetentionProfile
!=
YieldModel
```

Step 7 must not reverse-engineer reusable component retention factors from a
declared dish total.

## 20. Expected persistence change

Expected next migration:

`0038_transformation_applicability`.

Reserved `0033_recipe_template_catalogue` remains reserved/unconsumed.

Expected new table:

`food_transformation_applicability`.

Conceptual minimum columns:

```text
transformation_id PK/FK
food_ingredient_id FK
retention_registry_version nullable FK
season_scope
season_reference nullable
evidence_scope_id
provenance_json
snapshot_sha256
```

No existing Composition/NutrientVector/MealPlan table rebuild is expected.

## 21. Required 0038 database invariants

0038 must enforce or enable fail-closed enforcement of:

- one applicability row per transformation;
- immutable UPDATE/DELETE;
- no replacement under the same transformation ID;
- no applicability insertion after the transformation is referenced by a
  composition step;
- `ALL_SEASONS → season_reference IS NULL`;
- `EXACT_SOURCE_PERIOD → non-empty season_reference`;
- retention registry null iff the transformation has no retention profile;
- when retention exists, all retention rows use the exact bound registry;
- future/new retention profiles cannot mix registry versions;
- explicit V2 transformed-composition publication rejects missing applicability
  or a food-identity mismatch before composition publication;
- legacy `add_versions(...)` remains valid for historical V1 behavior;
- exact FKs remain clean.

If implementation proves one of these cannot be enforced safely without
rebuilding an accepted table, **STOP and amend this Contract Gate before runtime
implementation**.

## 22. Preservation matrix

Step 7 must preserve:

| Existing truth | Requirement |
| --- | --- |
| migrations 0001–0037 | exact accepted prefix |
| reserved 0033 | unchanged / unconsumed |
| V1 registry | unchanged |
| V2 registry | unchanged |
| historical V1 nutrient vectors/seals | unchanged |
| Step 3/4 V2 profiles/vectors/ATOMIC compositions | unchanged |
| existing retention profile domain snapshot shape | unchanged |
| historical retention snapshot hashes | unchanged |
| legacy V1 retention rows | remain V1-pinned |
| existing CompositionCalculator | unchanged V1 semantics |
| existing FoodCompositionVersion history | unchanged |
| Step 5 reference table | unchanged |
| Step 6 selections / MealPlan pins | unchanged |
| Planner/API/UI defaults | unchanged |
| AI_ENABLED=false | supported |

No backfill is required to make historical transformations V2-applicable.

## 23. Runtime publication scope after gate merge

The initial Step 7 runtime PR may implement:

- applicability domain/read/write contract;
- migration 0038;
- explicit registry-aware V2 retention read/write seams;
- explicit applicability-aware V2 composition publication seam;
- explicit applicability-aware V2 calculator;
- synthetic/repository-owned fixtures;
- migration and replay verification.

It does **not** publish Book2002/School2022/legacy workbook numeric factors.

Production transformation/applicability rows remain zero unless a separately
reviewed source package is explicitly authorized.

## 24. Adversarial acceptance tests frozen by this gate

Runtime Step 7 must prove at least:

1. legacy `CompositionCalculator` V1 result/replay is unchanged;
2. V2 ATOMIC calculation works on the explicit V2 path;
3. transformed V2 composition without applicability fails closed;
4. applicability for another FoodIngredient fails closed;
5. wrong retention registry fails closed;
6. mixed V1/V2 atomic vectors fail closed;
7. V1 retention factor is not automatically reused for V2;
8. V1 `CARBOHYDRATE_AVAILABLE` retention is not relabelled V2;
9. new equivalent-code retention remains unknown without exact V2 evidence;
10. missing retention factor yields unknown nutrient, not implicit 100%;
11. missing yield yields unknown output mass;
12. `ALL_SEASONS` works only when explicitly published;
13. season-specific applicability requires exact season-reference match;
14. missing/incorrect season reference fails closed;
15. duplicate `evidence_scope_id` in one sequential chain fails closed;
16. distinct sibling chains do not become false overlap merely because the same
    reviewed source is used;
17. mixed-registry values in one new retention profile are rejected;
18. registry-aware retention read fails on mixed/mismatched persisted rows;
19. legacy V1 `add_versions(...)` remains usable without applicability;
20. explicit V2 transformed publication rejects missing applicability;
21. explicit V2 transformed publication rejects applicability for another food;
22. late applicability after composition-step publication is rejected;
23. applicability + transformation + composition can publish atomically in one
    UoW;
24. failure after applicability insert before composition commit rolls back all
    attempted Step 7 state;
25. applicability is immutable;
26. fresh / populated 0037→0038 migration works;
27. injected 0038 failure leaves no marker / no partial table or trigger state;
28. backup restore / re-upgrade works;
29. FK check is clean;
30. Step 3/4 V2 ATOMIC publication regression stays green;
31. Step 6 persistence/MealPlan regressions stay green;
32. Planner output/default behavior remains unchanged;
33. AI is not involved.

## 25. Verification tier

Step 7 is Composition runtime + migration + cross-version Nutrition semantics.

Required review-ready runtime evidence:

- focused transformation/applicability domain tests;
- focused Composition V1/V2 tests;
- NutrientVector V1/V2 regression;
- Step 3 transactional V2 publication regression;
- Russian methodology regression;
- migration fresh / populated / failure / restore tests;
- migration lineage/coexistence;
- MealPlan/Step 6 persistence regression;
- Planner no-default-switch regression;
- `AI_ENABLED=false`;
- full backend regression;
- full launcher regression;
- Docs/DC1;
- exact-head scope/diff/whitespace audit.

Broad checks run once after runtime freeze, then repeat only if runtime bytes
change or a concrete failure requires it.

## 26. Explicit non-goals

Step 7 does not authorize:

- Step 8 recipe-dependency food publication;
- Step 9 executable Russian RecipeVersion publication;
- Step 10 Planner integration;
- source-rights approval;
- Book2002 loss-factor publication;
- School2022 generalized loss publication;
- legacy workbook retention-factor promotion;
- automatic dish-analysis-to-retention conversion;
- automatic V1→V2 factor carry-forward;
- calendar/season inference from MealPlan dates;
- current-profile selector changes;
- API/UI;
- Shopping/Prep;
- Auth/PostgreSQL/Retail/AI.

## 27. ASSUMPTION

The expected 0038 change can remain additive because:

- retention rows are already registry-version-aware after 0035;
- applicability can be represented as a dependent record keyed by immutable
  transformation ID;
- no historical retention snapshot shape must change.

Runtime implementation must prove this assumption.

If a safe implementation requires a rebuild or a second independently persisted
aggregate, stop and amend the gate.

## 28. OPEN QUESTIONS deferred beyond Step 7

These are not silently solved by this gate:

- which Book2002 loss rows, if any, have acceptable production reuse rights;
- which source/category loss rows can be mapped to exact FoodIngredient;
- exact season normalization for future season-specific evidence;
- exact Step 8 foods that require transformed rather than direct cooked profiles;
- whether a later household-facing Planner ever needs calendar→season mapping;
- exact numeric V2 retention profiles for production recipes.

## 29. Stop boundary

This PR is the Step 7 Contract Gate only.

No migration 0038, runtime calculator, applicability table, numeric factor
publication, Step 8 food batch, RecipeVersion or Planner integration belongs in
this PR.

After gate merge:

1. stop;
2. Step 7 runtime requires separate explicit authorization;
3. after Step 7 runtime review/merge, stop before Step 8.
