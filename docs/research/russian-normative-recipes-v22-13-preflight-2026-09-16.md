# Russian normative recipes v22.13 — FamilyFoodOS integration preflight

**Status:** research/evidence preflight; no production publication
**Reviewed:** 2026-09-16
**Repository base:** `38de460dfcbf84997a1d9275314c4f3dab7e1d00` (PR #37 merged)
**Operation:** `V22-13-DATA-INTEGRATION-PREFLIGHT`

## 1. Purpose

This document evaluates the external checkpoint
`russian_normative_recipes_v22_13_checkpoint.zip` against current FamilyFoodOS
FoodIngredient, Nutrition, Composition, Recipe/source-provenance and Recipe
Assembly A contracts before any import or publication decision.

This operation is read-only with respect to runtime/domain truth. It does not
create or modify FoodIngredient, Nutrition profiles, RecipeVersion,
RecipeTemplate, RecipeAssembly, migrations, production seeds or accepted source
corpus rows.

## 2. Repository contracts used

The review used the accepted repository direction after PR #37, including
`AGENTS.md`, architecture/roadmap plus their 2026-09-13 addenda,
`food-composition-and-assembly.md`, `nutrition-core.md`, verification policy,
Recipe Assembly A/R1 evidence and the PR #36 Russian normative source corpus.

Existing invariants remain unchanged:

```text
FoodIngredient = sole canonical food identity
raw/input/cooked mass and food forms are distinct
Recipe publication requires verifiable provenance
Nutrition/Composition truth is deterministic and versioned
unknown critical facts do not become zero or guessed precision
AI_ENABLED=false remains sufficient for core behavior
```

## 3. External package integrity

The external workbook package is not committed by this operation. Exact reviewed
SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `russian_normative_recipes_v22_13_checkpoint.zip` | `a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97` |
| integrity audit | `4353aec58e2610e3a9b4d46b970888cd17e1aabcd6ebea2af6ed0c323865d47f` |
| manifest | `f57eb053f11f6230ad733824dbf4d3bba523be13d9418c7ab0932e58046aa9f0` |
| mass/nutrients | `5ea78ead82568f8aff019a4076215c6598675783cb81e0d1d5b4f913016de4cc` |
| row nutrients part 1 | `49eb0e24055f4261e8b4664ecf4a4002a45a9182b8fd54067c24836cbcc811af` |
| row nutrients part 2 | `28672441274b21a4c36efcbc23507594aa8cc10fa4079c531606becdb4a14ec2` |
| row nutrients part 3 | `bba7f2011462e720aad77791b8c0838d1a15bccd0bc514dc406f8af200f77b1b` |
| row nutrients part 4 | `10dfa8a4fd21e0b6346740578b9515f053eb9f82b98403c2570ecc5ef63d121e` |

Each extracted workbook was byte-compared with its ZIP member; all matched.

## 4. FACT — package inventory

- recipes: **350**;
- ingredient contribution rows: **6,179**;
- nutrient-input eligible rows: **6,177**;
- ingredient/reference records: **363**;
- scenario rows: **479**;
- scenario `READY`: **460**;
- scenario `PARTIAL`: **19**.

Recipe raw-readiness:

| Status | Count |
| --- | ---: |
| `READY_RAW` | 292 |
| `PARTIAL_RAW` | 53 |
| `NO_RELATIONSHIPS` | 4 |
| `NO_CALC_INPUTS` | 1 |

`READY_RAW` is an external raw/reference-completeness status. It is not a
FamilyFoodOS production-readiness status.

The checkpoint tracks 11 nutrient fields: Protein, Fat, Carbs, Kcal, Ca, Mg, P,
Fe, B1, B2 and VitC.

Reported minimum coverage is approximately:

- row coverage: **97.7335%**;
- total-mass coverage: **97.5583%**;
- non-water mass coverage: **96.5740%**.

Open debt:

- ingredient/reference queue: **58**;
- ingredient × nutrient gaps: **578**;
- semantic mapping pairs explicitly left for review: **15**.

## 5. FACT — evidence quality is lower than numeric availability

Strict A/B evidence-complete scope is approximately:

- **4,629 / 6,179 rows = 74.94%**;
- **528,095.084 g = 67.91%** of measured mass scope.

The 363 ingredient/reference records are stratified:

| Tier | Count |
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

**DECISION:** `C_PROXY`, `UNRESOLVED`, partial and process-dependent states are
review states, not production Nutrition authority.

## 6. FACT — form/process/retention semantics

Representative row states:

- `RAW_OR_UNSPECIFIED_OK`: 5,970;
- `COOKED_COMPONENT_RETENTION_PENDING`: 110;
- `COOKED_STATE_REVIEW`: 47;
- `COOKED_COMPONENT_REVIEW`: 24.

Semantic issue summaries include:

| Issue | Rows | Mass/scope | Affected scope |
| --- | ---: | ---: | --- |
| cooked-state review | 47 | 5,280 g | 19 recipes |
| cooked-component review | 24 | 1,448 g | 5 recipes |
| cooked-component retention pending | 112 | 14,495 g | 34 recipes |
| `SPLIT_REQUIRED` | 13 | 1,429 g | 7 recipes / 4 ambiguous parents |
| `PROCESS_TRANSFER_REQUIRED` | 27 | 11,872 g | 11 recipes / 8 open inputs |
| `COMPONENT_PROFILE_REQUIRED` | 12 | 1,725 g | 9 recipes / 7 blockers |

The package explicitly states:

```text
retention coefficients applied = NO
process-dependent profiles assigned by food-table proxy = NO
ambiguous/unreported cells remain null, not zero
```

**DECISION:** preserve this separation. Raw/reference scenario totals must not be
used as authoritative cooked/serving nutrition until FamilyFoodOS
transformation/yield/retention requirements pass.

## 7. FACT — optional roles and source choices

The row layer contains:

- optional rows: **41** across **13 recipes**;
- `READY_RAW` recipes with optional rows: **7**;
- `ChoiceGroup` rows: **1,665** across **171 recipes**;
- `verified_primary_alternative` rows: **1,682**.

Seven `READY_RAW` examples with explicit optional rows are:

- `USSR82-251` — `Солянка домашняя`;
- `USSR82-267` — `Суп-пюре из моркови или репы`;
- `USSR82-309` — `Щи зеленые с яйцом`;
- `USSR82-310` — `Щи зеленые с мясом`;
- `USSR82-317` — `Суп из плодов или ягод сушеных`;
- `USSR82-369` — `Грибы в сметанном соусе`;
- `USSR82-671` — `Биточки паровые`.

**DECISION:** external terms such as `verified_primary_alternative` describe
source/amount evidence. They do not automatically satisfy the FamilyFoodOS
`verified_substitution` gate. Existing Assembly A research already establishes
that a source-listed alternative does not prove kitchen-tested substitution in
the required form/mass/composition scope.

## 8. FACT — source lineage is distinct from PR #36

The accepted PR #36 corpus is `RU_MR_2_4_0162_19`: 214 technological cards from
Rospotrebnadzor guidance МР 2.4.0162-19, appendices 5–8.

The uploaded checkpoint instead uses identifiers such as `USSR82-*` and a
different source/reference graph. Relationship evidence is dominated by online
publication/mirror URLs, especially `studopedia.net` and `interdoka.ru`, while
nutrition/profile evidence is mixed across several source families.

The workbook package does not establish FamilyFoodOS rights clearance for direct
RecipeVersion/RecipeTemplate publication.

**DECISION:** PR #36 provenance and v22.13 provenance remain separate unless a
later source-lineage review proves an exact relationship.

## 9. FACT — identity mismatch

The checkpoint has **363 external ingredient/reference identities**. They are not
FamilyFoodOS `FoodIngredient` identities.

Name similarity is insufficient because form, cooked/raw state, composite/process
outputs and calculation authority may differ.

**DECISION:** no external checkpoint identifier is promoted as a canonical
FoodIngredient by name matching. A later mapping operation must classify every
external identity explicitly.

## 10. Data-readiness triage

For research triage only, this stricter filter was computed:

```text
READY_RAW
AND ProxyRows = 0
AND StateReviewRows = 0
AND UnresolvedIDs = empty
AND ReferenceCompleteRows = CalcRows
```

Exactly **64 recipes** pass. This does not establish rights, FoodIngredient
mapping, RU familiarity, kitchen verification, output yield/retention, household
scaling or RecipeTemplate rules.

Eight data-readiness leads that also contain explicit choice groups are:

- `USSR82-414` — `Каша вязкая с морковью`;
- `USSR82-374` — `Картофель, запеченный с яйцом и помидорами`;
- `USSR82-412` — `Каша вязкая с тыквой`;
- `USSR82-413` — `Каша вязкая с черносливом`;
- `USSR82-285` — `Овощи и яйца`;
- `USSR82-459` — `Яичница глазунья (натуральная)`;
- `USSR82-468` — `Омлет из яичного порошка`;
- `USSR82-451` — `Макаронник`.

These are research leads, not approved RecipeTemplate families.

## 11. Package quality observations

Presentation-level stale artifacts remain:

- the mass workbook README still refers to `v22.12`;
- dashboard/coverage presentation contains stale duplicate v22.12 rows;
- a duplicate stale VitC summary remains in presentation sheets.

Manifest/integrity sheets carry the current v22.13 values.

**DECISION:** any later normalization must retain exact source hashes and record
all cleanup steps; stale summaries are not permission to rewrite underlying data.

## 12. Integration classification

### ADOPT

- hash-pin the package as external evidence/reference material;
- preserve null/not-zero policy;
- preserve raw/process/retention separation;
- preserve row-level provenance and proxy/unresolved states;
- use coverage and structure for evidence triage.

### MAP

- 363 external ingredient/reference identities to explicit FamilyFoodOS mapping
  states;
- 350 recipes to a pre-publication candidate/evidence inventory, not directly to
  RecipeVersion;
- nutrient/reference evidence to candidate provenance without overwriting
  accepted Nutrition profiles;
- cooked/process/component identities only after form/process review.

### NEEDS_REVIEW

- 99 `UNRESOLVED` and 62 `C_PROXY` reference records;
- 58-item open queue and 578 field-level gaps;
- 15 semantic pairs left for review;
- state/component/process/retention blockers;
- source-lineage and rights/publication status;
- RU familiarity and kitchen-verification scope;
- exact substitution/compatibility evidence;
- mapping to canonical FoodIngredient forms and composition authority.

### REJECT as direct production truth

- direct external-ID → FoodIngredient import;
- `READY_RAW`/scenario `READY` interpreted as production readiness;
- raw/reference totals used as cooked/serving nutrition;
- source alternatives treated as verified substitutions;
- missing/null values converted to zero;
- cooked/raw equivalence inferred by name;
- finished-output nutrition attached to raw process inputs;
- RecipeVersion/RecipeTemplate publication from mirror URLs without source/rights
  review;
- silent merging with PR #36 provenance.

## 13. Assembly A impact

Assembly A remains **BLOCKED**.

| Gate | v22.13 evidence | Result |
| --- | --- | --- |
| `family_count` | 350 recipes, 292 `READY_RAW`, 64 strict raw-data leads | **OPEN** — larger funnel, but no third production-ready family established |
| `optional_role` | 41 optional rows / 13 recipes; 7 `READY_RAW` examples | **OPEN** — promising evidence, but candidate mapping/source/rights/kitchen review remains |
| `verified_substitution` | 1,665 choice-group rows; 1,682 source-alternative rows | **OPEN** — source alternatives do not prove tested substitution compatibility |

The package materially improves the research funnel but closes none of the three
gates automatically and does not authorize Assembly B.

## 14. DECISION — proposed next operation

If separately authorized after review, the next operation should be
`V22-13-MAP-A — external identity and candidate mapping`.

### Goal

Create a deterministic review inventory without publishing production food or
recipe truth.

### Scope

1. Classify all **363** external ingredient/reference identities into one state:

   ```text
   EXACT_EXISTING
   ALIAS_EXISTING
   FORM_SPLIT_CANDIDATE
   COMPOSITE_OR_PROCESS_OUTPUT
   NEW_FOOD_CANDIDATE
   UNRESOLVED
   REJECT_TECHNICAL
   ```

2. Classify all **350** recipes into explicit candidate states while retaining
   source IDs/URLs, raw readiness, proxy/unresolved debt, optional/choice
   structure, process/retention blockers and rights-review state.
3. Keep PR #36 and v22.13 source lineage separate.
4. Produce a bounded shortlist for the next Assembly A evidence review; shortlist
   membership is not production acceptance.
5. Preserve hashes and row/source identifiers for replay/audit.

### Non-goals

No FoodIngredient/Nutrition/Recipe publication, schema/migration, retention/yield
calculation, kitchen-verification claim, RU-familiarity claim, Planner/Retail/AI
work, Assembly B or PR7.

### Acceptance criteria

- 363/363 external ingredient/reference identities receive one explicit mapping
  state; `UNRESOLVED` is acceptable;
- 350/350 recipes receive one explicit candidate classification;
- source identity/provenance is retained;
- ambiguous forms fail closed instead of name matching;
- proxies/gaps are never silently promoted;
- PR #36 provenance remains distinct;
- mapping artifacts are deterministic, reviewable and hash-pinned;
- Assembly A gates are recomputed from evidence rather than manually changed.

## 15. OPEN QUESTIONS

1. Which of the 363 external identities exactly match existing FoodIngredient
   forms versus requiring a new form candidate?
2. What exact bibliographic/legal source sits behind each `USSR82-*` record beyond
   the mirror URLs in the package?
3. Which of the 64 strict raw-data leads can also pass rights, RU familiarity,
   kitchen verification and household scaling?
4. Can an optional-role recipe satisfy the complete Assembly A family contract
   without starting a separate composition/yield research programme?
5. Can any source alternative gain independent kitchen-tested substitution
   evidence?
6. Which process/component rows need producer/output binding instead of a direct
   FoodIngredient profile?

## 16. Conclusion

**FACT:** v22.13 is a high-value structured evidence/reference checkpoint with a
much larger raw candidate funnel than the previous narrow Assembly A donor set.

**FACT:** it also contains substantial proxy, unresolved, process, retention,
source-lineage and publication-rights debt.

**DECISION:** adopt it as hash-pinned external evidence and proceed only through
an explicit mapping/review layer. Do not import it directly as production
FoodIngredient/Nutrition/Recipe truth.

**DECISION:** Assembly A remains BLOCKED. The package improves all three remaining
research funnels but closes none automatically.

**NEXT:** `V22-13-MAP-A` requires separate explicit authorization after review of
this preflight.