# DC4 — Corpus Readiness Audit + Gate1 Consumption Contract

**Status:** implementation/audit contract
**Issue:** #162
**Accepted base:** `d3fc30d7eb677d3dc7aec8f6cb219fffa22762e4`
**Sequence:** `DC4 → Gate1-CLOSE → PR9 Shopping Engine`

## 1. Purpose

DC4 is the final DATA-CORPUS-V1 readiness audit and the first formal consumer of
the completed corpus for Gate1 Planning Core evidence.

The operation answers one question:

> Can the accepted ordinary production catalogue support the current deterministic
> Planning Core without a gate-only data exception?

DC4 is an audit/consumption operation. It does not exist to increase catalogue
size and does not authorize another R3 publication batch.

## 2. Accepted input state

The accepted post-R3-D state is:

- DATA-CORPUS-V1 / DC3 COMPLETE;
- 51 active exact-energy RecipeVersions;
- 17 `breakfast`;
- 33 `main`;
- 1 `sandwich`;
- MAIN family distribution: beef 14 / fish 9 / chicken 4 / meat-free 6;
- exact-beef unaffected MAIN = 19 / repetition capacity 57;
- hard exact `MILK_2_5` breakfast unaffected set = 3 / repetition capacity 9;
- migration head `0042_recipe_prepared_output_nutrition`;
- no migration `0043`;
- `AI_ENABLED=false`;
- current Planner role mapping, scoring and repetition limits unchanged by R3-D.

These counts are accepted starting evidence, not automatic DC4 PASS.

## 3. Audit ownership

DC4 owns:

1. corpus-wide readiness evidence;
2. Gate1 fixture consumption of ordinary accepted production truth;
3. explicit PASS / BLOCKED / DEFERRED disposition for every required check;
4. bounded infeasibility evidence where current hard constraints cannot be met;
5. a durable readiness report suitable for the later Gate1-CLOSE review.

DC4 does not own production data repair. Any repair must be a separate bounded
operation after the audit identifies the exact defect.

## 4. Authoritative corpus audit

The execution must inspect current active production RecipeVersions admitted by
the current Planner contract and establish, for the Gate1-consumed corpus:

### 4.1 Recipe identity and publication

For every consumed RecipeVersion:

- active current version exists;
- immutable RecipeVersion identity is stable;
- source identity/version is reviewable;
- verification/publication status is accepted;
- Russian consumer display name and steps are present where required;
- no gate-only RecipeVersion is created.

### 4.2 FoodIngredient resolution

For every required RecipeIngredient:

- a canonical FoodIngredient exists;
- the mapping is exact enough for current food/form semantics;
- unit/quantity representation is valid;
- no required unresolved ingredient is hidden as optional/default;
- no RetailSKU identity is used as Planner food truth.

The Gate1-consumed set must have 100% required FoodIngredient resolution.

### 4.3 Nutrition / prepared-output authority

For every consumed Planner candidate:

- the exact authority path required by current Planner admission exists;
- exact values remain exact;
- estimates remain estimates;
- UNKNOWN remains UNKNOWN;
- missing values are never coerced to zero;
- source/provenance/version are reviewable;
- no new Nutrition authority is introduced by DC4.

Prepared-output-only recipes may be used only according to the current accepted
Planner/Nutrition contract. DC4 must not infer unavailable macros/micronutrients.

### 4.4 Provenance and rights

The execution must report whether each consumed production family has reviewable:

- source;
- source URL/reference or durable source identity;
- source/version/date where applicable;
- retained hash/commitment where current publication contract requires it;
- rights/use disposition sufficient for the already accepted production record.

DC4 does not reopen already accepted source policy without evidence of a concrete
conflict, but missing durable provenance is a readiness blocker.

### 4.5 Russian-language readiness

Consumer-facing recipe/meal/program text used by the fixture must satisfy the
current Russian-language contract.

Internal codes may appear in audit output, but must not be the only user-facing
representation.

## 5. Gate1 fixture matrix

