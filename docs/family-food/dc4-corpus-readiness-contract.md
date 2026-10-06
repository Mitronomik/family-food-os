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

## 4. Layer A — corpus-wide authoritative readiness audit

DC4 first audits the **entire accepted active production corpus**. Gate1 fixture
selection is a later consumer layer and cannot reduce this audit surface.

The frozen post-R3-D baseline is 51 active exact-energy production
RecipeVersions. The DC4 execution must enumerate the complete active production
RecipeVersion set from repository/runtime truth and reconcile it with that
accepted baseline. If the active set is not exactly the accepted 51, the
difference must receive an explicit PASS/BLOCKED disposition before proceeding;
the implementation must not silently redefine the corpus.

Every active production RecipeVersion in this corpus-wide layer is audited for
all requirements in §§4.1–4.5, whether or not a Gate1 fixture later selects it.

### 4.1 Recipe identity and publication — all 51

For every active production RecipeVersion:

- active current version exists;
- immutable RecipeVersion identity is stable;
- source identity/version is reviewable;
- verification/publication status is accepted;
- Russian consumer display name and steps are present where required;
- no gate-only RecipeVersion exists or is created.

One defective active RecipeVersion is a corpus-wide BLOCKED item even when no
Gate1 fixture selects it.

### 4.2 FoodIngredient resolution — all 51

For every required RecipeIngredient of every active production RecipeVersion:

- a canonical FoodIngredient exists;
- the mapping is exact enough for current food/form semantics;
- unit/quantity representation is valid;
- no required unresolved ingredient is hidden as optional/default;
- no RetailSKU identity is used as Planner food truth.

The **entire active production corpus** must have 100% required FoodIngredient
resolution. Gate1-selected recipes are not a substitute for this corpus-wide
requirement.

### 4.3 Nutrition / prepared-output authority — all 51

For every active production RecipeVersion:

- the exact authority path required by its current publication/Planner-admission
  contract exists;
- exact values remain exact;
- estimates remain estimates;
- UNKNOWN remains UNKNOWN;
- missing values are never coerced to zero;
- source/provenance/version are reviewable;
- no new Nutrition authority is introduced by DC4.

Prepared-output-only recipes may be accepted only according to the current
accepted Planner/Nutrition contract. DC4 must not infer unavailable
macros/micronutrients.

A recipe may be outside a particular fixture's selected meals and still BLOCK
corpus readiness when its accepted active production authority is defective.

### 4.4 Provenance and rights — all 51

For every active production RecipeVersion, the execution must report whether its
production family has reviewable:

- source;
- source URL/reference or durable source identity;
- source/version/date where applicable;
- retained hash/commitment where the current publication contract requires it;
- rights/use disposition sufficient for the already accepted production record.

DC4 does not reopen accepted source policy without evidence of a concrete
conflict, but missing durable provenance on any active production RecipeVersion
is a readiness blocker.

### 4.5 Russian-language readiness — all 51

Consumer-facing recipe text for every active production RecipeVersion must
satisfy the current Russian-language contract.

Internal codes may appear in audit output, but must not be the only user-facing
representation. A Russian-readiness defect cannot be hidden by omitting that
RecipeVersion from the Gate1 fixture weeks.

## 5. Layer B — exact Gate1 consumption fixture matrix

Only after Layer A has enumerated and audited the full active corpus does DC4
consume ordinary accepted production truth through Gate1 fixtures.

The fixture **schedule identity is frozen to the existing repository
`scripts/gate1a_fixture_spec.py::GATE1_ROLE_SHAPES`**. DC4 does not invent a new
fixture topology merely because the catalogue has changed.

Common fixture inputs:

- timezone: `Europe/Moscow`;
- week: Monday `2026-09-14` through Sunday `2026-09-20`;
- every listed daily role repeats on all seven days;
- member meal-pattern source: `CUSTOM`;
- member profile foundation follows the existing Gate1 builder:
  `birth_date=1990-01-<member index>`, alternating female/male by index,
  `height_cm=170`, `weight_kg=65`, `activity_level=active`,
  `goal=maintain`;
- energy shares: BREAKFAST `0.30`, LUNCH `0.35`, DINNER `0.25`;
- same role/date is one shared Household meal event containing exactly the
  members whose frozen schedule includes that role;
- source kind for automatically generated meals remains the current authorized
  Planner source kind; no synthetic RecipeVersion is allowed;
