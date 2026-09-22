# First Russian Food Batch — Implementation Contract Gate

**Status:** pre-implementation contract for Russian-data integration Step 4
**Accepted base:** `0ee9e5a3335e876d5a1de6a2c32ea245efe8e5e6` (merged PR #79)
**Runtime/schema/data publication in this gate:** none
**Current gate result:** **SOURCE AUTHORITY CLEARED FOR RU-NUT-DB / SOURCE SEMANTICS MAPPING STILL GATED**

## 1. Goal

Step 4 publishes the first bounded Russian source-native food batch through the
accepted deterministic path:

```text
licensed official FIC electronic database record
→ reviewed FoodIngredient identity
→ non-current FoodNutritionProfile + immutable source observations
→ RU_NUTRIENT_REGISTRY_V2 NutrientVector
→ ATOMIC FoodCompositionVersion
```

Step 3 already proves single-bundle transactional mechanics. Step 4 must prove
that one real licensed batch has sufficient identity, source semantics, canonical
nutrient mapping and provenance to use those mechanics without changing historical
USDA truth or inventing values.

This Contract Gate contains no production numeric seed.

## 2. FACT — accepted upstream state

Merged PR79 provides:

- reviewed non-current profile publication without historical V1 auto-bootstrap;
- canonical `FFO_NUTRIENT_VALUE_EVIDENCE_V2`;
- explicit V2 method validation;
- one project UoW / one transaction / seal-last publication;
- fresh / exact replay / conflict / rollback semantics;
- preserved V1 provenance and V1-pinned legacy Composition behavior.

No schema change is expected for Step 4. If implementation proves otherwise,
stop for a separate architecture decision.

Every Step 4 profile remains `is_current=false`; existing current USDA profiles
remain unchanged.

## 3. DECISION — production numeric authority is RU-NUT-DB

The project owner supplied the corpus release
`FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`.

Archive SHA-256:

```text
c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea
```

The corpus pins the official FIC electronic database page:

```text
source_id: RU-NUT-DB
captured: 2026-09-20
URL:
https://ion.ru/nauka/baza-dannykh-khimicheskogo-sostava/1-1-baza-dannykh/1.1_baza%20dannih.html
raw HTML SHA-256:
155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d
rows: 3216
transform: fic-inline-v1.0.0
```

A second official FIC interface independently reproduces all 29 shared fields for
each of the five candidate records with
`status=corroborated_same_publisher`.

**DECISION:** RU-NUT-DB is the Step 4 production numeric authority.

Book2002 remains historical/corroborating evidence only. It is not the Step 4
numeric source because the electronic DB is not byte/semantic identical to the
Book2002 snapshot. Examples include:

- rice: FIC `322.6 kcal / 71.4 g carbh` vs Book2002 `333 / 74.0`;
- carrot: FIC `33.7 kcal` vs Book2002 `35`;
- white cabbage: FIC `26.9 kcal` vs Book2002 `28`;
- beet: FIC `42.1 kcal` vs Book2002 `42`;
- sugar water: FIC `0.14` vs Book2002 `0.1`.

No cross-source averaging, substitution or silent reconciliation is allowed.

## 4. SOURCE AUTHORITY — cleared for RU-NUT-DB

The project owner supplied a signed license permission dated 2026-09-10 from
ФГБУН «ФИЦ питания и биотехнологии» to FamilyFoodOS.

The licensed object in Appendix №1 includes the electronic database
«Химический состав пищевых продуктов, используемых в Российской Федерации».

The permission, as supplied to the project, grants FamilyFoodOS rights including:

- reproduction/copying and storage of the database on project infrastructure;
- use in paid/commercial services and mobile applications;
- use in calculations and algorithms;
- inclusion of data in program code and a public repository subject to source
  attribution;
- creation of derivative databases, subject to the stated restriction against
  redistributing the source database as a standalone commercial product without
  an additional agreement;
- worldwide territory;
- three-year term from the dated permission, subject to the original instrument.

Required attribution from the permission is preserved in repository/runtime
documentation.

The public repository stores only a metadata receipt and evidence hashes, not the
signed scans themselves.

License evidence hashes supplied by the owner:

```text
main permission image:
98c6e1715141c60adbee4957442d41d664bc0fa54f3987164283e242f81ef4b5

Appendix №1 image:
37c8b8f54edb8a292fa4d571989c05afdad777641bce0a4ea1ed80e060be0eb4
```

Canonical receipt:
`docs/family-food/fic-nutrition-license-receipt.md`.

**DECISION:** the historical corpus field `reuse_rights=unresolved` is superseded
for this licensed RU-NUT-DB source by the later reviewed permission.

This is a repository governance decision based on the supplied permission, not an
independent legal opinion about unrelated sources.

## 5. FACT — exact candidate source records

The Step 4 batch is limited to exactly these five RU-NUT-DB records:

| Platform action | RU-NUT-DB code | DB locator | Exact source name |
| --- | ---: | --- | --- |
| reuse `SUGAR` | 1150 | `/DB/252` | Сахар-песок |
| reuse `CARROT` | 1187 | `/DB/126` | Морковь свежая красная |
| reuse `CABBAGE_GREEN` | 1184 | `/DB/69` | Капуста белокочанная свежая |
| reuse `BEET` | 1204 | `/DB/254` | Свекла свежая |
| create generic rice-groats identity | 66 | `/DB/103` | Крупа рисовая |

No sixth record may enter the implementation PR without reopening this gate.

## 6. DECISION — canonical food identity

The existing platform identities reused without mutating their canonical fields are:

- `SUGAR` — `Сахар-песок`;
- `CARROT` — `Морковь`;
- `CABBAGE_GREEN` — `Капуста белокочанная`;
- `BEET` — `Свёкла`.

The exact source form/name remains in immutable profile/vector provenance. A
narrower source row does not replace or redefine the canonical food identity and
does not replace the current USDA profile.

The FIC source says only `Крупа рисовая`; it does not establish long-grain or
polished subtype.

**DECISION:** the new identity is generic:

```text
canonical_code = RICE_GROATS
canonical_name = Крупа рисовая
category_code = grains
default_unit = g
is_active = true
```

Do not reuse `RICE_WHITE`. Do not use the earlier proposed
`RICE_POLISHED_DRY` because that subtype came from Book2002 rather than the
licensed RU-NUT-DB record.

## 7. DECISION — source version and provenance identity

The captured FIC interface does not publish a release/edition identifier.

Do not invent one.

Step 4 pins the source snapshot by capture date + source hash:

```text
source_name = FIC_RU_NUT_DB
source_version = snapshot-2026-09-20-155107ddb381c147
source_data_type = official_electronic_database_snapshot
source_id = exact RU-NUT-DB record code
```

Every positive V2 value uses canonical
`FFO_NUTRIENT_VALUE_EVIDENCE_V2` and retains:

- exact record code;
- exact JSON pointer;
- raw HTML SHA-256;
- source literal Decimal string;
- source field;
- explicit method code;
- mapping review reference;
- license/authority receipt reference.

## 8. FACT — source field inventory

RU-NUT-DB exposes 26 nutrient fields per candidate record.

Across the five rows:

```text
source nutrient observations = 130
published_numeric = 87
published_zero = 43
not_reported = 0
```

The package distinguishes numeric zero from null, but explicitly states that the
scientific meaning of zero is unresolved.

**DECISION:** every one of the 130 source observations is retained. A
`published_zero` is never promoted to an authoritative numeric zero merely
because the JSON literal is zero.

## 9. FACT / DECISION — currently proven canonical mappings

The corpus itself closes the 100 g edible basis and units for four top-level FIC
fields: `kcal`, `prot`, `fat`, `carbh`.

However it also explicitly records:

```text
carbh nutrient_definition = carbohydrates_source_definition_unresolved
FIC numeric-zero scientific semantics = unresolved
FIC DB hidden-field unit binding = unresolved
```

The branded-product interface contains labels/units for 26 fields, but the corpus
correctly records that those form fields are not a proven DB serialization
contract. Conflicts such as cholesterol and beta-carotene units prove that a
mechanical transfer is unsafe.

Therefore the only currently approved Step 4 positive canonical mappings are:

| RU-NUT-DB field | V2 code | Rule |
| --- | --- | --- |
| `kcal` | `ENERGY_KCAL` | positive published value only |
| `prot` | `PROTEIN` | positive published value only |
| `fat` | `FAT_TOTAL` | positive published value only |

Method code for these published rows is
`published_method_unspecified`.

For the exact five records this proves **13 positive canonical V2 values**:

- energy: 5;
- protein: 4 (sugar source zero remains held);
- fat: 4 (sugar source zero remains held).

### 9.1 Carbohydrate

`carbh` is grams per 100 g edible, but its exact nutrient definition is not
closed for this database snapshot.

**DECISION:** do not map it yet to either
`CARBOHYDRATE_AVAILABLE` or `CARBOHYDRATE_BY_DIFFERENCE`.

Book2002 methodology cannot be silently transferred to RU-NUT-DB because the
numeric snapshots differ and record derivation is not established.

### 9.2 Hidden fields

Fields including `diet_fibre`, `water`, `starch`, `mdsug`, minerals,
vitamins and fatty-acid fields remain source-only observations until their exact
DB-field unit/definition mapping is reviewed.

No same-name or equal-unit inference grants canonical authority.

## 10. DECISION — do not prematurely seal a 13-row vector

Step 3 vector seals are immutable. A sealed profile cannot later be enriched in
place.

Therefore Step 4 must not publish the currently proven 13-row sparse projection
until the first-batch canonical mapping set is explicitly frozen as the intended
terminal mapping for this source snapshot.

**DECISION:** before runtime publication, perform one bounded source-semantic
closure for these five RU-NUT-DB records.

That closure must decide, field by field:

- which additional DB fields have source-owned definition/unit evidence sufficient
  for a V2 mapping;
- whether `carbh` can be mapped to an existing V2 carbohydrate concept;
- which published-zero fields remain held;
- final positive V2 row count per food;
- final source-observation inventory and mapping receipt.

If no additional mappings can be established, an explicit reviewed decision may
accept the 13-row sparse projection as terminal for this snapshot. It must not
happen implicitly.

No schema change is authorized by this semantic closure.

## 11. DECISION — explicit ATOMIC versions

Accepted baseline already has ATOMIC version 1 for:

- `SUGAR`;
- `CARROT`;
- `CABBAGE_GREEN`.

Step 4 therefore uses explicit version 2 for those three.

The proposed version slots for the other two are:

- `BEET` → version 1;
- new `RICE_GROATS` → version 1.

Implementation must assert these slots against the exact accepted base. Any
unexpected occupied slot is a conflict; never auto-increment.

All Step 4 ATOMIC snapshots use `MassState.INPUT`.

## 12. DECISION — batch transaction orchestration

All five foods form one reviewed publication batch.

Step 3's public `ReviewedNutritionPublicationService.publish()` owns and commits
its own UoW. Five calls would create five independent transactions.

Step 4 therefore introduces a bounded batch-orchestration seam:

```text
ReviewedNutritionBatchPublicationService.publish_batch(five bundles)
    ↓ opens one NutritionPublicationUnitOfWork
transaction-neutral reviewed bundle operation
    ↓ applies food 1..5
verify complete five-food batch
    ↓
single commit
```

The existing public single-bundle `publish(bundle)` remains behaviorally
unchanged and becomes a one-bundle wrapper around the same transaction-neutral
application operation.

The batch path must not nest calls to the committing public method.

A failure on food 5 rolls back foods 1–4 from that attempt.

## 13. Fresh / replay / conflict semantics

### Fresh

After the semantic-mapping gate is closed, fresh publication must:

- reuse exactly four accepted FoodIngredients;
- create exactly one new `RICE_GROATS`;
- create five non-current FIC profiles;
- publish exactly the finally reviewed V2 rows;
- create five V2 seals;
- create five explicit ATOMIC versions;
- preserve every existing current profile and historical row.

### Exact replay

The exact same snapshot/mapping/license batch:

- inserts zero rows;
- updates zero rows;
- changes zero current flags;
- returns the same persisted IDs;
- leaves the database unchanged.

### Conflict

Fail the entire batch with no writes for:

- source record outside the exact five;
- changed raw source hash/record identity;
- canonical food identity drift;
- changed source value/state;
- changed mapping/method/evidence;
- changed authority receipt;
- partial prior bundle;
- unexpected ATOMIC version occupation;
- attempted `RICE_WHITE` substitution;
- any unreviewed field promoted to canonical truth.

No automatic repair, version bump or cross-source substitution exists.

## 14. Preservation matrix

| Existing truth | Step 4 requirement |
| --- | --- |
| Existing FoodIngredient rows | unchanged for four reused identities |
| Existing USDA current profiles | unchanged and remain current |
| Existing V1/V2 vectors/seals | unchanged |
| Existing ATOMIC versions | unchanged |
| V2 registry definitions | unchanged |
| Book2002 evidence | preserved as corroborating/historical; not rewritten |
| RU-NUT-DB raw snapshot | hash-pinned, immutable input |
| License conditions | attribution and scope preserved |
| Planner/API/UI defaults | unchanged |
| Recipe catalogue | unchanged |
| `AI_ENABLED=false` | complete deterministic path |

## 15. Non-goals

- no Book2002 numeric publication as production truth;
- no schema/migration;
- no generalized ingestion platform;
- no source-field guessing;
- no retailer/price/availability work;
- no Step 5 Russian target table;
- no persisted methodology selection;
- no transformation/yield/retention applicability;
- no recipe publication/remapping;
- no Planner/Gate1/Shopping;
- no API/UI;
- no AI authority;
- no automatic current-profile switch.

## 16. Adversarial implementation acceptance

The later runtime/data PR is not review-ready until it proves at least:

1. exact five RU-NUT-DB record identities and raw snapshot hash;
2. license authority receipt matches the batch source;
3. four exact identity reuses plus new `RICE_GROATS`;
4. `RICE_WHITE` and `RICE_POLISHED_DRY` are rejected for source code 66;
5. final reviewed field→V2 mapping manifest is exact;
6. all 130 source nutrient observations are retained;
7. every published zero remains nonnumeric unless a separately accepted zero
   policy explicitly authorizes otherwise;
8. no unresolved DB field becomes a canonical value;
9. all five profiles remain non-current;
10. current USDA profiles remain unchanged;
11. explicit ATOMIC versions are used without auto-increment;
12. single-bundle Step 3 behavior remains unchanged after refactor;
13. fresh five-food batch commits once;
14. exact replay writes zero rows;
15. one-food conflict rolls back the whole attempted batch;
16. failure injection after each food/boundary rolls back the batch;
17. V1 / Step 3 / V2 methodology regressions remain green;
18. foreign-key integrity remains clean;
19. attribution metadata is present where required by the license;
20. no Book2002 value silently substitutes for a licensed RU-NUT-DB value.

## 17. Verification tier

### Contract-gate PR

Docs/state/authority-receipt only:

- `git diff --check`;
- repository-relative links;
- source/archive/license hashes;
- exact five-record source identity cross-check;
- source-accounting state/count cross-check;
- state consistency;
- no runtime/schema/production data payload.

### Later source-semantic closure

Evidence/curation only unless runtime changes:

- exact field dictionary review;
- no numeric-source mutation;
- mapping manifest/count reproducibility;
- source-owned definition/unit evidence.

### Later runtime/data PR

Only after semantic mapping is frozen:

- focused Step 4 batch tests;
- Step 3 transactional publication regression;
- FoodIngredient/profile/V2 vector/ATOMIC regression;
- Russian methodology regression;
- source/authority/mapping validators;
- migration coexistence/lineage regression;
- full backend regression;
- full launcher regression;
- Docs/DC1 where triggered;
- `AI_ENABLED=false`.

## 18. Gate exit and current stop

PR80 may merge when this corrected source/authority/transaction contract is
reviewed and docs/static verification is green.

Merging PR80 does **not** start numeric publication automatically.

The next bounded Step 4 task is the source-semantic mapping closure for the five
licensed RU-NUT-DB records.

Runtime publication starts only after that mapping set is explicitly frozen.
