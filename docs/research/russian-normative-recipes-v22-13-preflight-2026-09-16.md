# Russian normative recipes v22.13 — FamilyFoodOS integration preflight

**Status:** research/evidence preflight; no production publication  
**Reviewed:** 2026-09-16  
**Repository base:** `38de460dfcbf84997a1d9275314c4f3dab7e1d00` (PR #37 merged)  
**Operation:** `V22-13-DATA-INTEGRATION-PREFLIGHT`

## 1. Purpose

This document evaluates the external checkpoint
`russian_normative_recipes_v22_13_checkpoint.zip` against the current
FamilyFoodOS repository contracts before any attempt to import or publish its
contents.

The preflight answers four questions:

1. what parts of the package may be adopted as evidence/reference material;
2. what must be mapped to existing FamilyFoodOS identities and authorities;
3. what still requires review before it can affect deterministic production
   truth;
4. whether the package closes any currently open Recipe Assembly A evidence
   gates.

This operation is intentionally read-only with respect to runtime/domain data.
It does **not** create or modify `FoodIngredient`, Nutrition profiles,
RecipeVersion, RecipeTemplate, RecipeAssembly, migrations, production seeds or
accepted source-corpus rows.

## 2. Repository contracts used for the review

The package was checked against the accepted repository direction after PR #37,
including:

- `AGENTS.md`;
- `docs/family-food/architecture.md` and its 2026-09-13 addendum;
- `docs/family-food/master-roadmap.md` and its 2026-09-13 addendum;
- `docs/family-food/food-composition-and-assembly.md`;
- `docs/family-food/nutrition-core.md`;
- `docs/family-food/verification-policy.md`;
- `data/curation/recipe-assembly-a/README.md`;
- retained Recipe Assembly A R1/R2/R3/R4 evidence;
- the PR #36 Russian normative source corpus.

Important existing invariants remain unchanged:

```text
FoodIngredient = sole canonical food identity
raw/input/cooked mass and food forms are distinct
RecipeVersion/RecipeTemplate publication requires verifiable provenance
Nutrition/Composition truth is deterministic and versioned
missing/unknown critical facts do not become zero or guessed precision
AI_ENABLED=false must remain sufficient for the core
```

## 3. External package and integrity pins

The external package is not committed to the repository by this operation.
The following SHA-256 values pin the exact reviewed bytes.

| Artifact | SHA-256 |
| --- | --- |
| `russian_normative_recipes_v22_13_checkpoint.zip` | `a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97` |
| `russian_normative_recipes_v22_13_integrity_audit.xlsx` | `4353aec58e2610e3a9b4d46b970888cd17e1aabcd6ebea2af6ed0c323865d47f` |
| `russian_normative_recipes_v22_13_manifest.xlsx` | `f57eb053f11f6230ad733824dbf4d3bba523be13d9418c7ab0932e58046aa9f0` |
| `russian_normative_recipes_v22_13_mass_nutrients.xlsx` | `5ea78ead82568f8aff019a4076215c6598675783cb81e0d1d5b4f913016de4cc` |
| `russian_normative_recipes_v22_13_row_nutrients_part1.xlsx` | `49eb0e24055f4261e8b4664ecf4a4002a45a9182b8fd54067c24836cbcc811af` |
| `russian_normative_recipes_v22_13_row_nutrients_part2.xlsx` | `28672441274b21a4c36efcbc23507594aa8cc10fa4079c531606becdb4a14ec2` |
| `russian_normative_recipes_v22_13_row_nutrients_part3.xlsx` | `bba7f2011462e720aad77791b8c0838d1a15bccd0bc514dc406f8af200f77b1b` |
| `russian_normative_recipes_v22_13_row_nutrients_part4.xlsx` | `10dfa8a4fd21e0b6346740578b9515f053eb9f82b98403c2570ecc5ef63d121e` |

Each extracted workbook was byte-compared with its ZIP member during the
preflight; all seven workbooks matched.

## 4. FACT — package shape

The checkpoint is materially richer than a flat recipe list.

### 4.1 Recipe and row inventory

- recipes in `v22_RecipeCoverage`: **350**;
- ingredient contribution rows across the four row-nutrient shards: **6,179**;
- nutrient-input eligible contribution rows: **6,177**;
- ingredient/reference records in `v22_IngredientRefs`: **363**;
- scenario rows in `v22_ScenarioNutrients`: **479**;
- scenario status `READY`: **460**;
- scenario status `PARTIAL`: **19**.

Recipe raw-readiness distribution:

| Status | Count |
| --- | ---: |
| `READY_RAW` | 292 |
| `PARTIAL_RAW` | 53 |
| `NO_RELATIONSHIPS` | 4 |
| `NO_CALC_INPUTS` | 1 |

`READY_RAW` is the package's raw/reference completeness status. It is **not** a
FamilyFoodOS production-readiness status.

### 4.2 Nutrient scope

The checkpoint tracks 11 nutrient fields:

- Protein;
- Fat;
- Carbs;
- Kcal;
- Ca;
- Mg;
- P;
- Fe;
- B1;
- B2;
- VitC.

The checkpoint reports approximately:

- minimum row coverage: **97.7335%**;
- minimum total-mass coverage: **97.5583%**;
- minimum non-water mass coverage: **96.5740%**.

The package also reports:

- open ingredient/reference queue: **58**;
- open ingredient × nutrient gaps: **578**;
- profiles added/expanded in this checkpoint: **14**;
- patched contribution rows: **20**;
- structural split reclassifications: **3**.

### 4.3 Evidence-quality coverage is lower than numeric availability

The checkpoint distinguishes raw numeric coverage from stronger evidence
quality. Its strict A/B evidence-complete metrics are approximately:

- contribution rows: **4,629 / 6,179 = 74.94%**;
- contribution mass: **528,095.084 g = 67.91%** of the measured mass scope.

This distinction is important: high numeric coverage must not be interpreted as
uniform authoritative provenance.

## 5. FACT — reference-quality and unresolved debt

The 363 ingredient/reference records are explicitly stratified rather than being
presented as one homogeneous authority class.

| Exactness / reference tier | Count |
| --- | ---: |
| `A_REFERENCE` | 113 |
| `B_REFERENCE` | 13 |
| `B_MULTI_SOURCE_REFERENCE` | 28 |
| `B_PARTIAL_REFERENCE` | 15 |
| `B_COMPATIBLE_REFERENCE` | 4 |
| `A_INTERNAL_DERIVED` | 5 |
| `B_PROCESS_OUTPUT_REFERENCE` | 2 |
| `B_VARIANT_COMPONENT` | 1 |
| `C_PROXY` | 62 |
| `C_INTERNAL_NORMATIVE` | 7 |
| `C_INTERNAL_NORMATIVE_FAMILY` | 6 |
| `C_INTERNAL_VARIANT` | 2 |
| `UNRESOLVED` | 99 |
| `STRUCTURAL_PARENT` | 5 |
| `X_TECHNICAL` | 1 |

Profile availability in the package:

- `YES`: 255;
- `NO`: 106;
- `ROW_LEVEL_ONLY`: 2.

Important action classes include `RESOLVED`, `DIRECT_REFERENCE`,
`RESOLVED_RETENTION_PENDING`, `PROCESS_TRANSFER_REQUIRED`, `SPLIT_REQUIRED`,
`PARTIAL_PROFILE_GAP` and `COMPONENT_PROFILE_REQUIRED`.

**DECISION:** `C_PROXY`, `UNRESOLVED`, structural/process-dependent records and
partial profiles are review states, not production Nutrition authority.

## 6. FACT — mass/form/process semantics

The row layer retains process/form distinctions instead of flattening them.
Representative state-compatibility counts include:

- `RAW_OR_UNSPECIFIED_OK`: 5,970 rows;
- `COOKED_COMPONENT_RETENTION_PENDING`: 110 rows;
- `COOKED_STATE_REVIEW`: 47 rows;
- `COOKED_COMPONENT_REVIEW`: 24 rows;
- smaller explicit review/technical-output states.

The package-level semantic-issue summaries include:

| Issue | Rows | Mass / scope | Affected recipes / note |
| --- | ---: | ---: | --- |
| cooked-state review | 47 | 5,280 g | 19 recipes |
| cooked-component review | 24 | 1,448 g | 5 recipes |
| cooked-component retention pending | 112 | 14,495 g | 34 recipes |
| `SPLIT_REQUIRED` | 13 | 1,429 g | 7 recipes / 4 ambiguous parents |
| `PROCESS_TRANSFER_REQUIRED` | 27 | 11,872 g | 11 recipes / 8 open inputs |
| `COMPONENT_PROFILE_REQUIRED` | 12 | 1,725 g | 9 recipes / 7 blockers |

`v22_ProcessModels` keeps raw stock/bone/waste extraction inputs separate from
finished output profiles. The package does not back-propagate finished-output
nutrition into raw transfer inputs.

This is compatible with the FamilyFoodOS rule that a finished product profile
cannot silently become the authority for a raw/process input.

## 7. FACT — retention and output nutrition

The checkpoint contains explicit retention evidence for a small number of cases,
but every reviewed retention row is marked as **not applied to the numeric
layer**.

The manifest/checkpoint also states:

```text
retention coefficients applied = NO
process-dependent profiles assigned by food-table proxy = NO
```

The package policy additionally states that ambiguous or unreported source cells
remain `null` and are never silently converted to zero.

**DECISION:** this separation is useful evidence and should be preserved.
However, raw/reference scenario nutrition must not be imported as authoritative
cooked/serving nutrition until FamilyFoodOS transformation/yield/retention
requirements are satisfied.

## 8. FACT — source alternatives, optional roles and choice groups

The row layer contains useful structural evidence:

- rows explicitly marked optional: **41**;
- recipes containing optional rows: **13**;
- `READY_RAW` recipes containing optional rows: **7**;
- rows with `ChoiceGroup`: **1,665**;
- recipes with at least one `ChoiceGroup`: **171**;
- rows with amount status `verified_primary_alternative`: **1,682**.

Seven `READY_RAW` recipes with explicit optional rows include:

- `USSR82-251` — `Солянка домашняя`;
- `USSR82-267` — `Суп-пюре из моркови или репы`;
- `USSR82-309` — `Щи зеленые с яйцом`;
- `USSR82-310` — `Щи зеленые с мясом`;
- `USSR82-317` — `Суп из плодов или ягод сушеных`;
- `USSR82-369` — `Грибы в сметанном соусе`;
- `USSR82-671` — `Биточки паровые`.

This is useful candidate evidence for future template research.

**DECISION:** package terms such as `verified_primary_alternative` describe the
checkpoint's source/amount evidence. They do **not** automatically satisfy the
FamilyFoodOS `verified_substitution` gate. Existing Assembly A research already
establishes that a source-listed alternative does not prove that the substituted
variant was kitchen-tested and compatible in the required form/mass/composition
scope.

## 9. FACT — source lineage is not the existing PR #36 corpus

The accepted PR #36 source corpus is a distinct source family:

- source code `RU_MR_2_4_0162_19`;
- Rospotrebnadzor / Chief State Sanitary Doctor of the Russian Federation;
- `МР 2.4.0162-19`;
- 214 technological cards from appendices 5–8;
- preserved as pre-publication evidence/source material.

The uploaded v22.13 package instead uses recipe identifiers such as
`USSR82-*` and a different source/reference graph. The two datasets must not be
merged merely because both are Russian-language normative-recipe evidence.

Relationship-evidence rows in v22.13 are dominated by online publication/mirror
URLs, especially `studopedia.net` and `interdoka.ru`. Nutrition/profile evidence
is also mixed across several source families.

The package does not contain a FamilyFoodOS rights-clearance decision that would
permit direct RecipeVersion/RecipeTemplate publication.

**DECISION:** PR #36 source identity/provenance and v22.13 source identity remain
separate unless a later source-lineage review proves an exact relationship.

## 10. FACT — current FamilyFoodOS identity mismatch

The uploaded checkpoint has **363 external ingredient/reference identities**.
They are not FamilyFoodOS `FoodIngredient` identities.

Current repository food truth remains the existing `FoodIngredient` catalogue
and its versioned Nutrition/Composition contracts. Examples such as `POTATO`,
`CARROT`, `CABBAGE_GREEN`, `MILK_1_PERCENT`, `CRANBERRIES_DRIED`, cooked forms
and process outputs already demonstrate why name similarity is insufficient:
forms and calculation authorities may differ.

**DECISION:** no `ING-*`/external checkpoint identifier is promoted or copied as a
canonical `FoodIngredient` merely because a label looks familiar.

A later mapping operation must classify every external identity into an explicit
mapping state.

## 11. Data-readiness filter for further evidence review

For triage only, the preflight computed a deliberately stricter internal/raw
filter:

```text
READY_RAW
AND ProxyRows = 0
AND StateReviewRows = 0
AND UnresolvedIDs = empty
AND ReferenceCompleteRows = CalcRows
```

Exactly **64 recipes** pass this raw-data filter.

This is **not** a production-ready count. It does not establish rights,
FoodIngredient mapping, RU familiarity, kitchen verification, output yield,
retention, household scaling or RecipeTemplate rules.

A smaller triage subset also combines strong raw status with explicit choice
groups. Eight examples are:

- `USSR82-414` — `Каша вязкая с морковью`;
- `USSR82-374` — `Картофель, запеченный с яйцом и помидорами`;
- `USSR82-412` — `Каша вязкая с тыквой`;
- `USSR82-413` — `Каша вязкая с черносливом`;
- `USSR82-285` — `Овощи и яйца`;
- `USSR82-459` — `Яичница глазунья (натуральная)`;
- `USSR82-468` — `Омлет из яичного порошка`;
- `USSR82-451` — `Макаронник`.

These are **data-readiness leads only**, not approved RecipeTemplate families.

## 12. Package quality observations

The core data/integrity sheets are internally structured, but several presentation
artifacts should be normalized before any repository import:

- the main workbook README still labels the mass layer as `v22.12`;
- dashboard/coverage presentation contains stale duplicate v22.12 rows;
- a duplicate stale VitC summary is present in the presentation layer;
- some dashboard labels still refer to the previous checkpoint although the
  manifest/integrity sheets carry v22.13 values.

**DECISION:** these are treated as stale summary/presentation defects, not as
permission to rewrite underlying values. Any normalized import must retain the
exact source workbook hashes and document every correction/normalization step.

## 13. Integration classification

### ADOPT — safe as reference/evidence behavior

- pin the package and workbook hashes;
- preserve the checkpoint's explicit null/not-zero policy;
- preserve raw/process/retention separation;
- preserve row-level provenance and contribution structure;
- preserve explicit proxy/unresolved/review states;
- use recipe/ingredient/scenario coverage metrics for evidence triage;
- use the dataset as a candidate source for future Assembly A evidence review.

### MAP — useful only through FamilyFoodOS authorities

- map 363 external ingredient/reference identities to FamilyFoodOS
  `FoodIngredient` states;
- map 350 external recipe records to a pre-publication candidate/evidence layer,
  not directly to `RecipeVersion`;
- map nutrient/reference evidence to versioned candidate provenance without
  overwriting accepted Nutrition profiles;
- map cooked/process/component identities to FoodIngredient/composition/producer
  semantics only after form/process review;
- preserve external recipe/source IDs and row lineage for replay/audit.

### NEEDS_REVIEW — not authoritative yet

- 99 `UNRESOLVED` ingredient/reference rows;
- 62 `C_PROXY` rows;
- 58-item open reference queue;
- 578 ingredient × nutrient gaps;
- 15 semantic mapping pairs explicitly left for review;
- state/cooked/component review rows;
- `SPLIT_REQUIRED`, `PROCESS_TRANSFER_REQUIRED` and
  `COMPONENT_PROFILE_REQUIRED` records;
- all retention-pending outputs;
- source-lineage and rights/publication status;
- Russian consumer familiarity of candidate families;
- kitchen verification and household-scaling scope;
- exact substitution/compatibility evidence;
- mapping to existing FoodIngredient form identities and composition authority.

### REJECT — prohibited direct interpretations

The following must **not** be done:

- direct import of external ingredient IDs as canonical `FoodIngredient`;
- treat `READY_RAW` or scenario `READY` as RecipeVersion/RecipeTemplate
  production readiness;
- use raw/reference scenario totals as cooked/serving nutrient truth;
- treat source alternatives/choice groups as verified FamilyFoodOS
  substitutions;
- replace missing/null nutrient values with zero;
- infer cooked/raw equivalence from the same ingredient name;
- attach finished-product nutrition to raw process inputs;
- auto-publish RecipeVersion/RecipeTemplate from mirror URLs without source and
  rights review;
- merge this checkpoint into the PR #36 corpus provenance identity without an
  explicit source-lineage proof.

## 14. Assembly A gate impact

Assembly A remains **BLOCKED** after this preflight.

| Existing open gate | v22.13 evidence | Preflight result |
| --- | --- | --- |
| `family_count` | 350 recipes, 292 `READY_RAW`, 64 strict raw-data leads | **OPEN** — substantially larger candidate funnel, but no third production-ready family is established |
| `optional_role` | 41 optional rows / 13 recipes; 7 `READY_RAW` recipes with explicit optional roles | **OPEN** — promising direct evidence, but candidate-specific FoodIngredient/source/rights/kitchen review is still required |
| `verified_substitution` | 1,665 choice-group rows; 1,682 `verified_primary_alternative` rows | **OPEN** — source-listed alternatives do not prove tested substitution/compatibility under the FamilyFoodOS contract |

The package therefore materially improves the **research funnel**, but it does
not silently convert Assembly A into COMPLETE and does not authorize Assembly B.

## 15. DECISION — next bounded operation

If separately authorized after review of this preflight, the next operation
should be:

`V22-13-MAP-A — external identity and candidate mapping`

It is a data/research supporting operation, not a new product milestone.

### Goal

Convert the checkpoint from an external workbook namespace into a fully explicit,
reviewable mapping inventory without publishing production food/recipe truth.

### Scope

1. Classify all **363** external ingredient/reference identities into exactly one
   current mapping state:

   ```text
   EXACT_EXISTING
   ALIAS_EXISTING
   FORM_SPLIT_CANDIDATE
   COMPOSITE_OR_PROCESS_OUTPUT
   NEW_FOOD_CANDIDATE
   UNRESOLVED
   REJECT_TECHNICAL
   ```

2. Classify all **350** recipes into an explicit FamilyFoodOS candidate state,
   retaining source IDs, source URLs, raw readiness, proxy/unresolved debt,
   optional/choice structure, process/retention blockers and rights-review state.
3. Produce a source-lineage inventory that keeps PR #36 and v22.13 provenance
   separate.
4. Produce a bounded shortlist for the next Assembly A evidence review; shortlist
   membership is not production acceptance.
5. Preserve package hashes and enough row/source identifiers to replay every
   mapping decision.

### Non-goals

- no new FoodIngredient publication;
- no Nutrition profile overwrite/promotion;
- no RecipeVersion/RecipeTemplate/RecipeAssembly publication;
- no migration/schema change;
- no retention/yield calculation;
- no Kitchen verification claim;
- no RU familiarity claim without review;
- no Retail/Planner/Serving work;
- no automatic start of Assembly B or PR7.

### Acceptance criteria

- 363/363 external ingredient/reference identities receive one explicit mapping
  state; `UNRESOLVED` is an acceptable truthful result;
- 350/350 recipe candidates receive one explicit candidate classification;
- every mapped value retains external source identity/provenance;
- ambiguous forms fail closed instead of being name-matched automatically;
- no proxy/unresolved/reference-gap record is silently promoted;
- PR #36 provenance remains distinct;
- all generated mapping artifacts are deterministic, reviewable and hash-pinned;
- Assembly A gate status is recomputed from evidence, not manually changed to
  pass.

## 16. OPEN QUESTIONS

The preflight deliberately leaves the following for the mapping/evidence stages:

1. Which of the 363 external ingredient identities are exact matches to existing
   FamilyFoodOS FoodIngredient forms versus true new form candidates?
2. What is the exact bibliographic/legal source behind each `USSR82-*` recipe,
   beyond the mirror URLs present in the checkpoint?
3. Which of the 64 strict raw-data leads can pass RU familiarity, rights,
   kitchen-verification and household-scaling requirements?
4. Can any optional-role recipe satisfy the complete Assembly A family contract
   without introducing a new composition/yield research programme?
5. Can any source alternative obtain independent kitchen-tested substitution
   evidence, or must it remain a source-only variant?
6. Which process/component rows need producer/output bindings instead of direct
   FoodIngredient profiles?

## 17. Preflight conclusion

**FACT:** v22.13 is a high-value structured evidence/reference checkpoint with
much better raw coverage than the current narrow Assembly A donor funnel.

**FACT:** it also contains substantial proxy, unresolved, process, retention,
source-lineage and publication-rights debt.

**DECISION:** adopt the checkpoint as pinned external evidence and proceed only
through an explicit mapping/review layer. Do not import it directly as production
FoodIngredient/Nutrition/Recipe truth.

**DECISION:** Assembly A remains BLOCKED. The checkpoint materially improves the
candidate funnel for all three remaining research gates, especially optional-role
and family-count discovery, but closes none automatically.

**NEXT:** after human review of this preflight, `V22-13-MAP-A` requires separate
explicit authorization before any mapping artifacts are created.