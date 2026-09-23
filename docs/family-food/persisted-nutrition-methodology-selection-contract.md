# Step 6 — Persisted Reference Methodology Selection Contract

**Status:** Implementation Contract Gate / corrected after adversarial re-review
**Accepted base:** `3de3c58ee898284f8d2168af1aae04af754a6bfc` (merged PR #84)
**Bounded step:** Russian-data integration Step 6
**Runtime implementation authorized by this document:** no — merge/review this gate first

## 1. Goal

Persist an explicit, versioned **member reference-methodology selection** before
Russian Planner/default integration, while preserving historical replay and the
existing NASEM baseline.

Step 6 is deliberately split into two runtime slices:

```text
Step 6A
Member reference-methodology selection persistence
→ migration 0036

Step 6B
MealPlan reference-methodology pins + member target-input snapshots
→ migration 0037
```

The split is mandatory. It is the direct response to the project stop-signal
adopted after PR77: do not combine a new persisted identity, a second persisted
bounded context and historical compatibility migration in one runtime PR.

## 2. FACT — accepted dependencies

Accepted runtime before Step 6 already provides:

- `FAMILY_FOOD_NUTRITION_V1` personal reference-target configuration;
- `NASEM_EER_2023_V1`, DRI AMDR/fibre and the existing PR6 personal target path;
- `RU_NUTRIENT_REGISTRY_V2`;
- `RU_SOURCE_NATIVE_STRICT_V1`;
- opt-in `RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1`;
- explicit `NutritionMethodologyService.atomic_input(..., policy=...)`;
- `RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1` reviewed group-reference table;
- immutable/revisioned `MealPlan`;
- immutable/versioned `MemberMealPatternSelection`;
- household-scoped MealPlan persistence and project UoW;
- migration head `0035_versioned_nutrient_registry`.

The reserved migration `0033_recipe_template_catalogue` remains reserved and is
not available to Step 6.

## 3. FACT — two different methodology axes exist

The project has two distinct concepts that must not be stored as one member
preference merely because both contain the word "methodology".

### 3.1 Member reference methodology

This controls how a HouseholdMember is compared with reference targets.

Current accepted axes:

- personal baseline config:
  `FAMILY_FOOD_NUTRITION_V1`;
- optional reviewed group-reference table:
  `RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1`.

This is member-scoped because applicability depends on member facts such as age
and sex.

### 3.2 Food/source-native calculation policy

`RU_SOURCE_NATIVE_STRICT_V1` and
`RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1` are inputs to
`NutritionMethodologyService.atomic_input`.

They interpret a FoodComposition/NutrientVector source observation and do not
take a HouseholdMember as an input.

Therefore:

> source-native food calculation policy is not a member reference-methodology
> selection.

Step 6A/6B must not persist `RU_SOURCE_NATIVE_*` inside a member selection.

The later V2 food/recipe/Planner integration contract must pin source-native food
calculation policy at the calculation/plan receipt level where one shared food or
recipe nutrition result has one reproducible policy. Step 6 does not pre-empt
that future ownership decision.

## 4. FACT — hidden historical replay coupling

`HouseholdMember` is mutable.

The current personal reference-target calculation depends on:

- birth date;
- sex;
- height;
- weight;
- activity level;
- goal;
- explicit calculation date;
- pinned `FAMILY_FOOD_NUTRITION_V1` config.

Therefore:

> reference-methodology version + member ID is not a historical replay contract.

If a member changes after a plan is created, recomputing against the current
member row can produce a different reference result even when the same
methodology version is selected.

The current MealPlan revision pins meal-pattern selection history, but does not
pin a member reference-methodology selection or the member target-input snapshot.

## 5. DECISION — Step 6A ownership

Introduce a distinct Household-owned concept:

`MemberReferenceMethodologySelection`.

It is separate from:

- mutable `HouseholdMember`;
- `MemberMealPatternSelection`;
- platform nutrient registry;
- platform reference tables;
- food/source-native calculation policy;
- `MealPlan.config_version`;
- Planner configuration/version;
- RecipeVersion nutrition provenance.

Different HouseholdMembers may hold different accepted reference selections.

## 6. DECISION — Step 6A supported reference bundles

The selection records reference methodology only.

### 6.1 Baseline bundle

```text
nutrition_config_version = FAMILY_FOOD_NUTRITION_V1
group_reference_methodology_version = null
```

This preserves the existing NASEM/DRI personal reference-target path.

### 6.2 Russian group-reference add-on bundle

```text
nutrition_config_version = FAMILY_FOOD_NUTRITION_V1
group_reference_methodology_version =
  RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1
```

The Russian table is additive.

It does not replace the personal NASEM/DRI target and is never presented as an
individualized Russian formula.

### 6.3 Unsupported combinations

Unknown config/table versions fail closed.

The database does not hardcode the current allowlist. Exact supported versions
are resolved by code-owned reference-methodology resolver logic.

## 7. DECISION — Step 6A domain shape

The initial immutable domain shape is conceptually:

```text
MemberReferenceMethodologySelection
- id: UUIDv4
- household_id: UUIDv4
- member_id: UUIDv4
- version_number: positive integer

- nutrition_config_version: non-empty version code
- group_reference_methodology_version: nullable version code

- accepted_local_date: date
- household_timezone_at_acceptance: IANA timezone
- member_updated_at_at_acceptance: UTC instant
- household_updated_at_at_acceptance: UTC instant

- acceptance_request_id: UUIDv4
- accepted_at: UTC instant
- supersedes_selection_id: nullable UUIDv4
- created_at: UTC instant
```

The entity is immutable after insertion.

`version_number` is scoped to `(household_id, member_id)`.

Version 1 has no superseded selection. Version N>1 supersedes exactly version
N-1 for the same Household/member.

`acceptance_request_id` is the persisted idempotency identity of a command
that **publishes a new immutable selection version**. It is stored on that
selection row and is not a methodology version.

A semantic no-op publishes no new selection and performs zero writes. Therefore a
new request ID used only for a semantic no-op is intentionally **not consumed or
persisted**. Reusing that unconsumed ID later is a new command and must satisfy
the then-current optimistic-concurrency and applicability rules.

## 8. DECISION — applicability at Step 6A acceptance

Baseline selection may be persisted even when current NASEM input data are
incomplete. Step 6 records the selected reference methodology; it does not invent
missing measurements.

For the reviewed Russian group-reference add-on, acceptance fails closed unless
the Step 5 table is applicable on `accepted_local_date`.

Current V1 applicability requires at least:

- completed age 19+;
- sex exactly `male` or `female`;
- reviewed Step 5 table/provider available;
- the 24 Step 5 definitions select completely;
- no KFA inference.

`accepted_local_date` is derived from `accepted_at` using the authoritative
Household timezone.

The exact `household_timezone_at_acceptance` is retained so the derivation is
auditable after a later Household timezone change.

The selection also binds:

- `member_updated_at_at_acceptance`;
- `household_updated_at_at_acceptance`.

## 9. DECISION — Step 6A cross-context stale-read protection

The acceptance command may need to read Household/member state before opening the
selection write UoW.

It must not commit from a stale pre-read.

Before insert/commit, the write path revalidates the relevant optimistic tokens:

- `Household.updated_at`;
- `HouseholdMember.updated_at`.

A concurrent Household/member change produces conflict and zero authoritative
write.

This guarantee is mandatory even if the exact adapter/service split changes
during implementation.

## 10. DECISION — Step 6A request identity and optimistic concurrency

The acceptance command requires:

- `acceptance_request_id`;
- `expected_current_selection_id`, nullable when the caller expects no current
  selection;
- requested reference bundle.

A persisted request ID closes the ambiguity found during PR85 re-review for
commands that publish immutable selection history. Step 6A does not introduce a
second command-receipt table merely to record zero-write semantic no-ops.

### 10.1 Exact request replay

If `acceptance_request_id` already exists on a published selection for the
same Household/member:

- requested reference bundle must exactly equal the persisted command result;
- return the same selection ID/version;
- zero writes.

If the same request ID is reused with a different member/scope/bundle, fail
closed.

This is the only path allowed to bypass a stale
`expected_current_selection_id`: it is a replay of the same persisted command,
not a new optimistic write.

### 10.2 Fresh first selection

No current selection exists, caller expects none, request ID is new, and
applicability passes:

- create version 1;
- one commit.

### 10.3 Semantic no-op with current expectation

Caller expects the actual current selection, request ID is not already persisted
on a published selection, applicability passes, and requested bundle equals
current bundle:

- return the current selection;
- zero writes;
- do not create a fake history version merely because the command was repeated;
- do not persist/consume the new request ID;
- if that unconsumed request ID is later reused, treat it as a new command against
  the then-current selection rather than as historical replay.

### 10.4 Genuine change

Caller expects the actual current selection, request ID is new, applicability
passes, and requested bundle differs:

- create exactly the next immutable version;
- `supersedes_selection_id = current.id`;
- one commit.

### 10.5 Conflict

Fail with zero writes when:

- expected current ID does not match the actual current selection and this is not
  an exact request replay under section 10.1;
- a **persisted** request ID is reused with different command semantics;
- scope points to another Household/member;
- version chain is not contiguous;
- reference version is unsupported;
- Russian applicability fails;
- Household/member optimistic state token changed.

This prevents an A → B → A history from being mistaken for a direct retry merely
because the current bundle happens to equal a stale caller's requested bundle.

## 11. DECISION — Step 6A persistence schema

Step 6A is one bounded persistence task.

Expected migration:

`0036_member_reference_methodology_selection`.

Expected new table:

`member_reference_methodology_selections`.

Minimum constraints:

- PK `id`;
- FK `household_id → households.id`;
- FK `member_id → household_members.id`;
- self-FK `supersedes_selection_id`;
- unique `(household_id, member_id, version_number)`;
- unique `acceptance_request_id`;
- positive version;
- non-empty `nutrition_config_version`;
- non-empty group-reference version when non-null;
- non-empty `household_timezone_at_acceptance`.

Do not hardcode accepted methodology version strings in SQL CHECK constraints.

Step 6A does not change any MealPlan table, MealPlan repository or MealPlan UoW.

## 12. Step 6A preservation matrix

0036 must preserve:

| Surface | Preservation requirement |
| --- | --- |
| migrations 0001–0035 | exact accepted historical prefix |
| reserved 0033 | remains reserved/unconsumed |
| households | schema/data unchanged |
| household_members | schema/data unchanged |
| member_meal_pattern_selections | unchanged |
| meal_plans | schema/data/history unchanged |
| meal_plan_member_selections | unchanged |
| meal_plan_events | unchanged |
| servings | unchanged |
| FoodIngredient/Nutrition/Profile/Vector/Composition | unchanged |
| Step 5 reference table | unchanged |
| Planner | behavior/defaults unchanged |
| NASEM member target | output/default unchanged |

No historical selection rows are backfilled.

## 13. Step 6A repository / UoW boundary

Runtime 6A adds one focused driver-independent repository contract:

```text
add(selection)
get(household_id, selection_id)
get_by_request_id(household_id, member_id, acceptance_request_id)
get_current(household_id, member_id)
list_history(household_id, member_id)
```

Repository methods:

- require Household scope;
- do not expose SQLAlchemy/DBAPI types;
- do not commit independently;
- map constraint failures to stable persistence/application errors.

The Step 6A command uses one project UoW for selection write + concurrency
revalidation.

## 14. Step 6A migration / rollback contract

0036 is expected to be an additive standard migration.

Required verification:

- fresh database;
- populated accepted 0035 → 0036 upgrade;
- exact repeat/no-op;
- injected migration failure leaves no 0036 marker and no authoritative partial
  Step 6A state;
- FK check clean;
- backup restore to pre-0036 state and re-upgrade;
- migration lineage/coexistence preserved.

Operational rollback after successful deployment remains pre-upgrade
backup/restore. No destructive down migration is added.

## 15. Step 6A acceptance tests frozen by this gate

Runtime 6A must prove:

- baseline selection persists;
- Russian group-reference selection persists only when current Step 5
  applicability passes;
- age 18 fails Russian group-reference acceptance;
- unsupported/unknown sex fails Russian group-reference acceptance;
- unknown config/table version fails closed;
- request-id exact replay is zero-write and returns the original selection;
- persisted request-id reuse with changed payload fails;
- same current bundle with correct current expectation is a zero-write no-op;
- a request ID used only by a no-op is not persisted/consumed, and later reuse
  follows ordinary new-command concurrency/applicability semantics;
- stale expected-current ID fails even when current bundle happens to equal the
  requested bundle;
- A → B → A cannot be collapsed into a stale replay;
- genuine change creates the next version and exact supersedes link;
- Household/member scope isolation;
- concurrent Household timezone edit before commit fails;
- concurrent member profile edit before commit fails;
- history order is deterministic;
- no MealPlan runtime/schema behavior changes;
- existing NASEM and Planner behavior are unchanged;
- AI is not involved.

## 16. DECISION — Step 6B begins only after accepted Step 6A

Step 6B is a separate runtime task and PR.

It is not authorized merely by merging the Contract Gate.

Step 6B consumes accepted
`MemberReferenceMethodologySelection` identity from Step 6A.

Its purpose is to make MealPlan history replayable for member reference targets.

## 17. DECISION — Step 6B MealPlan pin ownership

Introduce one MealPlan-owned dependent record:

`MealPlanMemberReferenceMethodologyPin`.

Conceptual shape:

```text
MealPlanMemberReferenceMethodologyPin
- plan_id: UUIDv4
- member_id: UUIDv4
- reference_methodology_selection_id: UUIDv4

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

The pin is a dependent part of MealPlan persistence. It is not a new independent
member-selection aggregate.

The member snapshot is copied from authoritative Household state by the
application service. It is never trusted caller data.

## 18. DECISION — source-native food policy is not in the Step 6B member pin

Step 6B pins member reference selection only.

It does not add `RU_SOURCE_NATIVE_*` to the per-member pin.

When a later step starts using source-native V2 food/recipe calculations in a
plan, that owning calculation/Planner contract must persist or durably reference
one exact source-native calculation policy for the shared calculation result.

That future pin is plan/calculation-level, not member preference state.

This avoids two members assigning conflicting interpretation policy to the same
shared recipe/food nutrition truth.

## 19. DECISION — Step 6B reference date and snapshot replay

The frozen plan-level reference-target date is exactly:

`MealPlan.week_start`.

This preserves the current Planner behavior:

`member_reference_target(..., as_of_date=week_start)`.

The Step 6B pin freezes the authoritative member inputs used for that plan
revision.

Together with:

- `MealPlan.week_start`;
- immutable Step 6A selection version;
- code-owned exact reference config/table versions;

the system can later reproduce which reference inputs and methodology were used
even if current HouseholdMember data change.

This replay guarantee is intentionally limited to member reference methodology
and member reference-target inputs.

It does not claim complete historical recipe/food/transformation replay before
the later Russian-data steps are complete.

## 20. DECISION — Step 6B complete-or-zero compatibility

Existing historical MealPlans have no reference-methodology pins.

Do not invent or backfill them.

MealPlan detail must support exactly two valid states:

1. legacy/unaware revision: zero reference-methodology pins;
2. methodology-pinned revision: exactly one pin for every member already present
   in `MealPlanMemberSelection`.

A partial pin set is invalid.

The existing manual/Planner creation path may remain zero-pin for compatibility
until Step 10 explicitly integrates methodology-aware planning.

## 21. DECISION — Step 6B pin validation

When methodology pins are supplied:

- pin member set exactly equals MealPlan member-selection member set;
- referenced Step 6A selection belongs to the same Household/member;
- selection exists before plan persistence;
- selection `accepted_at` is not later than plan creation;
- member snapshot comes from authoritative HouseholdMember;
- member `updated_at` is revalidated before commit;
- if a Russian group-reference selection is pinned, its applicability is
  revalidated against the authoritative member snapshot at `MealPlan.week_start`;
- plan + meal-pattern pins + reference-methodology pins + events + Servings commit
  atomically in the existing MealPlan UoW.

There is no standalone post-commit writer for methodology pins.

## 22. DECISION — Step 6B migration

Expected migration after accepted Step 6A:

`0037_meal_plan_reference_methodology_pins`.

Expected new table:

`meal_plan_member_reference_methodology_pins`.

Minimum constraints:

- composite PK `(plan_id, member_id)`;
- FK `plan_id → meal_plans.id`;
- FK `member_id → household_members.id`;
- FK `reference_methodology_selection_id →
  member_reference_methodology_selections.id`;
- non-empty activity/goal snapshot fields under the current Household contract.

No existing MealPlan table is rebuilt.

Existing MealPlan rows are not modified.

## 23. Step 6B preservation matrix

0037 must preserve:

| Surface | Preservation requirement |
| --- | --- |
| accepted migrations through 0036 | exact prefix |
| existing MealPlan IDs/revisions | unchanged |
| existing meal-pattern pins | unchanged |
| events / Servings | unchanged |
| all legacy zero-pin plans | load identically plus empty new pin collection |
| Step 6A selection history | unchanged |
| Planner current behavior | unchanged |
| NASEM current behavior | unchanged |
| Step 5 table | unchanged |

## 24. Step 6B failure / adversarial tests frozen by this gate

Runtime 6B must cover at least:

- legacy plan loads with zero reference-methodology pins;
- complete pinned plan has one pin per plan member;
- partial pin set rejected;
- another member's selection rejected;
- another Household's selection rejected;
- unsupported Russian applicability at plan `week_start` rejected;
- member changed after snapshot pre-read but before commit → rollback;
- failure after plan insert but before methodology pins → rollback;
- failure after methodology pins but before events/Servings → rollback;
- later member changes do not alter old plan snapshot;
- later current selection changes do not alter old plan pin;
- plan revision 2 can pin a newer selection without rewriting revision 1;
- migration fresh / populated 0036 → 0037;
- migration failure/no-marker;
- backup restore/re-upgrade;
- MealPlan revision/persistence regressions;
- full backend + launcher regression;
- AI disabled.

## 25. Planner/default preservation

Neither Step 6A nor Step 6B changes current Planner behavior.

Specifically:

- `PlannerService.compose_authoritative_request` continues to call existing
  `NutritionService.member_reference_target`;
- Planner does not automatically select Russian group-reference targets;
- existing Planner generation may continue to create zero-pin plan revisions
  until Step 10;
- no API/UI methodology default changes;
- no source-native food policy default is introduced.

Step 10 consumes the accepted Step 6A/6B persistence boundary.

## 26. Verification tiers

### Step 6A runtime PR

Persistence/migration task, but no MealPlan persistence change.

Required review-ready evidence:

- Step 6A domain/service/repository/UoW tests;
- fresh/populated 0035 → 0036 migration;
- failure/no-marker;
- backup restore/re-upgrade;
- migration lineage/coexistence;
- NASEM + Russian reference regressions;
- AI disabled;
- full backend + launcher regression because shared persistence/migration lineage
  changes;
- exact final-head scope/diff/whitespace audit.

### Step 6B runtime PR

MealPlan persistence/history cross-context change.

Required review-ready evidence:

- Step 6B domain/application/persistence tests;
- MealPlan revision/history tests;
- full Step 6A selection regression;
- fresh/populated 0036 → 0037 migration;
- transaction failure injection;
- NASEM/Russian reference regression;
- Planner regression proving no default switch;
- AI disabled;
- full backend + launcher regression;
- exact final-head scope/diff/whitespace audit.

## 27. Explicit non-goals

Step 6 Contract Gate does not authorize:

- Step 6A or Step 6B runtime implementation before separate authorization;
- replacing NASEM personal targets with Russian population references;
- persisting source-native food policy as member state;
- Planner Russian-target integration;
- API/UI methodology defaults or selection UX;
- Step 7 transformation applicability;
- Step 8 recipe-dependency food batch;
- Step 9 executable Russian RecipeVersion publication;
- Step 10 Planner integration;
- adequate-level tables 13/18;
- child Russian reference tables;
- pregnancy/lactation;
- clinical/therapeutic nutrition;
- Auth/PostgreSQL/Retail/AI.

## 28. Orchestrator split decision

The earlier draft proposed one Step 6 runtime migration containing:

- a new member methodology selection identity;
- MealPlan persistence changes;
- legacy zero-pin compatibility.

That draft violated the accepted implementation stop-signal.

**DECISION:** Step 6 runtime is split into Step 6A / 0036 and Step 6B / 0037.

This Contract Gate may specify both phases because it is documentation-only and
owns their interface. Runtime delivery remains two bounded PRs with a merge/review
stop between them.

## 29. Blocker resolution ledger

### PR85 re-review blocker 1 — split signal

Resolved by mandatory Step 6A / Step 6B runtime split.

### PR85 re-review blocker 2 — source-native policy ownership

Resolved by removing `RU_SOURCE_NATIVE_*` from member selection and MealPlan
member pin. Future source-native food policy is calculation/plan-level truth.

### PR85 re-review blocker 3 — ambiguous semantic replay

Resolved by persisted `acceptance_request_id` plus ordinary
`expected_current_selection_id` optimistic concurrency.

Bundle equality alone never turns a stale new command into replay.


### PR86 re-review blocker 1 — real SQLite stale-token concurrency

Resolved by a Step-6A-specific authoritative-state CAS/write-intent guard.
The guard performs exact-token conditional no-op UPDATEs inside the same UoW
before either semantic no-op return or selection publication. A competing SQLite
writer/lock is mapped to conflict; successful guard ownership prevents a
concurrent Household/member edit from committing until the Step 6A transaction
finishes. Real two-connection SQLite verification is required.

### PR86 re-review blocker 2 — no-op request-id persistence ambiguity

Resolved by making request identity precise: `acceptance_request_id` is
persisted only when a command publishes a new immutable selection version.
Semantic no-op remains zero-write and deliberately does not consume its new
request ID. A later reuse of that unconsumed ID is a new command.

This preserves one-table Step 6A schema and avoids introducing a second persisted
command-receipt identity solely for zero-write no-ops.

## 30. Stop boundary

PR85 is Contract Gate only.

No migration, runtime table, repository/service implementation or Planner change
belongs in this PR.

After PR85 merge:

1. stop;
2. Step 6A runtime requires explicit authorization;
3. after Step 6A review/merge, stop again;
4. Step 6B runtime requires explicit authorization.

No later Russian-data step starts automatically.
