# Step 5 — Reviewed Russian Reference Table Contract

**Status:** Implementation Contract Gate / adversarial preflight
**Accepted base:** `aa5ebcb4c70c9adee0fd1242f520ef1298f6b167` (merged PR #82)
**Bounded step:** Russian-data integration Step 5
**Runtime implementation authorized by this document:** no — merge/review this gate first

## 1. Goal

Publish the first production-reviewed Russian **population group reference table**
for the already implemented explicit Russian reference-selection path.

The table is:

- a versioned group-reference catalogue;
- deterministic;
- source/provenance preserving;
- non-personalized;
- not a prescription;
- not a replacement for the existing NASEM personalized v1 path;
- not a Planner/API/UI default.

This step does **not** persist a household/member methodology selection. That is
the next separately gated step.

## 2. Source authority and freshness

Primary source:

`МР 2.3.1.0253-21 — Нормы физиологических потребностей в энергии и пищевых веществах для различных групп населения Российской Федерации`.

Source identity:

```text
source_id = RU-NEEDS-MR-2.3.1.0253-21
document_number = МР 2.3.1.0253-21
edition_date = 2021-07-22
publisher/institution = Роспотребнадзор
official PDF SHA-256 =
cf96c7ea7fab087d16b478b2c8c097406d7572e495b2beb43405e4fd05917d79
```

Pinned corpus package:

`FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

Archive SHA-256:

`c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`.

The corpus classifies the source as
`OFFICIAL_DOCUMENT_FACTUAL_DATA`. Step 5 republishes only a bounded set of
reviewed factual scalar reference values with provenance; it does not republish
the source PDF or expressive text.

A current-source check performed on 2026-09-22 found a Rospotrebnadzor publication
dated 2025-08-22 still explicitly using МР 2.3.1.0253-21 as the reference for
physiological energy/nutrient needs. This supports operational relevance but is
not a claim of independent legal-currentness certification.

Official source URLs retained by the project:

- FIC copy of the official PDF:
  `https://ion.ru/upload/medialibrary/e70/xq18hm3mm1f1b3izde8kcb5136l8373z/Нормы%20физиологических%20потребностей%202021.pdf`;
- 2025 Rospotrebnadzor reference check:
  `https://77.rospotrebnadzor.ru/index.php/press-centr/press-relizy/14564-potrebnost-organizma-v-energii-i-pishchevykh-veshchestvakh-22-08-2025`.

## 3. FACT — source transport package

The supplied corpus already contains an independently QA-checked source transport
package:

`packages/population-reference/`.

Pinned inputs:

```text
research/normalized/population-needs-all.jsonl
SHA-256 = 8e68a6f3450f40c52c44bc422c6ecfad9e8bfa6561041948529c391211df7bdf

inventory-qa/population-transport-qa.json
SHA-256 = 2404b044cc48ef56abc03653c10d3fc192cb9e6a6ae76a7f869c6c5c51a42445
```

Normalized package hashes:

```text
groups.jsonl    8101fabce928d2033cc831ff4984502b6068b305e0c330b8ff53b3d5d146341e
nutrients.jsonl bf29e392b548600499de90effa9a46660fa928c6eb867bc8a7bfe35c9f61d031
values.jsonl    ff9b21599797355ca47af6af5db9e920705cfa233cdaecd173d0c0a07cbf4b3f
quality.json    51736ca640e3295fca00fc4011f1cb70fe1c4ef768b320e9c050bf484108d566
validation.json 931e1e4a2e92190b1d4c651d65eaf93dd9b7274fe66ed84658b0bcdbd2677894
manifest.json   cff02f7e5b17ff00bed32ae79d6bc033f9ba83a10cf33170a761a0b623ae4154
```

Package accounting:

```text
source groups                  147
source nutrient row identities 218
source claims                  872
scalar source-group lookups    735
withheld source claims         137
individual prescriptions ready   0
```

The package intentionally has `runtime_authorized=false`: exact source transport
is evidence, not production publication authority. Step 5 adds the explicit
FamilyFoodOS review/mapping layer.

## 4. DECISION — first production table is deliberately narrower

Do **not** publish all 735 scalar source-group lookups.

The first table is an **adult scalar micronutrient reference table** built only
from source tables:

- table 11 — vitamins, men;
- table 12 — minerals, men;
- table 16 — vitamins, women;
- table 17 — minerals, women.

Only source claims with corpus status
`ready_source_group_lookup` may enter the Step 5 table.

The initial table contains exactly:

```text
24 canonical definitions × 2 sexes = 48 rows
```

No numeric value is published by this docs-only gate.

## 5. DECISION — table identity

Freeze:

```text
methodology_version =
RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1

table_review_reference =
STEP5_RU_REFERENCE_TABLE_V1
```

Every runtime row must retain:

- stable FamilyFoodOS row id;
- source id;
- source edition/version;
- exact source claim id;
- PDF page/table/row/column locator;
- review reference;
- canonical definition code;
- canonical daily unit;
- exact Decimal source value;
- sex;
- age interval;
- physical-activity applicability;
- life stage;
- basis/applicability.

## 6. DECISION — applicability

The selected source tables say `Старше 18 лет`.

The selector uses completed chronological years.

Source-faithful translation is:

```text
age_min_years = 19
age_max_years_exclusive = null
life_stage = adult
sex = male | female
physical_activity_coefficient = null
basis = group_reference_daily
applicability = wellness
individualized = false
```

There is **no age-18 fallback**.

`physical_activity_coefficient = null` means the selected micronutrient row is
source-independent of KFA. It does not mean a missing KFA was inferred.

No source `sex=null` group is converted to `sex=all`.

## 7. DECISION — exact 24 definition mappings

The following source labels are approved for the first table:

| Source definition | Canonical definition code | Canonical unit |
| --- | --- | --- |
| Витамин С | `VITAMIN_C` | mg/day |
| Витамин B1 | `THIAMIN` | mg/day |
| Витамин B2 | `RIBOFLAVIN` | mg/day |
| Витамин B6 | `VITAMIN_B6` | mg/day |
| Ниацин, ниациновый эквивалент | `NIACIN_EQUIVALENT` | mg/day |
| Витамин B12 | `VITAMIN_B12` | µg/day |
| Пантотеновая кислота | `PANTOTHENIC_ACID` | mg/day |
| Биотин | `BIOTIN` | µg/day |
| Витамин А, ретиноловый эквивалент | `VITAMIN_A_RE` | µg/day |
| Бета-каротин | `BETA_CAROTENE` | mg/day |
| Витамин Е, токофероловый эквивалент | `VITAMIN_E_TOCOPHEROL_EQUIVALENT` | mg/day |
| Фосфор | `PHOSPHORUS` | mg/day |
| Магний | `MAGNESIUM` | mg/day |
| Калий | `POTASSIUM` | mg/day |
| Натрий | `SODIUM` | mg/day |
| Хлориды | `CHLORIDE` | mg/day |
| Железо | `IRON` | mg/day |
| Цинк | `ZINC` | mg/day |
| Йод | `IODINE` | µg/day |
| Медь | `COPPER` | mg/day |
| Марганец | `MANGANESE` | mg/day |
| Молибден | `MOLYBDENUM` | µg/day |
| Селен | `SELENIUM` | µg/day |
| Хром | `CHROMIUM` | µg/day |

The mapping is definition-sensitive. Equal units never establish nutrient
equivalence.

## 8. DECISION — explicit deferrals

### 8.1 Tables 9 and 14 — energy/macronutrient grams

Do not publish them in V1 of this table.

Reason:

- the source contains a Far-North adjustment footnote (+15% energy expenditure
  with proportional macro changes);
- the current `RussianReferenceRow` has no geography/occupational applicability
  dimension;
- publishing the base row as universally applicable would hide a source condition;
- dietary fibre is a non-scalar source range in these tables.

A later contract may add exact applicability rather than silently generalize.

### 8.2 Tables 10 and 15 — percent-energy references

Do not publish them in this table.

Reasons:

- percent-energy values are not directly comparable through the current
  `compare_daily_reference` daily-amount path;
- several rows are ranges/bounds rather than scalar values;
- the current table-overlap contract must not use one nutrient definition code
  simultaneously as two incompatible target dimensions without an explicit
  design.

### 8.3 Tables 13 and 18 — adequate levels

Do not publish them in Step 5 V1.

The corpus preserves these rows with `adequate_level=true`. The current
`RussianReferenceRow` does not carry a reference-kind dimension that can
distinguish an adequate intake level from the ordinary scalar group-reference
rows in tables 11/12/16/17.

Publishing `Фтор → FLUORIDE` from these tables would therefore erase a
source-owned semantic distinction.

**DECISION:** tables 13/18 are deferred in their entirety. Do not add a new
domain field in this gate; a later bounded contract may introduce explicit
reference-kind semantics and then review adequate-level rows.

### 8.4 Source claims withheld by the corpus

Do not override `withheld` claims in Step 5 V1.

In particular:

- Vitamin D base rows are withheld because an age >65 footnote changes the value;
- Calcium base rows are withheld because an age >65 footnote changes the value;
- B1/B2/niacin per-1000-kcal expressions are non-scalar source expressions.

A future contract may model their applicability explicitly.

### 8.5 Definition mismatch / unavailable V2 target

Do not publish:

- `Фолаты`: the source table/reference convention is not silently equated with
  `FOLATE_TOTAL` or `FOLATE_DFE`;
- `Витамин D`: the source definition is broader than V2
  `VITAMIN_D_D2_D3`;
- `Витамин К`: the source explicitly covers phylloquinone + menaquinones,
  while V2 `VITAMIN_K_PHYLLOQUINONE` is K1 only;
- cobalt, silicon and vanadium: no approved V2 canonical target exists;
- fluoride: V2 has `FLUORIDE`, but the available adult source row is in
  adequate-level tables 13/18, which are deferred until reference-kind semantics
  are explicit.

## 9. Existing domain/service contract to reuse

Already implemented:

- `RussianReferenceRow`;
- `ReviewedRussianReferenceTable`;
- `select_russian_reference_targets(...)`;
- `NutritionService.russian_member_group_reference(...)`;
- `compare_daily_reference(...)`.

The existing selector already enforces:

- completed-year interval;
- exact sex;
- exact KFA when a row has KFA;
- life stage;
- no overlapping applicable rows;
- no NASEM activity mapping;
- no interpolation;
- non-individualized result.

Do not create a second reference-table domain model.

## 10. Runtime implementation contract after gate merge

The subsequent runtime PR must:

1. add a hash-pinned repository curation package for exactly the 50 reviewed rows;
2. validate the source package hashes and exact source-claim identities;
3. parse all numeric values as `Decimal`, never float;
4. construct one immutable
   `ReviewedRussianReferenceTable` for the frozen methodology version;
5. expose it through the existing controlled table-provider boundary;
6. keep unknown methodology versions unavailable/fail-closed;
7. preserve the existing NASEM `member_reference_target` path unchanged;
8. keep Russian selection explicit — no API/Planner/default switch;
9. add no database table and no migration.

Source/corpus parsing and checksum verification must stay outside the pure domain
types. `NutritionService` receives only the reviewed typed table provider.

## 11. Fresh / replay / conflict semantics

This Step 5 table is repository-owned immutable catalogue data, not DB state.

### Fresh load

A valid package produces exactly one table:

`RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1`

with exactly 48 rows.

### Exact replay

Loading the same pinned bytes produces an equal table and stable deterministic
table digest/receipt. No database write occurs.

### Conflict / fail-closed

Reject before provider availability if any of the following changes:

- package/file checksum;
- source PDF/input/QA hash;
- expected row count;
- source claim id/locator;
- source status is not `ready_source_group_lookup`;
- source definition mapping;
- unit;
- value;
- sex;
- age applicability;
- life stage;
- duplicate/overlapping row;
- methodology version;
- review reference.

No automatic repair, fallback, row dropping or alternate-source substitution.

## 12. Preservation matrix

| Existing truth | Step 5 requirement |
| --- | --- |
| NASEM personalized v1 target path | unchanged |
| Russian selector domain behavior | reused, not weakened |
| Russian methodology calculations | unchanged |
| V1/V2 food nutrient vectors | unchanged |
| Step 4 FIC profiles/compositions | unchanged |
| Household/member persistence | unchanged |
| Planner methodology/defaults | unchanged |
| API/UI | unchanged |
| migration head | unchanged |

## 13. Adversarial acceptance tests for runtime PR

The runtime PR must prove at least:

1. exact source-package hashes accepted;
2. tampered source/table package rejected before table creation;
3. exactly 48 rows / 24 definitions × 2 sexes;
4. only tables 11/12 and 16/17 contribute rows;
5. every source claim is `ready_source_group_lookup`;
6. every row has exact source claim locator/provenance;
7. all numeric values are exact `Decimal`;
8. male/female rows are distinct and no null-sex→all coercion occurs;
9. source `Старше 18 лет` maps to completed age 19+; age 18 is unsupported;
10. KFA-independent rows work with explicit caller KFA without changing the row;
11. Vitamin D and Calcium footnote rows are absent;
12. folate / Vitamin K / fluoride / cobalt / silicon / vanadium rows are absent;
13. no table 9/10/13/14/15/18 value is present;
14. duplicate/overlapping rows fail table construction;
15. wrong methodology version does not fall back;
16. existing NASEM service remains unchanged;
17. explicit Russian service selection returns `individualized=false`;
18. exact replay returns byte/digest-equivalent table truth;
19. no DB write/migration occurs;
20. AI is not used.

## 14. Verification tier

### Contract Gate PR

Docs/state only:

- diff/whitespace;
- links;
- source/hash consistency;
- stale-state audit;
- no runtime/data numeric publication.

### Runtime PR

Required:

- focused reference-table loader/provider tests;
- `test_russian_reference_targets.py`;
- `test_russian_reference_service.py`;
- `test_reference_comparison.py`;
- Russian nutrition methodologies workflow;
- Nutrient Registry V2 compatibility checks;
- data-package checksum/adversarial checks;
- broader backend/launcher only if shared composition/startup wiring changes.

## 15. Non-goals

Step 5 does not authorize:

- persisted methodology selection;
- default Russian methodology for Household/Planner;
- personal prescription claims;
- children;
- pregnancy/lactation;
- clinical targets;
- regional/Far-North adjustment;
- percent-energy planning targets;
- inequalities/ranges;
- age interpolation;
- KFA inference from activity labels;
- NASEM→Russian conversion;
- API/UI;
- schema/migration;
- Step 6+.

## 16. Stop boundary

Merge/review this Contract Gate before any numeric Step 5 runtime package is
committed.

After the gate is merged, runtime implementation requires the user's separate
authorization under this contract.

After runtime Step 5 is merged, do not automatically start persisted methodology
selection.