The execution must use at least three materially different repository-backed
Household fixtures. They must consume current public application/service/repository
boundaries and ordinary accepted catalogue truth.

### Fixture A — General family

Minimum shape:

- three HouseholdMembers;
- materially different serving needs;
- ordinary mixed meal pattern;
- no artificial exclusions introduced only to simplify selection.

Expected result:

- complete seven-day authoritative plan;
- individualized Servings;
- persisted MealPlan/history;
- deterministic trace.

### Fixture B — Hard exclusion / resilience

Must exercise a canonical hard exclusion that materially removes candidates.

At minimum the current accepted evidence includes:

- hard `MILK_2_5` breakfast exclusion with unaffected capacity 9; and/or
- hard beef exclusion against MAIN capacity.

Expected result:

- excluded ingredient never appears in selected meals;
- rejected candidates carry the expected hard-rejection reason;
- a complete week is produced where current accepted capacity proves feasibility;
- if another explicitly tested constraint set is infeasible, the result is
  bounded infeasibility with no partial persisted MealPlan.

### Fixture C — Heterogeneous household / constrained week

Must differ materially from A and B through a combination of:

- heterogeneous member meal opportunities;
- different accepted meal-pattern selections;
- time/equipment/variety/budget constraint already supported by Planner v0;
- shared household events with individualized Servings.

Expected result:

- Planner is not hardcoded to one universal meal count;
- household reconciliation remains deterministic;
- complete week or explicit bounded infeasibility;
- no synthetic RecipeVersion is invented for unsupported source kinds.

## 6. Meal-pattern and source-kind checks

Gate1 consumption must preserve the 2026-09-13 planning amendments.

The audit must prove:

- configurable meal opportunities are represented;
- at least representative 1/2/3/5/6-opportunity capability remains supported by
  current domain contracts/tests where those cases are already accepted;
- heterogeneous member patterns can compile into one household week;
- RecipeVersion meal classification remains distinct from MealRole;
- automatic Planner supply uses only source kinds currently authorized for
  automatic selection;
- unsupported source kinds remain fixed/user-supplied or unavailable rather than
  being silently fabricated.

DC4 may reuse accepted PR7/PR8 evidence where runtime bytes/contracts are unchanged,
but must explicitly identify reused evidence and execute the end-to-end Gate1
fixture proof against the current post-DC3 catalogue.

## 7. Determinism and trace

For successful fixture generation:

- same accepted inputs/config/version produce the same authoritative result under
  the current deterministic contract;
- `planner_version` is recorded;
- candidate pool/rejections/selected recipes are explainable;
- hard rejection reasons are reproducible;
- MealPlan revision/history behavior remains valid.

The audit must not require an LLM or network service.

## 8. Bounded infeasibility

A Planner failure is acceptable evidence only when it is a truthful bounded
infeasibility result rather than an exception, 500 or partial state.

The execution must prove at least one relevant fail-closed case where justified:

- explicit infeasibility result;
- useful rejection/constraint reason;
- no partially persisted MealPlan;
- no mutation of authoritative catalogue or Pantry to force feasibility.

Infeasibility in a required baseline fixture is a DC4 BLOCKER unless the canonical
Gate1 contract explicitly permits that fixture to be the bounded-infeasibility
case and the remaining required product capability is still demonstrated.

## 9. Readiness dispositions

Each audit item receives exactly one disposition:

### PASS

Current accepted production truth and runtime evidence satisfy the requirement.

### BLOCKED

A concrete defect prevents Gate1 readiness, for example:

- unresolved required FoodIngredient;
- missing/invalid authority;
- non-reviewable provenance;
- insufficient candidate capacity for a mandatory fixture;
- Planner/domain regression;
- hidden estimate/unknown promotion;
- partial-state behavior.

A BLOCKED item prevents DC4 completion.

### DEFERRED

Only valid for a capability explicitly outside Gate1 scope and not required by the
current fixture. DEFERRED cannot be used to hide a Gate1 requirement.

