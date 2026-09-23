# Current focus

Updated: `2026-09-23`.

## Accepted state

PR84 is merged into `main` at
`3de3c58ee898284f8d2168af1aae04af754a6bfc`.

Russian-data integration Steps 1–5 are accepted. Step 5 publishes the reviewed
48-row Russian adult micronutrient group-reference table without changing
Planner/API/UI defaults.

Current bounded work is **Step 6 — persisted nutrition methodology selection,
Implementation Contract Gate / adversarial preflight only**.

## Step 6 goal

Freeze the household-owned persistence/replay contract for explicitly selected
nutrition methodology versions before any Step 6 runtime migration or service
implementation.

The gate must define at least:

- methodology-selection ownership and exact version components;
- separation from `MemberMealPatternSelection`;
- historical MealPlan pinning semantics;
- member input snapshot needed to reproduce reference-target calculations;
- migration/schema impact and preservation of existing plans;
- fresh/replay/conflict/rollback behavior;
- Planner/default preservation;
- adversarial acceptance tests and proportional verification.

## Critical preflight findings

1. Storing only a methodology string on mutable `HouseholdMember` is
   insufficient for historical replay.
2. Existing NASEM target calculation depends on birth date, sex, height, weight,
   activity, goal and explicit calculation date/config version.
3. Existing MealPlan revisions pin meal-pattern selections but do not pin a
   nutrition methodology selection or the member calculation-input snapshot.
4. Step 6 therefore requires an explicit immutable/versioned household-owned
   methodology-selection contract plus an immutable MealPlan/member pin boundary.
5. The accepted SQLite migration chain ends at `0035`; reserved
   `0033_recipe_template_catalogue` remains reserved and must not be reused.

## Current authorization

Docs/state Contract Gate only.

Do not create migration `0036`, runtime tables, repositories/services, Planner
integration, API/UI defaults, transformation applicability, recipe publication or
Step 7+ before this gate is reviewed and merged.

## Stop boundary

Deliver and review the Step 6 Contract Gate. Runtime Step 6 requires separate
explicit authorization after the gate merges.
