# Transactional Nutrition Publication — Implementation Contract Gate

**Status:** pre-implementation contract for Russian-data integration step 3
**Accepted base:** `5343734e620c9f36d24aad54320c2196588b004d` (merged PR #77)
**Runtime/schema changes in this gate:** none
**Next runtime step after acceptance:** implement one transactional reviewed publication path

## 1. Goal

Step 3 establishes a reusable, deterministic publication operation for one reviewed bundle:

```text
FoodIngredient
→ FoodNutritionProfile + immutable source observations
→ RU_NUTRIENT_REGISTRY_V2 NutrientVector
→ ATOMIC FoodCompositionVersion
```

The operation must prove **fresh / exact replay / conflict / rollback** semantics before any Russian production food batch is published.

This gate freezes the implementation contract first. It does not publish Book2002 values, approve source rights, publish Russian target tables, change methodology selection, change Planner/API/UI defaults, publish recipes, close Gate1 or start Shopping.

## 2. FACT — current repository capabilities and couplings

### 2.1 Existing schema is sufficient

Merged migrations already provide the required storage:

- `0034_partial_nutrition_profiles` allows nullable legacy macro fields and immutable `food_nutrition_profile_observations`;
- `0035_versioned_nutrient_registry` gives nutrient definitions and values the identity `(registry_version, nutrient_code)`;
- `nutrition_vector_seals` already pins one immutable `registry_version` per profile;
- `food_composition_versions.profile_id` references the sealed nutrition profile, so an ATOMIC composition is transitively pinned to the vector registry through the seal;
- the existing project `SqlAlchemyUnitOfWork` owns one connection and one transaction.

**DECISION:** Step 3 consumes no new migration. If implementation proves a schema change is necessary, stop and return for a separate architecture decision. Do not consume `0036` opportunistically. Reserved `0033_recipe_template_catalogue` remains unused.

### 2.2 Complete profile inserts currently auto-bootstrap V1

`SqlAlchemyFoodNutritionProfileRepository.add()` preserves historical behavior: when a profile has complete legacy kcal/protein/fat/carbohydrate fields, it automatically calls the V1 nutrient-vector initializer.

A profile can have only one immutable vector seal because `nutrition_vector_seals.profile_id` is the primary key.

Therefore a complete reviewed V2 profile cannot safely use the generic profile `add()` path and then publish a V2 seal: the legacy V1 seal may already exist.

**DECISION:** Step 3 adds a specialized reviewed/versioned publication writer that persists a validated profile + source observations **without invoking legacy V1 bootstrap**. Do not add a generic boolean such as `bootstrap_v1=false` to ordinary catalogue operations. Existing catalogue/profile behavior remains unchanged.

### 2.3 Vector persistence is already version-capable

The merged vector reader joins values to definitions using `registry_version` and validates every value against the seal. The current RU publication adapter still hardcodes V1.

**DECISION:** the Step 3 publication port requires an explicit registry version and Step 3 accepts only `RU_NUTRIENT_REGISTRY_V2`. No version is inferred from units, source name or nutrient code.

### 2.4 ATOMIC Composition needs no registry column

An ATOMIC composition references the nutrition profile; the profile has exactly one sealed vector; the seal owns `registry_version`.

**DECISION:** do not duplicate registry identity in `food_composition_versions`.

### 2.5 Current-profile selection is a separate later decision

Partial profiles cannot be legacy-current. Complete profiles can be current under the old catalogue semantics, but Step 3 must not silently change default Nutrition/Planner behavior before persisted methodology selection and later integration steps.

**DECISION:** every Step 3 publication profile is persisted with `is_current=false`, including complete profiles. Existing current profile IDs and values are preserved exactly. Step 3 does not call `clear_current()`.


### 2.6 V2 value provenance must be source-neutral

The persisted vector schema is registry-version-aware, but the current V1 read adapter still decodes the historical USDA/FDC evidence envelope. It expects source-specific keys such as `source_nutrient_nbr` and the old nested `observation` / `mapping` shape.

That shape is valid historical V1 evidence, but it is not a FamilyFoodOS-wide source contract. Requiring a Russian or future source to fabricate FDC-style identifiers would turn an external dataset quirk into a domain invariant.

**DECISION:** Step 3 introduces a registry-version-aware provenance decoding seam.

- V1 persisted JSON and V1 decoding behavior remain unchanged.
- V2 uses a normalized source-neutral evidence envelope.
- V2 evidence must retain exact profile source identity/version/type, source component/observation identity when the source supplies one, source value/unit, source locator/definition references, mapping status, uncertainty/estimated state and the explicit supported `method_code`.
- `method_code` must be available to the V2 methodology adapter without guessing.
- V2 must not require or invent FDC-only fields such as `source_nutrient_nbr`.
- the V2 decoder must produce the existing domain `NutrientProvenance` without changing its source semantics or inventing facts.

The normalized envelope is a persistence/application contract, not permission to discard original raw/source evidence. Original evidence remains referenced by immutable provenance/receipts.

### 2.7 Legacy CompositionCalculator remains V1-pinned

After PR77, `SqlAlchemyFoodCompositionRepository.nutrient_definition(code)` deliberately resolves V1 definitions for the legacy Composition engine. `CompositionCalculator` compares ATOMIC vector definitions with those V1 definitions.

A V2 ATOMIC snapshot can therefore be persisted and read, but Step 3 must not claim that the legacy Composition calculation path has become V2-aware merely because storage accepts the vector.

**DECISION:** Step 3 does not change the legacy `CompositionReader.nutrient_definition(code)` behavior or broaden transformation/retention calculation semantics.

For Step 3, a V2 ATOMIC bundle is validated through:

```text
FoodCompositionVersion identity
+ version-aware NutrientVectorReader
+ V2 provenance decoder
+ NutritionMethodologyService.atomic_input for supported V2 methodology reads
```

The legacy `CompositionCalculator` remains V1-compatible. V2 transformation/retention applicability and any version-aware Composition calculation contract belong to the separately approved transformation-applicability step (Step 7).

## 3. Application contract

Introduce a bounded application operation, named by implementation as a reviewed/versioned nutrition publication service, consuming a validated bundle equivalent to:

```text
ReviewedNutritionPublicationBundle
  ingredient
    action: REUSE_EXISTING | CREATE_REVIEWED
    canonical identity
  profile
    exact source provenance
    nullable legacy values
    immutable source observations
    is_current = false
  vector
    registry_version = RU_NUTRIENT_REGISTRY_V2
    ordered/sparse nutrient values
    value_count
    value_sha256
    observations_json
  atomic_composition
    explicit composition version
    explicit input mass state
    exact publication provenance
```

External/source IDs never become FamilyFoodOS entity UUIDs. New UUIDs are project identities created by the operation.

The caller must supply an **explicit composition version**. The publisher must not silently calculate `max(version)+1`. A later data batch owns the reviewed version number for each food identity.

## 4. Pre-write validation

Before the first database mutation, validate every condition that does not require persisted-state comparison:

- bundle registry is exactly `RU_NUTRIENT_REGISTRY_V2`;
- profile is non-current;
- profile/source observations satisfy the PR76 domain contract;
- nutrient codes are unique;
- each nutrient definition exists under V2;
- each numeric value has finite non-negative Decimal semantics;
- V2 present values contain explicit supported method evidence where a method adapter exists;
- no equal-unit substitution is used for incompatible definitions;
- vector `value_count` and `value_sha256` match the canonical ordered values;
- vector/profile source provenance agrees;
- V2 value provenance uses the source-neutral V2 envelope, round-trips through the V2 decoder and exposes explicit supported `method_code` without fabricated source-specific fields;
- ATOMIC composition references the same FoodIngredient/profile identity and has an explicit mass state/version;
- publication provenance is non-empty and reviewable.

Validation cannot grant source-use permission. Rights remain a separate gate.

## 5. Single-UoW write order

All fresh writes occur inside one existing project Unit of Work and one transaction:

```text
1. resolve/create reviewed FoodIngredient
2. insert non-current FoodNutritionProfile + source observations without V1 bootstrap
3. insert V2 nutrient values
4. insert V2 vector seal LAST
5. insert ATOMIC FoodCompositionVersion
6. read/verify the resulting bundle inside the same transaction
7. commit once
```

The seal remains the vector completeness boundary. Composition publication must not occur before a readable valid V2 seal exists.

No method may commit internally before step 7.

## 6. Fresh / replay / conflict semantics

### 6.1 Fresh

Fresh means the intended authoritative bundle is absent.

Expected result:

- create only the explicitly reviewed missing FoodIngredient when action is `CREATE_REVIEWED`;
- create exactly one profile and its observation rows;
- create exactly the reviewed V2 nutrient rows and one V2 seal;
- create exactly one explicit ATOMIC composition version;
- preserve every pre-existing current profile and historical V1/V2 row.

### 6.2 Exact replay

Replay resolves identity from canonical FoodIngredient identity plus exact profile provenance and explicit composition version.

If every persisted immutable fact is semantically identical:

- return success/no-op;
- insert **zero** rows;
- update **zero** rows;
- clear **zero** current profiles;
- retain the same profile/vector/composition IDs;
- leave database content unchanged.

Replay comparison must include profile snapshot values, source observations, registry version, nutrient amounts and provenance, vector hash/count/observations, composition mass state/version/provenance and FoodIngredient identity.

### 6.3 Conflict

Fail closed with no writes when any authoritative identity is reused with different truth, including:

- canonical food code/name/form conflict;
- same profile provenance with different profile values;
- same profile provenance with different source observations;
- an existing seal for that profile under another registry;
- different V2 nutrient set/hash/provenance;
- requested composition version already occupied by a different snapshot;
- existing ingredient is inactive or does not match the reviewed identity;
- an exact profile exists but the expected sealed-vector/ATOMIC bundle is only partially present.

Step 3 does **not** repair mixed/partial historical state. Adoption or repair of pre-existing partial bundles requires a separate explicit operation.

## 7. Rollback guarantees and failure-injection matrix

Any exception before successful commit must leave the persistent database equivalent to its pre-operation state.

Required injected failure points:

1. after new FoodIngredient insert;
2. after profile + source observations;
3. after one or more nutrient values but before seal;
4. after seal but before ATOMIC composition;
5. after ATOMIC insert but before commit;
6. transaction commit failure/uncertain persistence boundary where the existing UoW contract can simulate it.

For points 1–5, assert zero surviving task rows and unchanged pre-existing rows. Also assert `PRAGMA foreign_key_check` remains empty.

The implementation must not catch a conflict and then commit earlier writes.

## 8. Preservation matrix

| Existing truth | Step 3 requirement |
| --- | --- |
| V1 registry snapshot/definitions | byte/semantic unchanged |
| Existing V1 nutrient values/seals | IDs, amounts, provenance, hashes unchanged |
| Existing V2 registry artifact | unchanged; read only |
| Generic complete-profile `add()` | historical V1 auto-bootstrap behavior unchanged |
| Existing current FoodNutritionProfile | same ID/current flag/values |
| Existing profile provenance rows | never rewritten |
| Existing ATOMIC/Composition snapshots | immutable and unchanged |
| V1 Composition retention semantics | remain V1-pinned |
| Existing RU V1 publication seed/path | behavior unchanged |
| V1 persisted provenance JSON / decoder | unchanged |
| Legacy CompositionCalculator definition semantics | remain V1-pinned |
| Planner/API/UI defaults | unchanged |
| `AI_ENABLED=false` | complete path remains supported |

## 9. Implementation boundaries

Expected runtime surface is limited to:

- a specialized application contract/service for reviewed versioned publication;
- a specialized SQLAlchemy Core publication adapter/UoW composition using the existing project UoW;
- a registry-version-aware nutrient-provenance decoding seam that preserves V1 decoding unchanged and adds source-neutral V2 decoding;
- reuse of existing FoodIngredient/profile/vector/Composition domain objects and validation;
- focused tests plus required regression workflow updates only if needed.

Prefer a specialized publication writer over weakening generic repository semantics.

### Non-goals

- no migration/schema change;
- no Book2002 or other blocked-source numeric publication;
- no Step 4 Russian food batch;
- no source-rights decision;
- no current-profile selector change;
- no target tables;
- no persisted methodology choice;
- no transformation/retention applicability work;
- no RecipeVersion publication;
- no Planner/Gate1/Shopping/API/UI changes;
- no AI authority.

## 10. Adversarial acceptance tests

The implementation PR is not review-ready until it proves at least:

1. **fresh complete V2 bundle** publishes without generating a V1 seal;
2. **fresh partial V2 bundle** publishes with explicit unknown observations and no invented zero;
3. V2 vector is readable by the version-aware vector reader;
4. V2 ATOMIC composition is readable and binds to the same ingredient/profile/vector;
5. source-neutral V2 provenance round-trips through `NutrientVectorReader` without invented FDC/source-specific identifiers;
6. `NutritionMethodologyService.atomic_input` can consume a supported V2 value only with valid explicit method evidence;
7. legacy V1 provenance reads and legacy V1 `CompositionCalculator` behavior remain unchanged;
8. exact replay produces zero writes and stable IDs;
9. same provenance + changed profile value fails closed;
10. same provenance + changed source observation fails closed;
11. same profile + wrong registry/versioned vector fails closed;
12. changed nutrient hash/provenance fails closed;
13. occupied composition version with different truth fails closed;
14. pre-existing current profile is unchanged after fresh publication and replay;
15. generic complete-profile insertion still produces its historical V1 behavior;
16. all rollback injection points leave no partial task state;
17. `PRAGMA foreign_key_check` is empty after fresh/replay/failure tests;
18. a V2 ATOMIC bundle is not falsely accepted through the legacy V1-pinned `CompositionCalculator`;
19. existing Nutrition/NutrientVector/Composition regressions remain green.

Use synthetic/repository-owned test fixtures for Step 3. Do not require blocked external numeric corpus to prove publication mechanics.

## 11. Verification tier

This is a cross-context persistence/transaction change. Required final exact-head evidence after runtime freeze:

- focused Step 3 publication tests;
- affected FoodIngredient/profile tests;
- affected NutrientVector V1/V2 tests;
- affected Composition/ATOMIC tests;
- Russian methodology tests;
- migration coexistence/lineage regression even though no new migration is expected;
- full backend regression;
- full launcher regression;
- Docs verification;
- DC1/data-contract verification where workflow triggers are affected;
- `AI_ENABLED=false`.

Broad exact-head CI runs after runtime behavior is frozen. Any later runtime change invalidates that exact-head receipt and reruns the affected/broad verification. Pure documentation corrections after runtime freeze follow the proportional verification policy and do not automatically invalidate byte-identical runtime evidence.

## 12. Gate exit

This contract gate is complete when:

- dependency inventory has been reviewed;
- the no-migration decision remains valid;
- the specialized no-V1-bootstrap publication seam is accepted;
- fresh/replay/conflict/rollback behavior is unambiguous;
- preservation matrix is accepted;
- adversarial tests are accepted as implementation DoD;
- docs/state/AGENTS are synchronized;
- this docs-only gate PR is reviewed and merged.

Only then may the runtime Step 3 implementation PR start.
