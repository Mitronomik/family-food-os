# Planner Energy Allocation — Implementation Contract Gate

**Status:** docs-only Implementation Contract Gate  
**Decision date:** 2026-09-27  
**Accepted base:** `75e2854eff82955b5c01ccacaca35fe0fdc534bc` (merged PR #104)  
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

Official Rospotrebnadzor materials support the general idea that daily energy is
distributed across eating occasions and provide role-specific ranges/examples.

Relevant retained references for review include:

- Rospotrebnadzor / FBUZ CGON, healthy-ration material:
  breakfast 20–30%, lunch 30–35%, dinner 20–25%, snacks 5–15%;
- Rospotrebnadzor materials for organized three-meal patterns:
  breakfast 25–30%, lunch 35–45%, dinner 25–30%;
- other official organized-meal guidance uses similar role-based distributions.

These sources do **not** establish one universal physiologically optimal exact
percentage for every adult/child/goal/schedule.

**DECISION:** exact persisted shares are versioned **planning-policy parameters**,
not medical facts. They must be reviewable against the program evidence and must
not be presented as measured physiological truth.

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

For a PROGRAM selection:

```text
published program version
→ resolved schedule
→ copy exact opportunity share
→ immutable Household selection
```

For CUSTOM selection:

- the effective opportunity shares must be explicitly supplied by a reviewed
  product/default policy or by an explicit user-confirmed override;
- runtime must not invent an equal split merely because N opportunities exist;
- unresolved custom allocation produces an unsupported Planner state.

This allows future program evolution without changing an already accepted
Household selection.

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

For each member / local day / planned opportunity:

```text
allocated_kcal
=
reference_energy_kcal
× opportunity.energy_share
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
- allocation-policy version/source;
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
10. exact deterministic replay;
11. persisted historical `planner-v0.3` plan remains unchanged/readable;
12. v0.4 trace exposes shares, allocated kcal and residual;
13. hard exclusions still dominate candidate selection;
14. no LLM dependency.

Serving multipliers must remain positive and bounded by existing Decimal precision.

## 15. Verification tier

Because runtime will change persisted Meal Pattern/selection truth and Planner
Serving semantics, required implementation verification is broad:

- domain validation;
- migration fresh/upgrade/restore/rollback;
- Meal Pattern catalogue persistence;
- MemberMealPatternSelection persistence;
- Planner focused/adversarial tests;
- MealPlan/Serving integration;
- historical planner-v0.3 replay/readability;
- R1-C prerequisites;
- full backend regression;
- launcher regression;
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
