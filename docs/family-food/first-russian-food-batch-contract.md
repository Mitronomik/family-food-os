# First Russian Food Batch — Implementation Contract Gate

**Status:** pre-implementation contract for Russian-data integration Step 4
**Accepted base:** `0ee9e5a3335e876d5a1de6a2c32ea245efe8e5e6` (merged PR #79 / Step 3 transactional publication)
**Runtime/schema/data publication in this gate:** none
**Gate result:** **TECHNICALLY READY / PERMISSION REPORTED — EVIDENCE REVIEW PENDING**
**Candidate batch:** exactly five reviewed Book2002 source records

## 1. Goal

Step 4 is the first bounded publication of Russian source-native food composition
through the already accepted deterministic path:

```text
reviewed source record
→ canonical FoodIngredient identity
→ non-current FoodNutritionProfile + immutable legacy-field observations
→ RU_NUTRIENT_REGISTRY_V2 NutrientVector
→ ATOMIC FoodCompositionVersion
```

Step 3 already proves the transactional mechanics. Step 4 must prove that one
real reviewed source batch has sufficient **identity, source authority, nutrient
mapping and provenance** to use those mechanics without changing historical
USDA truth or inventing values.

This gate contains no source numeric values and does not publish a production
batch.

## 2. FACT — accepted upstream state

### 2.1 Step 3 publication primitive exists

Merged PR79 provides:

- reviewed non-current profile publication without historical V1 auto-bootstrap;
- source-neutral `FFO_NUTRIENT_VALUE_EVIDENCE_V2`;
- explicit V2 method validation;
- one project UoW / one transaction / seal-last publication;
- fresh / exact replay / conflict / rollback guarantees;
- version-aware vector reads and pinned ATOMIC publication;
- preserved V1 provenance and V1-pinned legacy Composition behavior.

**DECISION:** Step 4 reuses this primitive. No duplicate importer/UoW/persistence
path is introduced.

### 2.2 No schema change is expected

Migrations 0034 and 0035 plus Step 3 already represent:

- partial/non-current nutrition profiles;
- immutable legacy source observations;
- V2 nutrient values and seals;
- explicit ATOMIC versions.

**DECISION:** Step 4 consumes no migration. If implementation proves a schema
change is necessary, stop for a separate architecture decision.

### 2.3 Existing current profiles are historical truth

The reused catalogue identities already have USDA-backed current profiles.
A Russian source-native profile is an additional immutable source snapshot, not
a replacement.

**DECISION:** every Step 4 profile remains `is_current=false`. Step 4 never calls
`clear_current()`, never mutates an existing current profile and never changes
Planner/API/UI defaults.

## 3. FACT — exact candidate batch

The batch is limited to the five source records already prepared and visually
reviewed in the DC2 evidence chain:

| Source code | Reviewed source label | Step 4 canonical action | Source input form |
| --- | --- | --- | --- |
| `10.1.1` | Сахар-песок | reuse `SUGAR` | `dry_granulated` |
| `8.1.5.1` | Морковь | reuse `CARROT` | `raw_root` |
| `8.1.2.1` | Капуста белокочанная | reuse `CABBAGE_GREEN` | `fresh_head` |
| `8.1.5.12` | Свёкла | reuse `BEET` | `raw_root` |
| `6.5.3` | Крупа рисовая шлифованная | create `RICE_POLISHED_DRY` | `dry_polished` |

No sixth food may enter the implementation PR without reopening this gate.

## 4. DECISION — canonical food identity

### 4.1 Reused identities

The following platform identities are reused without changing their stored
canonical fields:

- `SUGAR` — canonical name `Сахар-песок`;
- `CARROT` — canonical name `Морковь`;
- `CABBAGE_GREEN` — canonical name `Капуста белокочанная`;
- `BEET` — canonical name `Свёкла`.

The existing USDA profile attached to each identity is only one nutrition source;
it does not define the FoodIngredient identity itself.

Implementation must fail closed if the current catalogue identity differs from the
accepted canonical code/name/category/unit facts at the accepted base.

### 4.2 New rice identity

The source record `6.5.3` is generic polished rice groats. Existing
`RICE_WHITE` means `Рис белый длиннозёрный` and cannot be reused.

**DECISION:** Step 4 creates:

```text
canonical_code = RICE_POLISHED_DRY
canonical_name = Крупа рисовая шлифованная
category_code = grains
default_unit = g
is_active = true
```

No alias to `RICE_WHITE` is created. No food-form equivalence with cooked rice
is implied.

## 5. DECISION — explicit ATOMIC versions

Step 4 never calculates `max(version)+1`.

Accepted baseline evidence already pins ATOMIC version 1 for:

- `SUGAR`;
- `CARROT`;
- `CABBAGE_GREEN`.

Therefore the Step 4 publication uses explicit ATOMIC version **2** for those
three identities.

The accepted PR6 Russian-food package contains no Step-4-target ATOMIC reference
for `BEET`, and `RICE_POLISHED_DRY` is a new identity.

The proposed explicit versions are therefore:

| Food code | Step 4 ATOMIC version |
| --- | ---: |
| `SUGAR` | 2 |
| `CARROT` | 2 |
| `CABBAGE_GREEN` | 2 |
| `BEET` | 1 |
| `RICE_POLISHED_DRY` | 1 |

Implementation must assert these exact version slots before the first write.
Any occupied slot with other truth is a conflict and stops publication; it is
never repaired by silently choosing another version.

All five Step 4 ATOMIC snapshots use `MassState.INPUT`: they represent the
reviewed edible input form, not a cooked/transformed state. Transformation,
yield and retention applicability remain Step 7.

## 6. FACT / DECISION — source-state scope

The prepared evidence contains exactly:

- 5 source profiles;
- 12 reviewed source fields per profile;
- 60 source cells total;
- 45 `published_positive`;
- 15 `below_detection`;
- zero missing cells in this twelve-field subset.

Printed source zero means below detection with unknown detection limit. It is not
an exact numeric zero.

**DECISION:** all 60 source-cell states remain reproducible evidence. Step 4 does
not densify, infer or erase source-only observations.

## 7. DECISION — profile projection

The owning `FoodNutritionProfile` is a legacy-compatible projection, not the
authoritative V2 nutrient set.

For every published Step 4 profile:

- `basis_grams = 100`;
- `is_current = false`;
- positive source `energy_kcal`, `protein_g`, `fat_g` and `fiber_g` may
  project to the matching legacy field;
- `below_detection` legacy values persist as SQL NULL with immutable source
  observation state/literal;
- source-native `carbohydrates_g` **never** populates legacy
  `FoodNutritionProfile.carbohydrates_g`; that field remains NULL with
  `METHOD_INCOMPATIBLE` evidence because the source concept is available
  carbohydrate, not historical V1 total/by-difference carbohydrate.

All five legacy fields retain immutable source observations where applicable.
No unknown is replaced by zero.

## 8. DECISION — V2 nutrient mapping

The existing V2 registry/method policy is sufficient; Step 4 adds no nutrient
definition.

| Source field | V2 code | Method for positive source row |
| --- | --- | --- |
| `energy_kcal` | `ENERGY_KCAL` | `published_method_unspecified` |
| `protein_g` | `PROTEIN` | `published_method_unspecified` |
| `fat_g` | `FAT_TOTAL` | `published_method_unspecified` |
| `carbohydrates_g` | `CARBOHYDRATE_AVAILABLE` | `available_published_row_method_unspecified` |
| `fiber_g` | `FIBER_TOTAL_DIETARY` | `published_method_unspecified` |
| `water_g` | `WATER` | `published_method_unspecified` |
| `starch_g` | `STARCH` | `published_method_unspecified` |
| `sugars_g` | `SUGARS_TOTAL` | `published_method_unspecified` |
| `cholesterol_mg` | `CHOLESTEROL` | `published_method_unspecified` when positive |
| `saturated_fat_g` | `FATTY_ACIDS_SATURATED_TOTAL` | `published_method_unspecified` when positive |

The carbohydrate mapping relies on the already accepted Russian methodology:
the book describes source-native available carbohydrate while the exact row method
may be unspecified. This does not convert the value to
`CARBOHYDRATE_BY_DIFFERENCE`.

### 8.1 Source-only fields

The current V2 registry has no canonical definition for:

- `ash_g`;
- `organic_acids_g`.

**DECISION:** these remain source-only observations in the complete vector
observation inventory. They do not become numeric nutrient rows and do not justify
a new registry code in Step 4.

### 8.2 Below-detection fields

Any `below_detection` cell remains held/unavailable evidence and creates no
numeric V2 row.

The accepted optional published-zero-estimate methodology does not authorize
Step 4 to persist an estimated zero as authoritative canonical food composition.

## 8.3 Historical evidence reconciliation

The PR74/DC2 review correctly recorded:

```text
canonical_nutrient_mapping = null
publication_ready = false
nutrient_equivalence_accepted = false
```

at the time that evidence was produced.

Later accepted decisions changed only the relevant technical prerequisites:

- PR75 accepted the explicit Russian source-native interpretation policy;
- PR77 introduced `RU_NUTRIENT_REGISTRY_V2` and explicit method adapters;
- PR79 introduced the transactional V2 publication primitive.

**DECISION:** this Step 4 contract supersedes the historical
`canonical_nutrient_mapping=null` only for the exact field→V2 mappings listed
in §8. It does not reinterpret equal units as equivalence and does not grant any
unlisted nutrient mapping.

The historical `publication_ready=false` remains effective because source
authority is still unresolved. Likewise, historical
`nutrient_equivalence_accepted=false` is not treated as a blanket FoodIngredient
identity decision; food identity is decided separately in §4 from reviewed
food/form evidence.

## 9. DECISION — exact expected vector shape

Without copying source numeric values into this gate, the reviewed field-state and
mapping contract implies the following V2 numeric row counts:

| Source code | Expected positive V2 rows |
| --- | ---: |
| `10.1.1` sugar | 4 |
| `8.1.5.1` carrot | 8 |
| `8.1.2.1` white cabbage | 8 |
| `8.1.5.12` beet | 8 |
| `6.5.3` polished rice | 9 |
| **Total** | **37** |

Every profile retains a 12-cell source observation inventory. Therefore the batch
preserves 60 reviewed source cells while publishing only 37 positive canonical V2
values.

A different count is a contract drift and requires review; implementation must
not “fix” the count by adding zeros or dropping evidence.

## 10. DECISION — provenance package

Every positive V2 value uses canonical
`FFO_NUTRIENT_VALUE_EVIDENCE_V2` and binds:

- exact Step 4 source edition/export identity;
- exact source food code;
- stable source observation/component identity;
- exact source unit and Decimal literal;
- top-level explicit `method_code`;
- reviewed mapping status;
- source locator;
- definition/mapping review reference.

The batch also retains the complete source-cell observation inventory and the
authority receipt described below.

Raw page images/full book text are not production payload.

## 11. SOURCE AUTHORITY GATE — permission reported, evidence review pending

### 11.1 Current repository status

Accepted repository evidence records:

```text
rights_status = BLOCKED_PENDING_RIGHTS_REVIEW
explicit_reuse_permission = not_found
production_use_disposition = pending_scope_review
public_redistribution_disposition = pending_scope_review
```

This repository evidence was correct when recorded. On 2026-09-21 the user
explicitly stated that they possess permission for Book2002 use.

**DECISION:** from this point the blocker is no longer "permission is assumed
absent". It is **evidence/scope review pending**. The project must inspect the
actual permission before declaring Step 4 runtime publication authorized.

### 11.2 Current external verification — 2026-09-21

The reviewed 2002 edition is identifiable as ISBN `5-94343-028-8`.

The Russian State Library catalogue currently states that the document is
available for full online viewing and free work in its viewer. That establishes
access; this contract does **not** treat the catalogue wording as an explicit grant
for commercial machine extraction or public redistribution of derived structured
data.

The current official FRC Nutrition database page exposes an online chemical
composition database and a request form for an Excel database requiring email and
purpose of request. No explicit commercial/public-redistribution license was
visible on the reviewed page.

This is a factual access/terms observation, not a legal conclusion.

Reviewed URLs:

- `https://search.rsl.ru/ru/record/01001844793`
- `https://ion.ru/nauka/baza-dannykh-khimicheskogo-sostava/1-1-baza-dannykh/1.1_baza%20dannih.html`

### 11.3 Required source-authority receipt

Before runtime/data implementation starts, the user's permission must be reviewed
and repository evidence must contain an immutable receipt answering the intended
Step 4 scope:

- exact source edition/export/document identity and hash;
- authority/evidence document identity;
- machine extraction permitted or not established;
- internal retention permitted or not established;
- commercial calculation use permitted or not established;
- public repository/public derived structured-data redistribution permitted or
  not established;
- required attribution;
- scope: these five food records or an explicitly broader scope;
- reviewer/date and evidence locator.

Acceptable unblock paths are:

1. the user's existing permission/license, if review confirms that it covers the
   intended scope;
2. an official export with explicit applicable terms;
3. a separately approved bounded factual-use disposition with documented review.

The assistant/implementation agent does not make the legal determination on its
own.

### 11.4 Public-repository coupling

FamilyFoodOS currently stores reviewed production seed/data packages in a public
repository.

If authority permits internal/commercial use but **not** public redistribution of
the derived numeric package, Step 4 must stop. Moving the numeric data to a private
artifact/runtime source would be a separate data-distribution architecture
decision and is not silently introduced by this batch.

### 11.5 Source substitution is not automatic

If an official Excel export or another authorized source is obtained and its
version/fields/methods differ from Book2002, do not reuse the Book2002 payload
blindly.

A new source review must verify:

- food identity/form;
- basis;
- field definitions and methods;
- source states;
- V2 mappings;
- value/provenance receipts.

## 12. ASSUMPTION — implementation package after authority clears

If the source-authority gate is satisfied without changing source semantics,
Step 4 implementation is expected to contain:

- a bounded five-row/record publication manifest;
- exact authority receipt;
- reproducible numeric payload or approved source-backed build mechanism;
- deterministic transformation into Step 3 publication bundles;
- no generic ingestion platform;
- no network dependency at production publication time;
- no LLM-derived values.

If authority or source format requires a different delivery architecture, reopen
the gate instead.

## 13. Fresh / replay / conflict semantics

Step 4 inherits Step 3 transaction semantics and adds batch-level identity.

### Fresh

For the accepted five records:

- reuse exactly four reviewed existing FoodIngredients;
- create exactly one new `RICE_POLISHED_DRY`;
- create exactly five non-current source profiles;
- create exactly 37 positive V2 nutrient rows;
- create five V2 seals;
- create five explicit ATOMIC versions;
- preserve all existing current profiles, V1/V2 history and existing ATOMIC rows.

### Exact replay

A second run of the exact same authority-approved batch:

- creates zero rows;
- updates zero rows;
- changes zero current-profile flags;
- returns the same persisted FoodIngredient/profile/composition identities;
- leaves the database byte/semantic state unchanged.

### Conflict

Fail the entire batch with no writes for any mismatch including:

- canonical identity drift;
- unexpected occupied ATOMIC version;
- same profile provenance with changed source values/states;
- changed authority/source receipt;
- changed V2 evidence/mapping/method;
- changed vector hash/count;
- missing or partial prior bundle;
- attempted reuse of `RICE_WHITE`;
- source record outside the accepted five.

No automatic repair, version bump or source substitution exists.

## 14. DECISION — batch transaction orchestration

All five foods are one reviewed publication batch.

Step 3's existing public `ReviewedNutritionPublicationService.publish()` owns its
own UoW and commits one bundle. Calling that public method five times would create
five independent transactions and would violate Step 4 atomicity.

**DECISION:** Step 4 introduces a bounded batch-orchestration seam without changing
the accepted single-bundle behavior.

Required design:

```text
ReviewedNutritionBatchPublicationService.publish_batch(five bundles)
    ↓ opens one NutritionPublicationUnitOfWork
transaction-neutral reviewed bundle operation
    ↓ food 1
    ↓ food 2
    ↓ food 3
    ↓ food 4
    ↓ food 5
verify complete five-food batch
    ↓
single commit
```

Implementation may refactor the Step 3 service so its existing public
`publish(bundle)` becomes a one-bundle wrapper around a transaction-neutral
internal/application operation. The existing `publish(bundle)` API and all
accepted fresh/replay/conflict/rollback semantics must remain unchanged.

The batch service must not call the committing public `publish()` method from
inside another UoW.

A failure or conflict on food 5 must roll back fresh writes for foods 1–4 from that
attempt. Exact replay of all five performs zero writes and one read transaction
with no commit-side mutations.

No generic ingestion platform, distributed transaction mechanism or new database
abstraction is introduced by this seam.

## 15. Preservation matrix

| Existing truth | Step 4 requirement |
| --- | --- |
| Existing FoodIngredient IDs/fields | unchanged for the four reused identities |
| Existing USDA current profiles | same IDs, values and `is_current=true` state |
| Existing V1/V2 vectors/seals | unchanged |
| Existing ATOMIC versions | unchanged |
| SUGAR/CARROT/CABBAGE_GREEN v1 ATOMIC | preserved; Step 4 uses v2 |
| Legacy CompositionCalculator | remains V1-pinned |
| V2 registry definitions | unchanged |
| Planner/API/UI defaults | unchanged |
| Recipe catalogue | unchanged |
| Source rights status | cannot be promoted without reviewed authority receipt |
| `AI_ENABLED=false` | full publication path remains deterministic |

## 16. Non-goals

- no source-rights conclusion by the coding agent;
- no new migration/schema;
- no generalized ingestion platform;
- no retailer/price/availability work;
- no Step 5 Russian target table;
- no persisted methodology selection;
- no transformation/yield/retention applicability;
- no recipe publication/remapping;
- no Planner/Gate1/Shopping change;
- no API/UI;
- no AI authority;
- no automatic current-profile switch.

## 17. Adversarial implementation acceptance

Runtime/data implementation is not review-ready until it proves at least:

1. exact five-record input scope;
2. four exact identity reuses and one new rice identity;
3. `RICE_WHITE` cannot satisfy `RICE_POLISHED_DRY`;
4. expected explicit ATOMIC versions are unoccupied/occupied exactly as required;
5. all five profiles remain non-current;
6. existing current USDA profiles remain byte/semantic equivalent;
7. exactly 60 source cells retained;
8. exactly 37 positive V2 numeric rows;
9. every below-detection cell remains nonnumeric;
10. source-native carbohydrate maps only to `CARBOHYDRATE_AVAILABLE` with the
    accepted explicit method;
11. ash/organic acids remain source-only evidence;
12. canonical V2 evidence/authority receipt round-trips;
13. existing single-bundle Step 3 `publish()` behavior remains unchanged after the transaction-neutral refactor;
14. fresh five-food batch commits once;
15. exact full-batch replay writes zero rows;
16. conflict on any one food leaves all five unchanged;
17. injected failure after each food/boundary rolls back the whole batch;
18. nested use of the committing single-bundle `publish()` is rejected/not used by the batch path;
19. unexpected ATOMIC-version occupation fails instead of auto-incrementing;
20. V1 and Step 3 regressions remain green;
21. foreign-key integrity remains clean;
22. no blocked source values are committed before the authority gate clears.

## 18. Verification tier

### Contract-gate PR

Docs/state only:

- `git diff --check`;
- docs links;
- state consistency;
- candidate/evidence hashes and counts checked against accepted repository metadata;
- no runtime/data payload.

### Later implementation PR, only after source authority clears

Required exact-head evidence:

- focused Step 4 batch tests;
- Step 3 transactional publication regression;
- FoodIngredient/profile/V2 vector/ATOMIC regression;
- Russian methodology regression;
- DC2 package/authority validator;
- migration coexistence/lineage regression;
- full backend regression;
- full launcher regression;
- Docs and DC1 where triggered;
- `AI_ENABLED=false`.

## 19. Gate exit and current stop

This Contract Gate is complete when:

- exact five-food scope is accepted;
- identity and composition-version decisions are accepted;
- V2 mapping/count contract is accepted;
- batch-level atomicity requirement is accepted;
- preservation/adversarial matrices are accepted;
- docs/state are synchronized;
- this docs-only gate PR is reviewed and merged.

However **runtime Step 4 remains not yet authorized** until the user's reported
permission is reviewed against §11 and the source-authority receipt is approved.

Merging this contract does not itself authorize copying/publishing Book2002
numeric values; review of the reported permission may remove that remaining gate.
