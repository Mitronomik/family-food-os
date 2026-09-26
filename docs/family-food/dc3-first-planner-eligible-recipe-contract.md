# DC3 USSR82-453 Planner-Eligibility Candidate — Preflight Contract

**Status:** evidence/preflight contract / docs-state only
**Decision date:** 2026-09-26
**Accepted base:** `7443f56b856184db6ddb040b9d68425db9f8d41a` (merged PR #96 / Step 10-B)
**Execution issue:** #67 — DATA-CORPUS-V1
**Runtime/data publication authorized by this gate:** no

## 1. Goal

Return from the Step 8–10 technical vertical slice to ordinary DATA-CORPUS-V1
catalogue work and freeze the first low-complexity **Planner-eligibility
candidate** for a bounded evidence review:

```text
USSR82-453 — Яйца вареные
```

This gate does **not** claim that USSR82-453 is already Planner-eligible,
production-ready, publishable or activatable.

Its purpose is to freeze:

- why this candidate is reviewed first;
- the exact accepted DC1 evidence already available;
- the source/provenance gaps that still block publication;
- the food-form / Nutrition / transformation questions that must be decided;
- the Recipe classification / Planner-compatibility question that must be decided;
- the exact evidence outputs required before any runtime/data publication can be
  authorized.

The next step after this gate is **evidence-only preflight**, not production
RecipeVersion publication.

## 2. FACT — sequencing after PR96

PR96 / Step 10-B is merged. The repository now has the reusable technical path:

```text
composition-backed V2 Recipe Nutrition
→ neutral consumption projection
→ Planner exact-energy readiness
→ planner-v0.3
→ MealPlan / Serving nutrition consumption
```

The accepted Step 10 contract explicitly stops before a real Recipe activation
or the next production-data publication.

DATA-CORPUS-V1 remains the active programme before Gate1-CLOSE. PR9 Shopping
remains blocked until Gate1-CLOSE.

## 3. FACT — why USSR82-453 is the first preflight candidate

The accepted DC1 batch plan classifies exactly one recipe as:

```text
DC3-A_CLEAN_BRANCH_EXISTING_PROFILE_REVIEW
```

That recipe is `USSR82-453`.

Accepted DC1 evidence records:

- source name: `Яйца вареные`;
- category: `Блюда из яиц`;
- source structure: single selected 1982 variant;
- no explicit alternative branch;
- one source relationship row;
- ingredient demand: `ING-0071`;
- existing accepted mapping: `ING-0071 → EGG`;
- proposed DC3 batch: `DC3-A_CLEAN_BRANCH_EXISTING_PROFILE_REVIEW`;
- `production_ready = NO`.

The retained relationship row is:

```text
USSR82-453
→ ING-0071 / Яйцо куриное
→ 40 g source_net_for_calc
```

No second FoodIngredient dependency is present in the accepted DC1 relationship
snapshot.

This means USSR82-453 is the cleanest **structural dependency candidate** in the
accepted DC1 queue. It does not mean that all RecipeVersion publication
requirements are already closed.

## 4. FACT — current EGG dependency state

DC1 food-demand evidence records:

```text
ING-0071
→ EGG
→ ALIAS_EXISTING
→ REUSE_ACCEPTED_MAPPING
→ current production profile present
→ USDA FDC Foundation 748967
→ OPEN_REUSE_CURRENT_PROFILE
→ PROFILE_PRESENT_FORM_REVIEW_REQUIRED
```

Therefore:

- FoodIngredient discovery is not the immediate blocker;
- an accepted identity mapping already exists;
- a current profile with accepted provenance exists;
- **recipe-form suitability remains unresolved**.

DC1's remaining catalogue-dependency blocker for this row is exact
recipe-form/profile review.

Full RecipeVersion production readiness still requires the independent
source/process/classification/provenance/Nutrition checks frozen below.

## 5. FACT — exact DC1 artifact lineage and current reproducibility limit

The retained USSR82-453 relationship row is derived from:

```text
data/curation/data-corpus-v1-dc1/source-relationships-part1.csv
source_file = russian_normative_recipes_v22_5_row_nutrients_part1.xlsx
source_sha256 =
72a70f31b6b59454a94d78b73bdf2d43119f04799b266773bb34917e9cb3961e
```

The accepted DC1 `source-artifacts.json` records that source file as:

```text
use = raw relationship/calculation-row extraction only;
nutrient values are not production authority
```

It also records:

```text
availability = OPERATOR_MANAGED_EXTERNAL_SOURCE_BUNDLE
ci_delivery = TEMPORARY_AUTHENTICATED_HTTPS_URL_VIA_ACTIONS_SECRET
repository_retention = NOT_COMMITTED_TO_GIT_UNDER_CURRENT_SOURCE_GOVERNANCE
```

Current DATA-CORPUS-V1 policy requires a durable private storage locator for a
non-committed raw artifact when that artifact is needed for independent
reproduction.

**OPEN BLOCKER:** the accepted DC1 artifact receipt does not currently record
that durable private locator for the v22.5/v22.13 operator-managed source bundle.

DC1 also explicitly records the v22.13 row-level relationship shards as missing,
so full v22.5 ↔ v22.13 relationship-row equality is not claimed.

Therefore this preflight gate may use the accepted DC1 row to select and scope the
candidate, but it must not promote that derived row to final production Recipe
authority.

## 6. DECISION — source authority must be closed before publication

The evidence-only preflight must freeze the exact underlying recipe source truth
for USSR82-453 independently of the derived DC1 CSV.

Required source evidence:

- authoritative source document/collection identity;
- edition/version/date;
- exact recipe/card identity;
- exact selected variant;
- exact source page/locator;
- retained source/card snapshot hash;
- durable retrieval locator/access boundary when raw bytes are not committed;
- exact ingredient row;
- quantity and mass/basis semantics;
- process/technology text;
- output/yield facts, or explicit unknown;
- rights/publication disposition.

A mirror URL may be retained as locator/corroboration where appropriate, but a
mirror URL alone does not establish production authority.

If the exact underlying artifact cannot be durably retrieved and hash-verified,
publication remains blocked.

## 7. DECISION — no automatic EGG profile reuse

The preflight must not assume that the existing `EGG` profile is suitable merely
because the source label is also "Яйцо куриное".

It must decide:

- what physical/input form the source 40 g quantity represents;
- whether `source_net_for_calc` is authoritative RecipeIngredient input mass;
- whether the current `EGG` FoodIngredient/profile represents the same form;
- whether boiling changes the required nutrition authority;
- whether a `FoodTransformation`, yield model or retention profile is required;
- whether current Composition authority can truthfully represent the source
  RecipeVersion without raw↔cooked substitution;
- whether exact positive energy can be produced without estimate promotion.

No name-only mapping, raw/cooked equivalence or hidden mass conversion is
permitted.

If exact form compatibility cannot be proven, the preflight disposition is
`BLOCKED`; the later production PR is not authorized.

## 8. DECISION — source-declared Nutrition is reference evidence only

The current canonical DATA-CORPUS contract remains unchanged.

Source-declared recipe nutrients, if present in the underlying recipe source or
derived corpus, are review/cross-check evidence only unless another accepted
contract explicitly grants them calculation authority.

They must not fill:

- missing EGG profile nutrients;
- missing transformation/yield evidence;
- missing Recipe Nutrition values;
- unknown canonical V2 nutrient concepts.

Unknown remains unknown.

## 9. DECISION — Recipe classification and MealRole remain separate

The source category `Блюда из яиц` does not itself determine
`RecipeVersion.meal_type_code`.

The evidence-only preflight must propose and justify one of:

- an existing supported Recipe classification;
- `KEEP_INACTIVE` because no existing classification is sufficiently supported.

The preflight must then evaluate that classification under the unchanged
compatibility contract:

```text
planner algorithm = planner-v0.3
compatibility = meal-role-recipe-v2
```

This gate does not authorize:

- changing `ROLE_COMPATIBILITY_V1`;
- changing `meal-role-recipe-v2`;
- adding an USSR82-453-specific exception;
- changing MealPattern programmes/selections.

If no current compatible classification is defensible, the recipe stays inactive.

## 10. Required evidence-only preflight outputs

Before any runtime/data publication is authorized, a durable repository evidence
package must record at least:

### Source/provenance

- exact source document/card/variant identity;
- exact locator;
- exact source snapshot/card hash;
- durable retrieval receipt;
- rights/publication disposition;
- exact process/output facts.

### Ingredient/form authority

- exact 40 g quantity/basis interpretation;
- exact `ING-0071 → EGG` mapping disposition;
- current EGG profile identity/provenance;
- source-required form vs current EGG form comparison;
- transformation/yield/retention requirement decision;
- exact authority path or explicit blocker.

### Nutrition

- deterministic Recipe Nutrition preview if authority is sufficient;
- canonical V2 status/known/unknown concepts;
- neutral legacy projection preview;
- exact-energy readiness result;
- explicit proof that no unknown was converted to zero and no estimate became
  exact.

### Recipe/Planner

- proposed `meal_type_code` with evidence/rationale;
- compatibility result under unchanged `meal-role-recipe-v2`;
- applicability/safety/quarantine review;
- explicit final disposition:
  - `ACTIVATE_CANDIDATE`;
  - `PUBLISH_INACTIVE`;
  - or `BLOCKED`.

The evidence package must distinguish FACT / ASSUMPTION / DECISION / OPEN
QUESTION.

## 11. Authorization boundary after preflight

A later production RecipeVersion PR may be authorized only if the evidence-only
preflight has closed all material authority questions needed by that PR.

That production PR must not invent a new:

- source authority;
- FoodIngredient identity;
- form equivalence;
- transformation/yield/retention rule;
- Recipe classification;
- MealRole compatibility rule;
- activation decision.

If any of those remains unresolved, production publication stays blocked.

## 12. Expected production flow if later authorized

Only after an accepted evidence disposition permits publication:

```text
accepted source evidence
→ frozen EGG/form/transformation authority
→ immutable RecipeVersion publication
→ exact Nutrition authority/binding as required
→ neutral V2/legacy projection
→ Planner eligibility under unchanged compatibility
→ MealPlan/Serving integration verification
```

Reuse Step 10 infrastructure. Do not add a parallel Nutrition path.

## 13. Acceptance tests for a later production PR

At minimum prove:

- source identity/version/hash matches accepted preflight;
- exact ingredient dependency matches accepted preflight;
- no hidden raw/cooked/form substitution;
- no unknown→zero or estimate→exact promotion;
- RecipeVersion publication is idempotent;
- conflicting same-provenance structure fails closed;
- deterministic Nutrition reproduces on replay;
- Planner consumes authority only through the neutral projection;
- planner version remains exactly `planner-v0.3`;
- compatibility remains exactly `meal-role-recipe-v2`;
- MealPlan/Serving consumes the same Nutrition truth;
- activation state exactly matches the accepted preflight disposition;
- existing Step 9 butter recipe remains inactive;
- `AI_ENABLED=false`;
- no Shopping/Prep/Retail/API/UI/Auth/PostgreSQL scope.

## 14. Non-goals

This preflight gate does not authorize:

- production RecipeVersion write;
- Recipe activation;
- FoodIngredient creation;
- nutrition/profile mutation;
- transformation/yield/retention publication;
- migration;
- MealRole compatibility changes;
- Planner algorithm rewrite;
- Gate1-CLOSE;
- PR9 Shopping;
- Prep / Freezer;
- Retail;
- API / UI;
- Auth / PostgreSQL;
- AI authority;
- bulk DC3 publication.

## 15. Relationship to DATA-CORPUS-V1

This is the first post-Step-10 return to ordinary DC3 catalogue construction.

USSR82-453 is selected from the accepted DC1 clean-branch queue rather than
inventing a gate-only recipe.

One recipe is used here as a bounded **authority/preflight vertical proof**. It
does not redefine the normal DC3 publication-batch direction of approximately
10–20 recipes where evidence complexity permits.

After this preflight and any later accepted bounded production proof, the project
continues with reviewed DC2/DC3 batches toward the 50–80+ RecipeVersion baseline.
Gate1-CLOSE remains separate.

## 16. Stop boundary

This PR is docs/state only.

After this preflight contract is reviewed and merged:

1. stop;
2. obtain explicit authorization for the **USSR82-453 evidence-only preflight**;
3. do not start production RecipeVersion publication or activation yet;
4. do not start Gate1-CLOSE, PR9 or bulk DC3 automatically.