## 10. Required durable outputs

The later DC4 execution/evidence PR must create or update:

- a machine-readable readiness summary;
- a human-readable DC4 audit report;
- exact fixture definitions or deterministic fixture builders;
- exact verification commands/workflow;
- state/current-focus, state/progress and state/handoff;
- any focused audit/test code needed to reproduce the evidence.

Suggested bounded locations:

```text
data/curation/dc4-corpus-readiness/
docs/family-food/dc4-corpus-readiness-report.md
backend/app/tests/... or scripts/... only where needed for reproducible proof
```

The exact file layout may be refined by implementation as long as ownership stays
bounded and no new production authority is introduced.

## 11. Adversarial acceptance

The execution must challenge at least:

1. hard exclusion candidate rejection;
2. repetition/capacity boundary;
3. unresolved/missing required authority fails closed;
4. UNKNOWN is not promoted to zero;
5. source/provenance mismatch or tamper where current immutable contract exposes
   a validation seam;
6. exact replay/deterministic generation;
7. no partial persisted MealPlan on infeasibility/failure;
8. no gate-only data authority;
9. no migration 0043;
10. `AI_ENABLED=false`.

Existing accepted tests may satisfy an adversarial point only when they still run
against the current relevant runtime surface or their unchanged-byte evidence is
explicitly justified.

## 12. Verification tier

DC4 execution is mixed data-corpus + Planner integration/gate evidence.

Required minimum:

- bounded corpus validator/audit;
- focused Planner/Gate1 integration tests;
- current fixture persistence proof;
- relevant MealPlan/Serving and Nutrition/Recipe regressions affected by the
  consumption path;
- deterministic rerun/replay proof;
- migration head check;
- `AI_ENABLED=false`;
- docs/state/status checks;
- diff/scope/whitespace checks.

A full backend/launcher regression is required only if the execution changes a
shared runtime/persistence/startup surface. Audit/test/data-only work must not run
broad regression merely by habit, but Gate1-CLOSE may independently require a
broader final evidence set.

## 13. Non-goals

DC4 contract and execution do not authorize:

- R3-E/R3-F or arbitrary catalogue growth;
- new FoodIngredient, FoodNutritionProfile, NutrientVector, Composition or
  RecipeVersion publication;
- schema change or migration 0043;
- Planner algorithm/scoring/role/repetition redesign;
- new Nutrition authority type;
- Shopping Engine;
- Prep / Freezer;
- PDF;
- PWA;
- Retail;
- AI;
- PostgreSQL/Auth/shared deployment;
- Gate1-CLOSE in the same audit PR unless separately and explicitly authorized.

## 14. Defect routing

If DC4 finds a material readiness defect:

```text
DC4 finding
→ exact BLOCKED evidence
→ separate bounded correction contract/PR if required
→ rerun affected DC4 checks
```

Do not weaken the fixture, change Planner rules or publish filler data merely to
obtain PASS.

## 15. Exit criteria

DC4 execution is review-ready only when:

1. all required audit dimensions have explicit dispositions;
2. all required Gate1 fixture cases have reproducible evidence;
3. ordinary accepted production catalogue truth is consumed;
4. no gate-only authority/data exception exists;
5. hard exclusions and individualized Servings are proven;
6. heterogeneous meal-pattern behavior is covered;
7. deterministic trace/replay is proven;
8. bounded infeasibility is fail-closed where tested;
9. no unresolved Gate1 BLOCKED item remains;
10. migration remains 0042 / no 0043;
11. `AI_ENABLED=false`;
12. state and durable evidence are synchronized.

Passing DC4 does not itself mark Gate1 COMPLETE.

The next separate operation is:

```text
Gate1-CLOSE review
→ if accepted, PR9 Shopping Engine
```

## 16. Stop rule

This contract PR is docs/state only.

After it is independently reviewed and merged, start one separate DC4
execution/evidence operation. Do not start Gate1-CLOSE or PR9 automatically.
