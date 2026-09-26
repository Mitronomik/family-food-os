# DC3 First Planner-Eligible Recipe — Contract Gate

**Status:** pre-implementation contract / docs-only
**Decision date:** 2026-09-26
**Accepted base:** `7443f56b856184db6ddb040b9d68425db9f8d41a` (merged PR #96 / Step 10-B)
**Execution issue:** #67 — DATA-CORPUS-V1
**Runtime/data publication authorized by this gate:** no

## 1. Goal

Return from the Step 8–10 technical vertical slice to ordinary DATA-CORPUS-V1
production catalogue work and freeze the first low-risk RecipeVersion candidate
that can later become a real Planner-consumable production recipe.

The selected candidate is:

```text
USSR82-453 — Яйца вареные
```

This gate does not publish or activate the recipe. It closes the evidence and
authority decisions required before a separately authorized runtime/data PR.

## 2. FACT — sequencing after PR96

PR96 / Step 10-B is merged. The repository now has the reusable path:

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

## 3. FACT — why USSR82-453 is the next candidate

The accepted DC1 batch plan classifies exactly one recipe as:

```text
DC3-A_CLEAN_BRANCH_EXISTING_PROFILE_REVIEW
```

That recipe is `USSR82-453`.

DC1 records:

- source name: `Яйца вареные`;
- category: `Блюда из яиц`;
- source structure: single selected 1982 variant;
- no explicit alternative branch;
- one source relationship row;
- ingredient demand: `ING-0071`;
- existing accepted mapping: `ING-0071 → EGG`;
- proposed DC3 batch: `DC3-A_CLEAN_BRANCH_EXISTING_PROFILE_REVIEW`;
- production_ready remains `NO` only because exact recipe-form/profile review is
  still required.

The source relationship row currently retained by DC1 is:

```text
USSR82-453
→ ING-0071 / Яйцо куриное
→ 40 g source net-for-calculation
```

No second FoodIngredient dependency is present in the accepted DC1 relationship
snapshot.

## 4. FACT — current EGG authority state

DC1 food-demand evidence records:

```text
ING-0071
→ EGG
→ ALIAS_EXISTING
→ accepted identity mapping
→ current production profile present
→ USDA FDC Foundation 748967
→ OPEN_REUSE_CURRENT_PROFILE
```

The unresolved state is explicitly:

```text
PROFILE_PRESENT_FORM_REVIEW_REQUIRED
```

Therefore the next operation is not source discovery and not FoodIngredient
creation. It is exact suitability review of the existing `EGG` authority for
the source-required egg form, followed only if justified by a bounded production
RecipeVersion publication.

## 5. DECISION — no automatic profile reuse

This gate must not assume that an existing `EGG` profile is suitable merely
because the source label is also "Яйцо куриное".

The review must prove the exact form/basis semantics required by USSR82-453.

At minimum it must establish:

- what physical/input form the source 40 g quantity represents;
- whether the existing `EGG` profile describes the same authoritative form;
- whether cooking/boiling changes the nutrition authority required by the
  RecipeVersion;
- whether a FoodTransformation / yield / retention path is required;
- whether the current V2 Composition path can reproduce the intended Recipe
  Nutrition without estimate promotion;
- whether any source-declared nutrition is only cross-check evidence rather than
  calculation authority.

If exact form compatibility is not proven, runtime publication stops. No name-only
mapping or raw/cooked substitution is permitted.

## 6. DECISION — Recipe classification and MealRole are separate

The source category `Блюда из яиц` does not by itself determine
`RecipeVersion.meal_type_code`.

The runtime publication PR must freeze a supported Recipe classification from
reviewed product/source semantics before activation.

No MealRole compatibility change belongs here.

In particular, this gate does not authorize:

- changing `ROLE_COMPATIBILITY_V1`;
- changing `meal-role-recipe-v2`;
- adding a recipe-specific compatibility exception.

If no existing compatible Recipe classification is defensible, keep the future
Recipe inactive and report the blocker instead of changing Planner compatibility.

## 7. DECISION — first ordinary Planner candidate must be production truth

A later runtime/data PR may activate USSR82-453 only when all of the following
are proven together:

1. immutable source RecipeVersion provenance is exact and reviewable;
2. all required source ingredient rows resolve exactly;
3. FoodIngredient/form authority is valid;
4. deterministic Nutrition is available through accepted authority;
5. exact positive Planner energy readiness is available without hidden estimate;
6. Recipe classification is compatible with the intended existing MealRole;
7. no applicability quarantine forbids automatic household use;
8. Russian display/process instructions are source-backed and usable;
9. activation is explicitly part of that bounded production-data PR.

Nutrition success alone does not imply activation.

## 8. Required preflight outputs

Before runtime publication, prepare durable evidence for:

- exact source card/variant identity and source locator;
- exact ingredient row and quantity/basis;
- EGG profile identity and provenance;
- form comparison: source-required egg vs existing EGG authority;
- transformation/yield/retention requirement decision;
- deterministic Recipe Nutrition preview;
- exact canonical/legacy projection result;
- proposed Recipe meal_type classification with rationale;
- Planner compatibility outcome under unchanged
  `meal-role-recipe-v2`;
- rights/provenance status;
- explicit activation recommendation: `ACTIVATE` or `KEEP_INACTIVE`.

## 9. Runtime PR shape if preflight passes

A separately authorized runtime/data PR should remain bounded to this one recipe
and only the exact dependency authority required for it.

Expected flow:

```text
accepted source evidence
→ exact EGG authority/form decision
→ immutable RecipeVersion publication
→ exact Nutrition authority/binding as required
→ neutral V2/legacy projection
→ Planner candidate eligibility
→ persisted MealPlan/Serving integration test
```

Reuse Step 10 infrastructure. Do not add a new parallel Nutrition path.

## 10. Acceptance tests for the later runtime PR

At minimum prove:

- source identity/version is exact;
- one required EGG dependency is resolved;
- no hidden raw/cooked/form substitution;
- no unknown→zero or estimate→exact promotion;
- RecipeVersion publication is idempotent;
- conflicting same-provenance structure fails closed;
- deterministic Nutrition reproduces on replay;
- Planner receives authority only through the neutral projection;
- planner version remains exactly `planner-v0.3`;
- compatibility remains exactly `meal-role-recipe-v2`;
- MealPlan/Serving can consume the same Nutrition truth;
- production activation, if authorized by the runtime contract, changes only the
  intended recipe;
- existing Step 9 butter recipe remains inactive;
- AI_ENABLED=false;
- no Shopping/Prep/Retail/API/UI/Auth/PostgreSQL scope.

## 11. Non-goals

This Contract Gate does not authorize:

- production RecipeVersion write;
- Recipe activation;
- FoodIngredient creation;
- nutrition/profile mutation;
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

## 12. Relationship to DATA-CORPUS-V1

This is the first post-Step-10 return to ordinary DC3 catalogue construction.

It is intentionally selected from the accepted DC1 clean-branch queue rather than
inventing a new gate-only recipe.

After a successful bounded runtime publication, continue with the next reviewed
DC2/DC3 production batch toward the DATA-CORPUS-V1 baseline of 50–80+ usable
RecipeVersions. Gate1-CLOSE remains separate.

## 13. Stop boundary

This PR is docs/state only.

After this gate is reviewed and merged:

1. stop;
2. obtain explicit authorization for the bounded USSR82-453 runtime/data
   publication;
3. do not start PR9, Gate1-CLOSE or bulk DC3 automatically.
