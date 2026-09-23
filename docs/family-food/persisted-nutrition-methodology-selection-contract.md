# Step 6 — Persisted Nutrition Methodology Selection Contract

**Status:** Implementation Contract Gate / adversarial preflight  
**Accepted base:** `3de3c58ee898284f8d2168af1aae04af754a6bfc` (merged PR #84)  
**Bounded step:** Russian-data integration Step 6  
**Runtime implementation authorized by this document:** no — merge/review this gate first

## 1. Goal

Persist an explicit, versioned nutrition-methodology choice for each
`HouseholdMember` and provide an immutable MealPlan revision pin that is
sufficient to reproduce the **selected methodology and member reference-target
inputs** later.

This step exists before Russian Planner/default integration so that future plans
cannot silently depend on whichever methodology or mutable member profile happens
to be current at replay time.

Step 6 does **not** enable Russian targets in Planner/API/UI.

## 2. FACT — accepted dependencies

Accepted runtime before Step 6 already provides:

- `FAMILY_FOOD_NUTRITION_V1` personal reference-target configuration;
- `NASEM_EER_2023_V1`, DRI AMDR/fibre and existing PR6 target calculation;
- `RU_SOURCE_NATIVE_STRICT_V1`;
- opt-in `RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1`;
- `RU_NUTRIENT_REGISTRY_V2`;
- explicit `NutritionMethodologyService` source-native calculation path;
- `RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1` reviewed group-reference table;
- immutable/revisioned `MealPlan`;
- immutable/versioned `MemberMealPatternSelection`;
- household-scoped MealPlan persistence and project UoW;
- migration head `0035_versioned_nutrient_registry`.

The reserved migration
`0033_recipe_template_catalogue` remains reserved and is not available to
Step 6.

## 3. FACT — hidden replay coupling

`HouseholdMember` is mutable.

The current personal reference-target calculation depends on:

- birth date;
- sex;
- height;
- weight;
- activity level;
- goal;
- explicit calculation date;
- pinned nutrition config/version.

Therefore:

> methodology version + member ID is not a historical replay contract.

If a member's height, weight, activity, goal, sex or birth-date correction changes
after a plan is created, recomputing against the current member row can produce a
different result even when the same methodology string is used.

The current MealPlan revision pins meal-pattern selection history, but it does not
pin nutrition methodology or the member calculation-input snapshot.

## 4. DECISION — ownership

Introduce a distinct Household-owned concept:

`MemberNutritionMethodologySelection`.

It is separate from:

- `HouseholdMember` mutable profile fields;
- `MemberMealPatternSelection` schedule/frequency choice;
- platform-owned nutrient registry;
- platform-owned reference tables;
- `MealPlan.config_version`;
- Planner configuration/version;
- RecipeVersion nutrition provenance.

Do not overload any of those concepts to encode methodology selection.

The selection is Household-owned accepted state because different members may
legitimately have different applicability or accepted reference options.

## 5. DECISION — methodology is a version bundle, not one magic enum

The persisted selection records explicit component versions.

### 5.1 Required personal baseline

Every Step 6 selection pins:

`nutrition_config_version = FAMILY_FOOD_NUTRITION_V1`.

This preserves the existing personalized NASEM/DRI reference-target path.

Step 6 does not replace it with a Russian population table.

### 5.2 Optional reviewed Russian add-on

A member may additionally pin both:

`group_reference_methodology_version =
RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1`

and one explicit source-native policy:

- `RU_SOURCE_NATIVE_STRICT_V1`; or
- `RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1`.

The two Russian fields are a pair:

- both null = baseline-only selection;
- both non-null = reviewed Russian add-on;
- exactly one non-null = invalid.

The published-zero-estimate policy remains opt-in. It is never inferred merely
because the Russian table is selected.

### 5.3 Additive semantics

The Russian group-reference table is a **group comparison add-on**.

It does not become an individualized replacement for the NASEM personal target
path.

This preserves the merged Step 5 contract.

## 6. DECISION — selection domain shape

The initial immutable domain shape is conceptually:

```text
MemberNutritionMethodologySelection
- id: UUIDv4
- household_id: UUIDv4
- member_id: UUIDv4
- version_number: positive integer
- nutrition_config_version: non-empty version code
- group_reference_methodology_version: nullable version code
- source_native_policy_version: nullable version code
- accepted_local_date: date
- member_updated_at_at_acceptance: UTC instant
- accepted_at: UTC instant
- supersedes_selection_id: nullable UUIDv4
- created_at: UTC instant
```

The entity is immutable after insertion.

`version_number` is scoped to
`(household_id, member_id)`.

Version 1 has no superseded selection. Version N>1 must supersede exactly version
N-1 for the same household/member.

## 7. DECISION — applicability at acceptance

Baseline-only selection may be persisted even when current NASEM input data are
incomplete. Step 6 persists the chosen methodology; it does not invent missing
member measurements.

For the reviewed Russian add-on, acceptance must fail closed unless the current
Step 5 table is applicable on `accepted_local_date`.

For V1 this requires at least:

- completed age 19+;
- sex exactly `male` or `female`;
- current reviewed table/provider available;
- the 24 Step 5 definitions select completely for that member;
- no KFA inference.

`accepted_local_date` is derived from `accepted_at` in the Household's
current IANA timezone and stored explicitly so a later timezone change cannot
alter the historical applicability date.

The selection also records
`member_updated_at_at_acceptance` as an audit binding.

## 8. DECISION — optimistic concurrency and semantic replay

The acceptance command is household-scoped and accepts an
`expected_current_selection_id` (nullable for an expected first selection).

Semantics:

### Fresh first selection

No current selection exists and caller expects none:

- create version 1;
- one commit.

### Semantic exact replay

If the currently persisted selection already has the requested methodology
bundle, return the current selection with:

- zero writes;
- zero new version;
- stable selection ID/version.

This also handles an ambiguous retry after the first attempt may already have
committed.

### Genuine change

If the expected current selection matches and the requested bundle differs:

- create exactly the next version;
- set `supersedes_selection_id` to the current selection;
- one commit.

### Conflict

Fail without writes when:

- the current selection differs from the caller's expected current selection and
  is not an exact semantic replay;
- selection scope points to another Household/member;
- version chain is not contiguous;
- methodology component version is unsupported;
- Russian component pairing is incomplete;
- Russian applicability fails.

No last-write-wins mutation is allowed.

## 9. DECISION — MealPlan methodology pin

Introduce an immutable plan/member pin:

`MealPlanMemberNutritionMethodologyPin`.

Conceptual shape:

```text
MealPlanMemberNutritionMethodologyPin
- plan_id: UUIDv4
- member_id: UUIDv4
- methodology_selection_id: UUIDv4

# immutable member reference-target input snapshot
- birth_date: nullable date
- sex: nullable text
- height_cm: nullable Decimal
- weight_kg: nullable Decimal
- activity_level: text
- goal: text
- member_updated_at: UTC instant
```

Primary identity is `(plan_id, member_id)`.

The pin references one immutable
`MemberNutritionMethodologySelection`.

The member snapshot is copied from authoritative `HouseholdMember` by the
application service. It is never supplied as trusted caller data.

## 10. Why the MealPlan snapshot is required

The selection freezes **which methodology versions** apply.

The plan pin freezes **which member inputs** were used for that plan revision.

Together with:

- `MealPlan.week_start`;
- immutable selection versions;
- immutable reference-table version;
- existing nutrition config versions;

the plan can later reconstruct the reference-target inputs used for its local
calendar dates even if the current HouseholdMember changes.

This Step 6 replay guarantee is limited to methodology selection and member
reference-target inputs.

It does not claim complete historical recipe/food/transformation replay before
Steps 7–9 publish the remaining required versioned nutrition path.

## 11. DECISION — complete-or-zero plan pin sets

Existing historical MealPlans have no methodology pins.

Do not invent or backfill a methodology choice for them.

For runtime compatibility, MealPlan detail must therefore support two states:

1. **legacy/unaware revision:** zero nutrition-methodology pins;
2. **methodology-pinned revision:** exactly one nutrition-methodology pin for
   every member already pinned by `MealPlanMemberSelection`.

A partial methodology-pin set is invalid.

This provides backward compatibility without allowing ambiguous half-pinned new
state.

Step 6 may extend the existing manual plan creation boundary with an optional
complete methodology-pin mapping.

If omitted, existing manual/Planner behavior remains byte/semantically unchanged.

Step 10 Planner integration must make complete methodology pins mandatory for
Planner-generated methodology-aware revisions before Russian targets/defaults are
enabled.

## 12. DECISION — plan pin validation

When a complete pin mapping is supplied:

- every selection must belong to the same Household as the plan;
- every selection must belong to the corresponding member;
- pin member set must exactly equal MealPlan member-selection member set;
- selection must already exist before the plan revision is persisted;
- selection `accepted_at` must not be later than the plan revision creation
  instant;
- the member snapshot is read from authoritative Household state;
- plan + meal-pattern pins + methodology pins + events + Servings persist in one
  existing project UoW/transaction.

There is no standalone writer that can add methodology pins after a MealPlan
revision has committed.

## 13. DECISION — current selection changes never rewrite plans

Changing the current member methodology selection:

- creates a new selection version;
- does not update any old MealPlan pin;
- does not rewrite old member snapshots;
- does not silently make an old plan "current methodology".

A new plan revision may pin the new methodology selection.

Historical plan revisions retain their original selection and input snapshot.

## 14. DECISION — persistence schema

Runtime Step 6 is expected to require additive SQLite migration:

`0036_persisted_nutrition_methodology_selection`.

Do not consume reserved
`0033_recipe_template_catalogue`.

The migration appends after accepted `0035` in the actual ordered migration
prefix.

### 14.1 New table — member selections

Expected table:

`member_nutrition_methodology_selections`.

Minimum columns correspond to section 6.

Required constraints include:

- PK `id`;
- FK `household_id → households.id`;
- FK `member_id → household_members.id`;
- self-FK `supersedes_selection_id`;
- unique `(household_id, member_id, version_number)`;
- positive version;
- non-empty version strings;
- Russian group-reference/source-policy null-pair consistency.

Do **not** hardcode every methodology version string into a SQL CHECK. Version
support is a domain/application contract so future accepted versions do not
require a schema rebuild merely to extend the allowlist.

### 14.2 New table — MealPlan pins

Expected table:

`meal_plan_member_nutrition_methodology_pins`.

Minimum columns correspond to section 9.

Required constraints include:

- composite PK `(plan_id, member_id)`;
- FK `plan_id → meal_plans.id`;
- FK `member_id → household_members.id`;
- FK `methodology_selection_id → member_nutrition_methodology_selections.id`;
- non-empty activity/goal snapshot fields where current Household contract
  requires them.

Cross-row same-Household/same-member validation remains repository/service logic,
matching existing MealPlan persistence patterns.

### 14.3 Immutability

Both new tables require UPDATE/DELETE rejection after publication.

No existing Household, HouseholdMember, MealPlan, MealPattern or Nutrition table
is rebuilt for Step 6.

## 15. Migration preservation matrix

The 0036 migration must preserve exactly:

| Surface | Preservation requirement |
| --- | --- |
| migrations 0001–0035 | exact accepted historical prefix |
| reserved 0033 | remains reserved/unconsumed |
| households | schema/data unchanged |
| household_members | schema/data unchanged |
| member_meal_pattern_selections | schema/data/history unchanged |
| meal_plans | schema/data/revision identity unchanged |
| meal_plan_member_selections | unchanged |
| meal_plan_events | unchanged |
| servings | unchanged |
| FoodIngredient/Nutrition/Profile/Vector/Composition | unchanged |
| Step 5 runtime package/table | unchanged |
| existing Planner behavior | unchanged |
| existing NASEM member target operation | unchanged |

No historical methodology rows or plan pins are backfilled.

A populated pre-0036 database must upgrade with all existing rows byte/value
equivalent at their owning schema level.

## 16. Migration transaction / rollback contract

0036 is an additive standard migration.

Implementation should use the existing migration runner and avoid
`executescript` for this migration so migration DDL + marker remain under the
runner/session transaction boundary.

Required verification:

- fresh database migration;
- populated accepted 0035 → 0036 upgrade;
- repeat migration is a no-op;
- injected failure before completion leaves:
  - no 0036 marker;
  - no partially authoritative Step 6 schema/state;
- foreign keys clean after success;
- backup/restore to pre-0036 state and re-upgrade succeeds.

Operational rollback after a successful deployment remains restore from the
pre-upgrade backup; do not add destructive down-migration semantics.

## 17. Domain / repository / UoW boundary

Runtime Step 6 should add a focused driver-independent repository contract for
methodology selections and extend the existing MealPlan persistence composition
only as required for atomic plan pins.

Expected capabilities:

```text
add selection
get exact selection
get current selection
list member selection history

MealPlan read:
load zero or complete methodology pins

MealPlan write:
persist complete pins only as part of add_detail(plan revision)
```

Repository methods:

- require Household scope;
- do not expose SQLAlchemy/DBAPI types;
- do not commit independently;
- map constraint failures to stable persistence errors.

## 18. Application service boundary

Step 6 runtime should expose explicit internal/application operations for:

- accept/update a member nutrition methodology selection;
- get current selection;
- get selection history;
- resolve a pinned selection by exact ID;
- create/read a MealPlan revision with optional complete methodology pins.

No public consumer HTTP route is required by Step 6.

No UI is required.

Step 10 owns Planner/default enablement and any consumer-facing selection flow.

## 19. Controlled version resolution

Persisted version strings must not become arbitrary behavior selectors.

Runtime resolves only currently supported exact versions.

Initial support:

```text
nutrition_config_version:
  FAMILY_FOOD_NUTRITION_V1

group_reference_methodology_version:
  null
  RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1

source_native_policy_version:
  null
  RU_SOURCE_NATIVE_STRICT_V1
  RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1
```

Unknown versions fail closed.

The resolver uses existing code-owned config/table/policy boundaries. It does not
load formulas or methodology code from the database.

## 20. Planner/default preservation

Step 6 must not change current Planner behavior.

Specifically:

- `PlannerService.compose_authoritative_request` continues to use the existing
  `NutritionService.member_reference_target` path;
- existing Planner generation does not automatically select a Russian reference
  table;
- existing Planner calls may continue to create legacy/unpinned plan revisions
  until Step 10 integration explicitly switches them to complete pins;
- no API/UI default changes;
- no hidden Russian policy default;
- `RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1` remains opt-in.

This is intentional sequencing, not incomplete migration.

Step 10 consumes the Step 6 persistence contract.

## 21. Fresh / replay / conflict semantics summary

### Member selection

Fresh:
- one immutable version created.

Exact semantic replay:
- zero writes;
- stable ID/version.

Change:
- one next version;
- exact supersedes link.

Conflict:
- zero writes.

### MealPlan

Legacy existing/new compatibility path:
- zero methodology pins.

Pinned path:
- exactly one pin per plan member;
- pins committed atomically with the plan revision.

Partial pin set:
- reject before commit.

Historical replay:
- old plan keeps original selection ID + member input snapshot even after current
  selection/member profile changes.

## 22. Failure injection points for runtime acceptance

Runtime tests must inject/cover failure at least:

1. before selection insert;
2. after selection insert but before commit;
3. stale expected-current selection;
4. invalid supersedes chain;
5. cross-Household selection;
6. Russian add-on for unsupported age/sex;
7. one missing Russian component version;
8. unsupported methodology version;
9. plan with partial methodology-pin mapping;
10. plan pin to another member's selection;
11. plan pin to another Household;
12. failure after plan row insert but before methodology pins;
13. failure after methodology pins but before events/Servings completion;
14. mutable HouseholdMember changed after persisted plan — old plan snapshot
    remains unchanged;
15. current methodology selection changed after persisted plan — old plan pin
    remains unchanged.

All transaction failures must leave no partial authoritative write.

## 23. Adversarial acceptance tests

Runtime Step 6 acceptance must prove at least:

- baseline-only selection persists and replays;
- Russian strict selection persists and replays;
- Russian published-zero-estimate selection persists only when explicitly
  requested;
- child/age-18 Russian add-on fails closed under current Step 5 table;
- unsupported/unknown sex Russian add-on fails closed;
- unknown config/table/policy version fails closed;
- exact semantic retry is zero-write;
- genuine selection change creates next immutable version;
- stale conflicting update writes nothing;
- selection history is Household/member scoped;
- existing `MemberMealPatternSelection` semantics are unchanged;
- existing historical MealPlans load with zero methodology pins;
- no synthetic backfill is created on migration;
- pinned MealPlan requires complete member coverage;
- plan snapshot equals authoritative member inputs at creation;
- later member changes do not alter old plan snapshot;
- later methodology selection changes do not alter old plan pin;
- NASEM default operation output remains unchanged;
- existing Planner output/trace behavior remains unchanged;
- AI is not involved.

## 24. Verification tier for runtime PR

Because Step 6 introduces persistence schema and touches MealPlan UoW/history, the
runtime implementation is a persistence/migration + cross-context contract
change.

Required review-ready evidence:

- domain tests for selection/snapshot invariants;
- service tests for fresh/replay/change/conflict/applicability;
- repository/UoW tests including rollback/failure injection;
- MealPlan persistence/revision regression;
- NASEM Nutrition target regression;
- Russian methodology/reference-table regression;
- migration fresh database;
- populated 0035 → 0036 upgrade;
- migration failure/no-marker proof;
- backup restore/re-upgrade;
- migration lineage/coexistence tests;
- `AI_ENABLED=false`;
- full backend regression;
- full launcher regression;
- Docs verification;
- exact final-head scope/diff/whitespace audit.

Do not repeat broad regression after runtime freeze unless code changes again or a
concrete failure/blocker requires it.

## 25. Data / API / UI impact

### Data

New Household-owned immutable selection history and MealPlan methodology pins.

No new external source data.

### API

No public API required in Step 6.

### UI

None.

### Schema

Expected additive migration 0036.

### Planner

No behavioral change in Step 6.

## 26. Explicit non-goals

Step 6 does not authorize:

- replacing NASEM personal targets with Russian group references;
- Planner Russian target integration;
- API/UI methodology defaults or selection UX;
- automatic opt-in to published-zero estimate;
- Step 7 transformation applicability;
- new retention/yield rules;
- Step 8 recipe-dependency food publication;
- Step 9 executable Russian RecipeVersion publication;
- Step 10 Planner integration;
- adequate-level tables 13/18;
- child Russian reference tables;
- pregnancy/lactation;
- clinical/therapeutic nutrition;
- Auth/PostgreSQL/Retail/AI work.

## 27. Assumptions validated by implementation preflight

**FACT:** a new schema is required because no current table owns versioned
nutrition-methodology selection or plan/member target-input snapshots.

**DECISION:** 0036 is the next actual migration for Step 6; reserved 0033 remains
untouched.

**DECISION:** no existing table rebuild is required by the proposed additive
shape.

If runtime implementation disproves that assumption and needs a rebuild, changes
existing plan semantics, or needs a different ownership model, stop and amend
this Contract Gate before implementation continues.

## 28. Open questions deliberately deferred

The following do not block Step 6:

- future individualized Russian energy algorithm;
- KFA-dependent Russian target tables;
- transformation/retention applicability;
- full historical recipe nutrient replay;
- consumer methodology-choice UX;
- Planner ranking consequences of group-reference comparisons.

Their owning later steps must consume, not silently redefine, the Step 6 persisted
selection contract.

## 29. Stop boundary

This PR is Contract Gate only.

No migration, runtime tables, domain/service/repository implementation or Planner
change belongs in the gate PR.

After review/merge, stop.

Runtime Step 6 requires the next explicit authorization.
