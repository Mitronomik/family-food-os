# Planner Energy Allocation — Implementation Contract Gate

**Status:** docs-only Implementation Contract Gate
**Decision date:** 2026-09-27
**Accepted base:** `cf96e9bb43bb991625a56d7d4c0fa0bad2842b1a` (merged PR #106; includes accepted PR #104 runtime plus post-merge integrity correction)
**Parent:** #100, #99, #67
**Runtime authorized by this document:** no — review/merge this gate first.

## 1. Goal

Close the Planner energy-allocation defect that blocks R1-C.

Current `planner-v0.3` scales every recipe-backed Serving for a member using:

```text
7 × member reference energy
÷
sum(base-serving kcal of selected recipe events)
```

Fixed non-recipe events are not credited.

That is not safe for valid FamilyFoodOS scenarios such as dinner-only at home,
breakfast + dinner, mixed `EAT_OUT` / `READY_MEAL` days, or heterogeneous
member schedules.

The goal of the next runtime PR is to make energy allocation deterministic,
versioned, explainable and compatible with partial-at-home planning without
inventing nutrition truth.

## 2. FACT — current persisted model cannot represent allocation truth

The current platform Meal Pattern model persists:

- program/version identity;
- opportunity role/order;
- eligibility/tags/evidence.

The current Household selection persists:

- accepted program/custom identity;
- resolved weekday opportunity role/order;
- selection history.

Neither model persists a per-opportunity energy allocation share.

Therefore the current accepted schedule can answer **which opportunities Planner
owns**, but not **what fraction of reference energy each opportunity is intended to
cover**.

Issue #100 explicitly requires the implementation to stop for an Implementation
Contract Gate if the persisted selection/config cannot represent the required
allocation truth. That condition is met.

## 3. FACT — product and architecture constraints

The following remain unchanged:

- reference energy is Nutrition-owned;
- Meal Pattern owns schedule/allocation policy, not Nutrition formulas;
- Planner consumes accepted Meal Pattern state;
- `RecipeVersion != Serving`;
- fixed/non-recipe meal sources may be legitimate;
- unknown fixed-source nutrition remains unknown;
- `AI_ENABLED=false` must work;
- historical MealPlans are versioned and must not silently recalculate;
- no medical/therapeutic claim is introduced.

R1-C remains blocked until #100 is closed. Shopping/PR9 remains blocked until
R1-C / DATA-CORPUS-V1 / Gate1-CLOSE.

## 4. FACT — external evidence boundary

The bounded evidence review confirms that official Rospotrebnadzor material uses
role-based distribution of daily energy as a nutrition-planning concept.

Reviewed policy references:

1. FBUZ Center for Hygiene Education of the Population, Rospotrebnadzor,
   `Тема_3 Как составить здоровый рацион`:
   `https://cgon.rospotrebnadzor.ru/upload/docs/Тема_3_Как_составить_здоровый_рацион.pdf`
   - breakfast 20–30%;
   - lunch 30–35%;
   - dinner 20–25%;
   - snacks 5–15%.
2. FBUZ Center for Hygiene Education of the Population, Rospotrebnadzor,
   `Курс на здоровое питание` bulletin:
   `https://cgon.rospotrebnadzor.ru/upload/pdf/pechatnaya_produktsiya/byulleten_a2.pdf`
   - breakfast 25–30%;
   - lunch 30–35%;
   - dinner 20–25%;
   - snacks 5–15%.

Reviewed for this contract on 2026-09-27.

These materials support the general planning concept and bounded role ranges.
They do **not** establish one universal physiologically optimal exact percentage
for every adult, child, goal, schedule or custom pattern.

They also do not authorize FamilyFoodOS to silently choose the midpoint or another
exact number from a published range.

**DECISION:** exact persisted shares are versioned **planning-policy parameters**,
not medical facts. Every automatically published PROGRAM share must be explicitly
selected/reviewed in a versioned FamilyFoodOS curation payload with its evidence
reference and review rationale. The external range is evidence for that decision,
not an executable formula.

User-confirmed PROGRAM overrides and CUSTOM shares are Household planning choices;
they are not promoted to platform scientific evidence and must not be presented as
measured physiological truth.

## 4.1. Dependency inventory

The runtime implementation may change only the following bounded seams.

### Nutrition-owned input

- `NutritionService.member_reference_target(...).reference_energy_kcal`;
- existing reference-methodology selection/pins remain authoritative;
- no new reference-energy formula is introduced.

### Meal Pattern Catalogue

- `MealPatternProgramVersion`;
- `MealPatternOpportunity`;
- reviewed program evidence/provenance;
- a bounded trusted target-version reconcile operation for new immutable allocation-ready program versions.

### Household-owned accepted pattern

- `MemberMealPatternSelection`;
- `MemberMealPatternOpportunitySnapshot`;
- immutable selection revision history;
- `MealPlanMemberSelection` pins.

### Planner

- `MemberPlannerConstraints`;
- `FixedPlannerEvent`;
- `PlannerConfig`;
- pure `generate_week()`;
- Planner trace/fingerprint;
- `PlannerService.generate_authoritative()` persistence only after pure success.

### Recipe Nutrition

- existing exact `kcal_per_base_serving` / `exact_energy_ready` candidate input;
- no Recipe Nutrition formula/version change.

### Persistence / migration

- migration `0041_meal_pattern_energy_allocation`;
- `meal_pattern_opportunities`;
- `member_meal_pattern_opportunities`;
- existing Meal Pattern and MealPlan UnitOfWork boundaries.

No new bounded context or network service is introduced.

## 5. DECISION — allocation belongs to resolved Meal Pattern opportunities

Add an optional exact planning share to each opportunity:

```text
energy_share: Decimal | None
```

Meaning:

> fraction of the member's daily reference energy that this accepted planning
> opportunity is intended to cover.

Rules:

- Decimal, never float;
- `0 < energy_share <= 1` when present;
- shares are attached to an opportunity, not inferred only from role name;
- duplicate roles (for example two snacks) may have different shares;
- total planned share for one local day must be `> 0` and `<= 1`;
- `1 - sum(planned shares)` is explicit energy outside Planner scope;
- a total below 1 is valid for partial-at-home planning;
- a total above 1 is invalid;
- missing share is unsupported for automatic Planner Serving allocation;
- Planner must never fall back to “allocate all remaining daily energy”.

This directly supports dinner-only and breakfast-only configurations without
pretending those planned meals represent the full day.

## 6. DECISION — platform program vs Household selection

### MealPatternProgram

Published curated program opportunities may carry reviewed `energy_share`
planning policy.

Program versions are immutable. Existing published versions are not rewritten.

If current programs need allocation shares, append new reviewed program versions;
do not mutate their accepted v1 history.

### MemberMealPatternSelection

The accepted/resolved selection must freeze the effective `energy_share` for
each weekday opportunity.

For a PROGRAM selection **without user overrides**:

```text
published program version
→ canonical resolved schedule
→ copy each exact program opportunity share by template position
→ immutable Household selection
```

No role-name matching is used to infer shares.

For a PROGRAM selection **with user overrides**:

- the published program shares are not automatically remapped onto the modified
  schedule;
- the caller must supply an explicit user-confirmed `energy_share` for every
  resolved weekday opportunity;
- removing, adding, reordering or duplicating roles does not trigger proportional
  redistribution or role-based inference;
- the resulting exact shares are frozen in the new immutable selection version.

For a CUSTOM selection:

- the caller must supply an explicit user-confirmed `energy_share` for every
  resolved weekday opportunity;
- #100 v0.4 does **not** introduce a hidden product/default allocation policy for
  CUSTOM schedules;
- runtime must not invent an equal split merely because N opportunities exist;
- missing custom allocation produces an unsupported Planner state.

Allocation provenance is derivable from already-persisted selection identity:

```text
PROGRAM + has_user_overrides=false
→ PROGRAM_VERSION:<program_version_id>

PROGRAM + has_user_overrides=true
→ USER_CONFIRMED_PROGRAM_OVERRIDE:<selection_id/version>

CUSTOM
→ USER_CONFIRMED_CUSTOM:<selection_id/version>
```

Therefore migration 0041 does not need an additional allocation-policy identity
column for this bounded v0.4 contract. If a future automatic/default CUSTOM
allocation policy is introduced, it requires a separately versioned persisted
policy identity and a new Contract Gate.

This allows future program evolution without changing an already accepted
Household selection and keeps replay/provenance unambiguous.

## 7. DECISION — expected schema change

The next migration is reserved for this bounded contract:

```text
0041_meal_pattern_energy_allocation
```

Expected additive/rebuild-compatible fields:

```text
meal_pattern_opportunities.energy_share TEXT NULL
member_meal_pattern_opportunities.energy_share TEXT NULL
```

using `DecimalText()` in SQLAlchemy metadata.

Row-level SQL/domain rules:

- null is allowed for historical/unallocated rows;
- when present, the value must be numeric and satisfy `0 < energy_share <= 1`;
- no float persistence path;
- the per-day aggregate `sum(energy_share) <= 1` is a domain/service invariant
  because it spans multiple rows and must not be faked as a per-row SQL CHECK.

Historical rows remain null.

No historical selection is silently backfilled from role names.

If implementation proves additional persisted state is required, stop and amend
this contract before expanding schema.

## 8. DECISION — Planner v0.4 allocation

The behavior change requires:

```text
planner-v0.3
→ planner-v0.4
```

`meal-role-recipe-v2` role compatibility remains unchanged unless a separate
review proves otherwise.

For each member / local day / planned opportunity, Planner reads only the
`energy_share` frozen in the accepted `MemberMealPatternSelection` snapshot.
It never re-reads current program shares for an already accepted selection.

```text
allocated_kcal
=
reference_energy_kcal
× accepted_selection_opportunity.energy_share
```

For a recipe-backed event:

```text
portion_servings
=
allocated_kcal
÷ recipe_kcal_per_base_serving
```

with existing Decimal/bounded-rounding rules.

There is no longer one weekly global factor that forces the recipe subset to absorb
100% of reference energy.

## 9. DECISION — fixed/non-recipe events

A fixed event occupies the allocation share of the accepted opportunity.

Example:

```text
Lunch share 0.35
→ fixed EAT_OUT lunch
→ 0.35 remains outside recipe Serving allocation

Dinner share 0.25
→ planned recipe dinner
→ dinner Serving targets 25% of reference energy
```

This is **allocation accounting**, not a claim that the fixed lunch actually
contained exactly 35% of daily energy.

Current #100 does not add authoritative fixed-source Nutrition.

If fixed-source Nutrition is unknown:

- MealPlan Nutrition stays incomplete for that event;
- Planner does not transfer its share to another recipe event;
- trace records that the share is reserved by an unknown-nutrition fixed source.

A future authoritative fixed-source Nutrition model may replace policy allocation
with known nutrition only under a separately reviewed contract.

## 10. DECISION — unsupported behavior

Add a bounded Planner failure for missing allocation truth, conceptually:

```text
MISSING_ENERGY_ALLOCATION
```

Planner must fail explicitly when:

- a planned opportunity lacks `energy_share`;
- a member/day share total is invalid;
- allocation state cannot be reconciled with the accepted selection.

It must not:

- use 100% daily energy as fallback;
- equal-split opportunities silently;
- infer shares from role names at Planner runtime;
- use LLM output;
- weaken the accepted schedule.

## 11. DECISION — trace and reproducibility

Planner trace must record enough allocation evidence to explain every Serving.

At minimum per member/day/opportunity:

- selection ID;
- role / occurrence;
- energy share;
- allocated kcal;
- source kind;
- recipe kcal/base serving when applicable;
- resulting portion multiplier when applicable.

Trace also records:

- Planner config version;
- allocation-policy source derived from the pinned selection semantics above;
- explicit outside-Planner residual share;
- fixed-source unknown-nutrition warning where applicable.

Identical authoritative inputs must produce identical allocation and trace
fingerprints.

## 12. DECISION — historical preservation

Historical `planner-v0.3` MealPlans remain historical truth.

They are not recalculated or rewritten after v0.4 exists.

New v0.4 generation requires allocation-complete accepted member selections.

A Household with an older null-allocation selection must create/accept a new
selection version before v0.4 automatic generation.

## 13. Initial data policy

The runtime PR may append reviewed MealPatternProgram versions that include
allocation shares needed by the bounded acceptance fixtures.

Requirements:

- retain exact evidence/provenance;
- document that shares are planning policy;
- keep values within/reconcilable with reviewed official guidance;
- no universal-health superiority claim;
- no silent backfill of existing program versions.

Do not expand the Meal Pattern catalogue beyond what #100 acceptance actually
needs.

## 13.1. Preservation matrix

| Surface | Before 0041 | After 0041 | Preservation rule |
| --- | --- | --- | --- |
| Historical MealPatternProgram v1 | roles/order only | shares null | never rewrite accepted v1 |
| New reviewed PROGRAM version | n/a | exact reviewed shares | append immutable version only |
| Historical MemberMealPatternSelection | roles/order only | shares null | no guessed backfill |
| New PROGRAM selection | resolved roles/order | frozen exact shares | snapshot from exact program version unless overridden |
| New PROGRAM override | resolved override schedule | explicit user-confirmed shares | no role remap/inference |
| New CUSTOM selection | custom schedule | explicit user-confirmed shares | no product-default/equal split |
| Historical MealPlan planner-v0.3 | persisted revision/config | unchanged | never recalculate/rewrite |
| RecipeVersion / Recipe Nutrition | current immutable truth | unchanged | no formula/schema change |
| Fixed non-recipe event Nutrition | unknown when unsupported | remains unknown | allocation share is not Nutrition truth |
| Planner role compatibility | meal-role-recipe-v2 | unchanged | separate gate required to change |
| Hard exclusions | current deterministic filter | unchanged | always dominate sharedness/allocation |

## 13.2. Fresh / replay / conflict semantics

### Program publication

Current `MealPatternCatalogueService.append_trusted_version()` always appends a
new version and therefore is **not** an idempotent trusted publication path for
allocation-ready program truth. Current `reconcile_seed()` only reconciles the
initial v1 seed.

**DECISION:** #100 runtime must add a bounded trusted **target-version reconcile**
operation for the allocation-ready program versions. It must not call
`append_trusted_version()` repeatedly and treat the resulting new versions as
replay.

For each bounded allocation program publication payload, the payload pins:

- program code;
- exact target version number;
- lifecycle/review timestamps;
- roles/order;
- exact `energy_share` values;
- evidence references and review rationale;
- expected previous version identity.

Semantics:

- if the target version does not exist and the expected previous version matches,
  publish the complete new version atomically;
- if the target version already exists and every immutable field/opportunity/share/
  evidence fact matches, return exact replay with zero writes;
- if the target version exists but any fact differs, fail closed;
- if the expected previous version/history differs, fail closed;
- no update-in-place of a published program opportunity is allowed;
- ordinary `append_trusted_version()` behavior remains unchanged for callers
  outside this bounded trusted-reconcile path.

The initial #100 runtime payload may target the next versions of the two currently
published adult programs only if those exact versions/shares/evidence are included
in the reviewed curation payload. It must not assume “next version” dynamically
at execution time.

### Household selection

Accepting allocation-complete state creates a new immutable
`MemberMealPatternSelection` revision.

- PROGRAM/no override copies exact shares from the pinned program version;
- PROGRAM override and CUSTOM require complete explicit shares in the acceptance
  command;
- concurrent or invalid revision lineage remains a persistence conflict;
- re-accepting the same user choice is a new explicit selection revision, not a
  hidden zero-write replay.

### Planner replay

Deterministic replay means:

```text
same authoritative Household state
+ same pinned MemberMealPatternSelection revisions
+ same reference-energy inputs/methodology
+ same candidate/fixed-event inputs
+ same PlannerConfig
→ same semantic events
→ same portion multipliers
→ same allocation trace/fingerprint
```

Wall-clock duration and newly generated persistence IDs are not part of the
semantic replay claim.

Reading a historical `planner-v0.3` MealPlan never invokes v0.4 allocation and
never creates a replacement plan automatically.

## 13.3. Transaction ownership and failure injection

No new cross-context shared write transaction is introduced by #100.

### Meal Pattern program publication

Uses the existing Meal Pattern Catalogue UnitOfWork. A fresh program version and
its opportunity rows must commit atomically.

Required failure injection:

- after version insert / before all opportunity rows;
- during an opportunity insert;
- at commit.

Failure leaves no partial new program version/opportunity set.

### Member selection acceptance

Uses the existing MealPlan UnitOfWork that owns Household selection persistence.

A selection row plus all seven-day opportunity snapshots/shares commit atomically.

Required failure injection:

- after selection row / before opportunity rows;
- during opportunity persistence;
- concurrent revision conflict;
- commit failure.

Failure leaves the previous current selection and its history unchanged.

### Planner / MealPlan

`generate_week()` remains pure and writes nothing.

`PlannerService.generate_authoritative()` persists a MealPlan revision only after
pure Planner success. Missing/invalid allocation must return failure before
MealPlan persistence.

Existing MealPlan UnitOfWork atomicity remains authoritative for plan/events/
servings/pins. Failure during persistence must roll back the complete new plan
revision.

### Migration 0041

Migration runner owns schema/marker atomicity.

Required checks:

- fresh database;
- populated 0040 → 0041 upgrade;
- injected failure after the first schema mutation;
- migration marker rollback;
- backup/restore/re-upgrade;
- historical row equality plus new null fields;
- clean foreign keys and preserved indexes/constraints.

## 14. Adversarial acceptance tests

Runtime implementation must cover at least:

1. dinner-only planned-at-home opportunity with residual energy outside Planner;
2. breakfast + dinner with explicit shares;
3. three planned meals;
4. fixed `EAT_OUT` lunch + planned dinner;
5. two members with materially different patterns/shares;
6. fixed source with unknown Nutrition;
7. missing opportunity allocation → explicit failure;
8. daily share total > 1 → validation failure;
9. duplicate role occurrences with independent shares;
10. PROGRAM override that removes/adds/reorders roles requires explicit shares and performs no role-based remapping;
11. CUSTOM selection requires explicit user-confirmed shares for every opportunity;
12. exact deterministic replay;
13. persisted historical `planner-v0.3` plan remains unchanged/readable;
14. v0.4 trace exposes shares, allocated kcal, residual and allocation source;
15. hard exclusions still dominate candidate selection;
16. no LLM dependency;
17. exact PROGRAM publication replay is zero-write and changed share/evidence conflicts;
18. selection failure after parent-row insertion rolls back every opportunity/share;
19. concurrent selection revision conflict leaves prior history unchanged;
20. Planner allocation failure persists no MealPlan revision;
21. migration 0041 mid-flight failure restores schema/data/marker and deterministic re-upgrade.

Serving multipliers must remain positive and bounded by existing Decimal precision.

## 15. Verification tier

Because runtime will change persisted Meal Pattern/selection truth and Planner
Serving semantics, required implementation verification is broad:

- domain validation;
- migration fresh/upgrade/restore/rollback;
- Meal Pattern catalogue persistence + allocation publication replay/conflict;
- MemberMealPatternSelection persistence + rollback/concurrency;
- Planner focused/adversarial tests;
- MealPlan/Serving integration;
- historical planner-v0.3 replay/readability;
- R1-C prerequisites;
- full backend regression;
- launcher regression;
- reviewed allocation curation payload/evidence audit;
- Docs + relevant nutrition/Meal Pattern workflows;
- `AI_ENABLED=false`.

Any runtime change after exact-head verification invalidates that receipt.

## 16. Non-goals

This gate does not authorize:

- R1-C itself;
- Recipe activation/transformation authority work;
- new Food/Nutrition authority;
- fixed-source exact Nutrition model;
- Shopping/PR9;
- Prep/Freezer;
- Retail;
- AI;
- Auth/PostgreSQL;
- consumer UI;
- medical diet logic.

## 17. Sequence after this gate

```text
PR104 R1-B merged
→ PR106 post-merge integrity correction merged
→ #100 energy-allocation Contract Gate
→ explicit #100 runtime authorization
→ migration 0041 + Planner v0.4 allocation
→ review/merge
→ R1-C production Planner proof
→ R2/R3/... corpus expansion
→ DC4 / Gate1-CLOSE
→ PR9 Shopping
```

Do not begin the next arrow merely because the previous PR is review-ready.