- expected baseline outcome for all three fixtures is **PlannerSuccess with a
  persisted complete seven-day MealPlan**. Any bounded infeasibility in one of
  these three mandatory fixtures is a DC4 BLOCKER.

### Fixture 1 — one-member dinner-only

Exact shape:

```text
Household members: 1
Member 1 roles: DINNER
Member 1 selection: CUSTOM
Member 1 hard exclusions: none
Daily shared events:
  DINNER -> Member 1
Expected week:
  7 DINNER events
  7 Servings
Expected outcome:
  SUCCESS + persisted complete week
```

### Fixture 2 — two-member breakfast + shared dinner with milk exclusion

Exact shape:

```text
Household members: 2
Member 1 roles: BREAKFAST + DINNER
Member 2 roles: DINNER
Selections: CUSTOM / CUSTOM
Member 1 hard exclusions: MILK_2_5
Member 2 hard exclusions: none
Daily shared events:
  BREAKFAST -> Member 1
  DINNER    -> Member 1 + Member 2
Expected week:
  14 meal events
  21 Servings
Expected outcome:
  SUCCESS + persisted complete week
```

The accepted post-R3-D baseline records three `MILK_2_5`-unaffected breakfast
candidates with repetition capacity 9, so this fixture intentionally proves the
hard-exclusion fallback rather than merely reusing an unconstrained household.

Selected meals containing `MILK_2_5` for Member 1 are forbidden. Relevant
rejected candidates must expose the current hard-exclusion rejection reason.

### Fixture 3 — three-member heterogeneous 3/2/1-role household with beef exclusion

Exact shape:

```text
Household members: 3
Member 1 roles: BREAKFAST + LUNCH + DINNER
Member 2 roles: BREAKFAST + DINNER
Member 3 roles: DINNER
Selections: CUSTOM / CUSTOM / CUSTOM
Member 1 hard exclusions: none
Member 2 hard exclusions: none
Member 3 hard exclusions: BEEF_CATEGORY_1_RAW
Daily shared events:
  BREAKFAST -> Member 1 + Member 2
  LUNCH     -> Member 1
  DINNER    -> Member 1 + Member 2 + Member 3
Expected week:
  21 meal events
  42 Servings
Expected outcome:
  SUCCESS + persisted complete week
```

A shared DINNER selected for Member 3 may not require
`BEEF_CATEGORY_1_RAW`. The accepted post-R3-D baseline records 19 unaffected
MAIN candidates / repetition capacity 57, so this fixture tests household
reconciliation under a material member-specific exclusion.

### 5.4 Historical Gate1 fixture test semantics

The existing `backend/app/tests/test_planner_gate1_fixtures.py` predates the
post-DC3 production corpus and historically expects
`NO_ELIGIBLE_CANDIDATE` against its old seed state.

DC4 freezes and reuses its `GATE1_ROLE_SHAPES` schedule identity, but **does not
inherit that historical failure outcome**. The DC4 execution must build the same
exact role shapes against current post-DC3 accepted production truth and prove
the success outcomes frozen above.

If implementation needs a new deterministic DC4 fixture builder/test to avoid
mutating historical evidence, it should add one rather than rewrite historical
PR8/Gate1-A evidence to imply it always had post-DC3 semantics.

### 5.5 Exact fail-closed infeasibility case outside the three mandatory fixtures

In addition to the three successful Gate1 fixtures, DC4 must execute this exact
adversarial capacity case:

```text
Household members: 1
Member 1 roles: BREAKFAST
Selection: CUSTOM
Week: 2026-09-14 .. 2026-09-20
Hard exclusions:
  MILK_2_5
  EGG
Expected outcome:
  bounded PlannerFailure / infeasibility
  no partial MealPlan persisted
```

Rationale: under the accepted post-R3-D milk-free breakfast baseline, the
unaffected set is `HARD_BOILED_EGG`,
`SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`, and
`SAD28_SANDWICH_CHEESE_20_10`. `EGG` removes the first two; the remaining
candidate has repetition capacity below seven breakfasts. The execution must
reconcile this assumption against current RecipeIngredient truth and fail closed
if the exact dependency/capacity differs.

This adversarial case is **not** one of the three mandatory success fixtures and
cannot be used to turn a required Gate1 success fixture into an allowed failure.

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
