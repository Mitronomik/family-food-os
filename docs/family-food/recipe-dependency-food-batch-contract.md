# Step 8 — Recipe-Dependency Food Batch Contract

**Status:** Implementation Contract Gate / docs-only
**Decision date:** 2026-09-24
**Accepted base:** `8ae941a1f5c4f07177b2e80272e582f8690dd747` (merged PR #89)
**Bounded step:** Russian-data integration Step 8 — recipe-dependency food batch
**Runtime/data publication authorized by this document:** no — review/merge this gate first

## 1. Goal

Step 8 publishes the smallest exact Russian food dependency that unlocks one
source-backed, deterministically calculable Step 9 `RecipeVersion` without
inventing food form, yield, retention, nutrient values or source authority.

The selected vertical slice is:

```text
School2022 source recipe 53-19з — «Масло сливочное (порциями)»
→ exact source-required butter form
→ licensed FIC RU-NUT-DB food record
→ exact FoodIngredient
→ non-current RU_NUTRIENT_REGISTRY_V2 profile/vector
→ ATOMIC Composition
→ Step 9 executable source RecipeVersion
```

Step 8 is a food-publication operation only. It does not publish the recipe.

## 2. FACT — sequencing and accepted prerequisites

The user-approved Russian-data integration sequence remains:

```text
Step 7 transformation applicability
→ Step 8 recipe-dependency food batch
→ Step 9 executable Russian RecipeVersion
→ Step 10 Planner integration
```

PR89 merged Step 7 runtime into `main` at
`8ae941a1f5c4f07177b2e80272e582f8690dd747`.

Accepted main therefore already contains:

- `RU_NUTRIENT_REGISTRY_V2`;
- the reviewed transactional Step 3 nutrition/ATOMIC publication seam;
- the licensed RU-NUT-DB Step 4 publication precedent;
- the reviewed Russian reference/methodology work from Steps 5–6;
- Step 7 applicability-aware transformed calculation infrastructure;
- migration head `0038_transformation_applicability`.

Reserved `0033_recipe_template_catalogue` remains unconsumed.

## 3. DECISION — select one concrete Step 9 target before publishing food

Step 8 is coverage-driven. It must not add unrelated catalogue rows merely
because an authoritative source contains them.

The selected future Step 9 target is the exact School2022 source card:

```text
source_id: ru-school2022
recipe_id: ru-school2022:recipe:53-19з
source_recipe_code: 53-19з
title: Масло сливочное (порциями)
scope: 7–11 years institutional school catering
PDF page: 18
```

The source card has exactly one food dependency: `масло сливочное`.

The route was selected because it gives a source-backed vertical slice with one
food dependency and no nutrition-altering culinary transformation.

This is a technical/data vertical slice, not a Planner-default recommendation.

## 4. FACT — School2022 source identity

Pinned School2022 source:

```text
title:
Сборник рецептур блюд и типовых меню для организации питания обучающихся
1—4-х классов в общеобразовательных организациях

publisher:
Федеральный центр гигиены и эпидемиологии Роспотребнадзора

year: 2022
PDF pages: 276
PDF SHA-256:
c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d
```

The source is authoritative for the selected institutional recipe/form/process
facts used by this gate. Its published nutrient calculations are not made primary
food-composition authority by Step 8.

## 5. FACT — exact recipe form and process evidence

School2022 introduction §1.4 states that recipe input norms use standard raw
material including:

```text
масло сливочное 72,5 % жирности
```

The selected recipe 53-19з records:

```text
масло сливочное: gross 10 g / net 10 g
thermal treatment: none
process: portion/cut and refrigerated holding before service
serving temperature: 14 °C
```

Therefore this selected recipe does not require a production yield or retention
coefficient to calculate its butter nutrient input.

School2022 procurement-quality evidence, PDF page 261, additionally states that:

- butter must be unsalted;
- butter may be traditional, amateur or peasant class;
- peasant-class butter has fat mass fraction at least 72.5%.

**FACT:** the earlier DC2 review correctly blocked the butter group because the
72.5% requirement was known but salinity had not yet been closed in that review.

**FACT:** the complete retained School2022 source package now contains explicit
unsalted-butter evidence.

## 6. FACT — the existing generic butter identity is not exact enough

Current catalogue truth includes:

```text
BUTTER_UNSALTED
Масло сливочное несолёное
```

with an existing USDA FDC SR Legacy current profile:

```text
source_id: 173430
source description: Butter, without salt
fat: 81.11 g / 100 g
```

That identity/profile must not be silently reinterpreted as School2022 72.5%
butter.

A narrow 72.5% FIC profile attached to generic `BUTTER_UNSALTED` would collapse
a materially different source form into an accepted broader identity.

## 7. DECISION — create a source-faithful butter FoodIngredient

Step 8 freezes one new canonical identity:

```text
canonical_code:
BUTTER_PEASANT_72_5_UNSALTED

canonical_name_ru:
Масло сливочное крестьянское 72,5% несолёное

category_code:
fats_oils

default_unit:
g

density_g_per_ml:
null

edible_fraction:
null

allergens_reviewed:
false

allergen_codes:
[]

storage_profile_code:
null

is_active:
true
```

Publication action:

`CREATE_REVIEWED`.

No allergen, density, edible-fraction or storage fact is inferred from the food
name. Those remain explicitly unreviewed/unknown in this bounded operation.

The identity combines:

- School2022 exact recipe standard: butter 72.5% fat;
- School2022 procurement requirement: unsalted;
- School2022 quality class: peasant-class threshold at 72.5%;
- FIC exact food-composition record: peasant butter, 72.5%;
- the same FIC DB/533 record's source field `salt_ad = 0.0`, whose frozen
  source label is `Добавленная соль`.

For this bounded identity, `UNSALTED` means **no added salt in the selected
source form**, not zero sodium and not analytical absence of sodium or chloride.
The binding is accepted only because the recipe source requires unsalted butter
and the exact FIC numeric-authority row independently publishes zero added salt.

Existing `BUTTER_UNSALTED` and its USDA profile/history remain unchanged.

## 8. FACT — licensed FIC numeric authority

The accepted FIC authority receipt remains:

`docs/family-food/fic-nutrition-license-receipt.md`.

Durable source artifact:

```text
private-library:/FamilyFoodOS/source-artifacts/
FamilyFoodOS-corpus-0.3.0-2026-09-20.zip

bytes:
206692075

SHA-256:
c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea
```

Pinned official RU-NUT-DB snapshot:

```text
source_name: FIC_RU_NUT_DB
source_id: RU-NUT-DB
source_version: snapshot-2026-09-20-155107ddb381c147
captured_date: 2026-09-20
raw HTML SHA-256:
155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d
rows: 3216
```

Exact selected record:

```text
DB index: 533
JSON pointer: /DB/533
source code: 1417
source name: Масло сливочное крестьянское, 72,5%

exact raw JSON-object SHA-256:
b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d
```

Independent corpus integrity review records this row as structurally clean with
no structural flags and corroborates all 29 shared fields against a second
official same-publisher interface.

### 8.1. FACT / DECISION — exact unsalted form binding

The selected FIC DB/533 record contains:

```text
source field: salt_ad
frozen source label: Добавленная соль
source literal: 0.0
Step 4 semantic disposition: SOURCE_ONLY_NO_V2_TARGET
```

The frozen Step 4 source-field contract does **not** publish `salt_ad` as a
canonical V2 nutrient. Step 8 keeps that rule unchanged.

**DECISION:** for this exact food/form mapping only, `salt_ad = 0.0` is accepted
as source-owned **form-compatibility evidence** that DB/533 represents butter
with no added salt. Together with School2022's explicit unsalted procurement
requirement and the exact 72.5% peasant-class match, this closes the
`UNSALTED ↔ FIC DB/533` binding.

This decision does not mean:

- sodium must be zero;
- low sodium proves unsalted form;
- `salt_ad` becomes a canonical nutrient;
- a zero in another FIC record automatically grants an unsalted identity;
- missing/null `salt_ad` may be treated as zero;
- the same form decision may be inherited by another source record without
  separate review.

Step 8 runtime must pin the exact source literal `0.0` in the reviewed package.
Changed, non-zero, null or missing `salt_ad` fails closed before publication.

## 9. DECISION — source authority remains separated by responsibility

Step 8 does not merge School2022 and FIC numeric tables.

Authority is split explicitly:

```text
School2022
→ recipe dependency identity
→ required 72.5% form
→ unsalted applicability
→ gross/net quantity
→ no-thermal-treatment process fact

FIC RU-NUT-DB / DB/533
→ production numeric food-composition authority
→ V2 nutrient values
→ source provenance
→ source-only salt_ad=0.0 form-compatibility evidence
```

School2022 published nutrient totals are reference/cross-check evidence only and
do not populate the production food vector.

Book2002 and legacy tables provide no production numeric authority in Step 8.

## 10. FACT — accepted FIC field semantics can be reused

Step 4 already froze the RU-NUT-DB source-field semantic mapping:

`data/curation/ru-nut-db-step4-semantic-closure/field-mapping.json`

SHA-256:

`bf77239d5976e5ec03d01f524726f9c2e8afb5fc4d92a884b62aa63dfe3a9477`.

That contract has 26 reviewed source nutrient fields and 18 fields whose
source concept/unit/method is approved for V2 publication when the source record
actually publishes a numeric value.

Step 8 reuses those semantic decisions. It does not reinterpret the historical
Step 4 batch-count metadata as facts about the butter row.

## 11. FACT — DB/533 has one explicit missing approved source field

The exact FIC DB/533 record publishes numeric literals for 25 of the 26 reviewed
source nutrient fields.

Its `water` field is:

`null`.

The accepted field mapping recognizes `water → WATER` as an exact concept when a
numeric source value exists. But this record does not publish such a value.

**DECISION:** Step 8 must preserve this distinction.

It must not:

- coerce `null` to zero;
- infer water by difference;
- copy water from another butter record;
- densify the V2 vector with an invented value.

## 12. DECISION — exact Step 8 V2 vector is sparse with 17 values

For DB/533, the existing 18 approved mapping fields yield exactly **17 persisted
V2 nutrient values**, because `WATER` is not reported.

Expected V2 codes:

```text
ENERGY_KCAL
PROTEIN
FAT_TOTAL
FATTY_ACIDS_SATURATED_TOTAL
STARCH
SUGARS_TOTAL
FIBER_TOTAL_DIETARY
VITAMIN_A_RE
THIAMIN
RIBOFLAVIN
VITAMIN_C
SODIUM
POTASSIUM
CALCIUM
PHOSPHORUS
IRON
MAGNESIUM
```

The source observation envelope must retain all 26 reviewed source fields:

- 25 published numeric source fields;
- 1 explicit not-reported/null field: `water`.

The eight source fields already deferred by the Step 4 semantic contract remain
source-only/deferred and do not become canonical V2 values.

One of those deferred/source-only fields, `salt_ad`, additionally carries the
reviewed Step 8 form-compatibility role from §8.1. Its numeric source literal is
retained as evidence but still does not enter the V2 nutrient vector.

Unknown stays unknown.

## 13. DECISION — profile and ATOMIC publication shape

Expected publication bundle:

```text
FoodIngredient
BUTTER_PEASANT_72_5_UNSALTED
    ↓
FoodNutritionProfile
source_name = FIC_RU_NUT_DB
source_id = 1417
source_version = snapshot-2026-09-20-155107ddb381c147
source_data_type = official_electronic_database_snapshot
basis = 100 g
verified_at = 2026-09-24T00:00:00Z
estimated = null
is_current = false
    ↓
RU_NUTRIENT_REGISTRY_V2 NutrientVector
value_count = 17
WATER absent/unknown
    ↓
FoodCompositionVersion
kind = ATOMIC
version = 1
input_state = INPUT
```

The legacy profile fields use source values where their meaning is already
accepted:

- energy: 660.9 kcal;
- protein: 0.8 g;
- fat: 72.5 g;
- fiber: published numeric 0;
- legacy carbohydrates: remain null because FIC `carbh` is still definition
  ambiguous under the accepted mapping contract.

The corresponding carbohydrates source observation remains
method/definition-incompatible rather than invented.

## 14. DECISION — no FoodTransformation is published for this vertical slice

Recipe 53-19з explicitly says there is no thermal treatment and publishes
gross = net = 10 g.

Step 8 therefore publishes:

- zero new `YieldModel` rows;
- zero new `NutrientRetentionProfile` rows;
- zero new `FoodTransformation` rows;
- zero new `TransformationApplicability` rows.

Cutting/portioning/refrigerated holding is Step 9 recipe process truth. It is not
converted into a nutrition-changing transformation merely to exercise Step 7.

## 15. DECISION — reuse the accepted publication infrastructure

Step 8 must reuse the existing reviewed Step 3/Step 4 publication boundary:

`ReviewedNutritionPublicationService` /
`ReviewedNutritionBatchPublicationService`.

Expected implementation is a narrow hash-pinned Step 8 source package/loader,
not a generalized ingestion framework.

Expected shape may include:

- `data/curation/ru-nut-db-step8-butter-runtime/README.md`;
- `publication.json`;
- package checksums/verification receipt;
- a narrow seed/publication adapter such as
  `backend/app/seed/ru_nut_db_step8_butter.py`;
- focused production-publication tests.

The generic Step 3 publication service should not need semantic changes merely
to publish a sparse 17-value vector.

If implementation proves shared publication semantics must change, stop and
review that change explicitly before widening the PR.

## 16. DECISION — no schema migration is expected

Step 8 is expected to require:

- no new table;
- no rebuild;
- no migration;
- no use of reserved `0033`;
- no change to migration head `0038`.

Current models already represent:

- exact FoodIngredient identity;
- partial/non-current profiles;
- sparse sealed V2 vectors;
- ATOMIC Composition.

If implementation proves this false, **STOP and amend this Contract Gate before
runtime/data implementation**.

## 17. Replay, conflict and transaction semantics

Fresh publication:

```text
reviewed source package
→ create exact FoodIngredient
→ create non-current source profile
→ source observations
→ seal exact 17-value V2 vector
→ publish ATOMIC v1
→ verify complete bundle
→ commit once
```

Exact replay:

- zero new FoodIngredient/profile/value/seal/composition writes;
- stable persisted identities;
- exact source/profile/vector/composition equality.

Conflict:

- an existing same canonical code with different identity facts fails closed;
- an occupied ATOMIC v1 slot with different snapshot fails closed;
- changed FIC row/hash/package fails before publication;
- changed field mapping or attribution fails closed;
- `salt_ad` changed from exact source literal `0.0`, or made null/missing,
  fails before publication;
- partial prior bundle is not silently completed as though it were exact replay.

Failure after any attempted Step 8 write must roll back the whole attempted
bundle under the existing project UoW.

## 18. Preservation matrix

| Accepted truth | Step 8 requirement |
| --- | --- |
| migrations 0001–0038 | unchanged |
| reserved 0033 | unchanged / unconsumed |
| V1 nutrient registry/vectors | unchanged |
| RU_NUTRIENT_REGISTRY_V2 | unchanged |
| Step 4 five FIC foods | byte/semantic history unchanged |
| BUTTER_UNSALTED | unchanged |
| USDA FDC 173430 current profile | remains current for BUTTER_UNSALTED |
| Step 5 reference table | unchanged |
| Step 6 methodology selections/pins | unchanged |
| Step 7 transformations/applicability | unchanged |
| Planner/API/UI defaults | unchanged |
| production RecipeVersions | no Step 9 row in this PR |
| AI_ENABLED=false | supported |

## 19. Why the one-food batch is intentionally small

DATA-CORPUS-V1 gives ~25–60 foods only as normal batch guidance; evidence
complexity and usefulness own the actual size.

This batch is intentionally one food because it closes one complete, low-risk
vertical dependency chain for the immediately following Step 9 operation.

Publishing additional FIC rows in the same PR would add catalogue scope without
being required to prove the Step 8 → Step 9 path.

## 20. Rejected immediate alternative — boiled egg

School2022 recipe `54-6о — Яйцо вареное` also has one food dependency, but it is
not selected.

Reasons:

- the source includes an 8–10 minute boiling transformation;
- Step 7 intentionally published no production retention coefficients;
- the retained FIC cooked-egg candidate is quarantined by source-integrity review
  for column alignment and is not approved for macro calculation;
- using raw egg composition as cooked egg truth would violate mass/form/process
  semantics.

Step 8 therefore does not select the superficially similar one-food route when
doing so would hide transformation uncertainty.

## 21. Adversarial acceptance tests frozen by this gate

Step 8 runtime/data publication must prove at least:

1. accepted main starts at migration head 0038;
2. reserved 0033 remains unconsumed;
3. source archive size/hash matches the durable receipt;
4. School2022 PDF hash matches the pinned source;
5. exact target recipe identity is 53-19з;
6. target recipe dependency is exactly the selected butter form;
7. source §1.4 establishes 72.5% butter;
8. procurement evidence establishes unsalted applicability;
9. selected FIC record is exactly code 1417 / DB/533;
10. exact FIC raw record hash matches;
11. source same-publisher corroboration does not change the primary source identity;
12. generic `BUTTER_UNSALTED` is not reused for the 72.5% profile;
13. new canonical butter identity is exact and Russian display text is preserved;
14. existing `BUTTER_UNSALTED` row is unchanged;
15. existing USDA FDC 173430 profile/history is unchanged;
16. FIC license receipt, attribution and source link are pinned;
17. the accepted FIC semantic mapping hash is pinned;
18. all 26 reviewed FIC source fields are accounted for;
19. exact DB/533 `salt_ad` source literal is `0.0`;
20. `salt_ad` remains source-only / no V2 target;
21. non-zero `salt_ad` is rejected for the frozen unsalted identity;
22. null/missing `salt_ad` is rejected rather than treated as zero;
23. sodium amount is never used to infer unsalted form;
24. `water = null` remains explicit not-reported evidence;
25. no WATER nutrient value is invented;
26. exactly 17 V2 nutrient values are sealed;
27. the eight already-deferred source concepts remain non-canonical;
28. published numeric zero remains numeric zero where the source reports zero;
29. legacy carbohydrates remain null/method-incompatible;
30. source profile is non-current;
31. ATOMIC version is exactly v1 / INPUT;
32. no YieldModel/RetentionProfile/Transformation/Applicability row is created;
33. fresh publication succeeds atomically;
34. exact replay performs zero writes and preserves IDs;
35. identity/profile/vector/composition conflict fails closed;
36. source/package/mapping/form-evidence tamper fails before writes;
37. injected publication failure rolls back all attempted Step 8 state;
38. no production RecipeVersion is created;
39. no Planner/API/UI default changes occur;
40. Step 4 FIC publication regression remains green;
41. V2 vector/partial-profile regression remains green;
42. AI is not involved.

## 22. Verification tier

Step 8 is bounded authoritative data publication over accepted runtime.

Required review-ready evidence:

- exact source archive/hash retrieval receipt;
- exact School2022 target/form/process evidence check;
- exact FIC DB/533 record/hash check;
- exact `salt_ad=0.0` form-compatibility evidence check;
- adversarial non-zero/null/missing salt evidence rejection;
- FIC rights/attribution check;
- field-accounting / 17-value vector audit;
- fresh publication;
- exact replay / zero-write;
- conflict and failure rollback;
- immutable existing butter/profile history;
- Step 3/Step 4 publication regression;
- V2 NutrientVector / partial-profile affected regression;
- ATOMIC Composition read/calculation check;
- migration head/0033 preservation;
- `AI_ENABLED=false`;
- Docs/DC1;
- exact-head scope/whitespace audit.

A full backend/launcher regression is not required merely because the batch
contains production data. It becomes required if shared persistence/publication/
startup runtime bytes change or a concrete failure broadens the risk surface.

## 23. Step 9 handoff contract

After Step 8 runtime/data publication is reviewed and merged, stop.

The next separate Step 9 operation may then publish the exact source
`RecipeVersion` for School2022 53-19з using:

- the source recipe/card identity;
- exact 10 g net butter quantity;
- the Step 8 ATOMIC composition identity;
- source process text;
- deterministic nutrition from FamilyFoodOS composition truth.

Step 9 must separately validate its own recipe-source rights/publication,
RecipeVersion persistence contract, Russian display and deterministic Nutrition.

Step 8 does not pre-approve Step 9 publication.

## 24. Explicit non-goals

Step 8 does not authorize:

- any other recipe-dependency food;
- the boiled-egg route;
- bulk FIC catalogue publication;
- Book2002 numeric publication;
- School2022 calculated nutrient values as food authority;
- a new retention/yield package;
- a generalized ingestion platform;
- Step 9 RecipeVersion publication;
- Step 10 Planner integration;
- Planner default eligibility;
- RetailSKU/market availability/prices;
- allergen inference not supported by reviewed authority;
- API/UI;
- Auth/PostgreSQL;
- AI authority.

## 25. Stop boundary

This PR is the Step 8 Contract Gate only.

No production FoodIngredient/profile/vector/Composition row, runtime seed,
migration, RecipeVersion or Planner change belongs in this gate PR.

After gate review/merge:

1. stop;
2. Step 8 runtime/data publication requires separate explicit authorization;
3. after Step 8 runtime review/merge, stop before Step 9.
