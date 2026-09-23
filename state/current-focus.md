# Current focus

Updated: `2026-09-23`.

## Accepted state

PR84 is merged into `main` at
`3de3c58ee898284f8d2168af1aae04af754a6bfc`.

Russian-data integration Steps 1–5 are accepted.

Current bounded work is **Step 6 — persisted nutrition methodology selection,
Implementation Contract Gate / adversarial preflight only**.

Canonical gate:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

## Frozen Step 6 direction

Step 6 will persist a distinct Household-owned immutable/versioned
`MemberNutritionMethodologySelection`.

The selection is a version bundle:

- required `FAMILY_FOOD_NUTRITION_V1` personal baseline;
- optional reviewed Russian group-reference version;
- optional paired explicit Russian source-native policy.

Russian group reference is additive; it does not replace NASEM personal targets.

Historical MealPlan replay requires more than a methodology ID because
`HouseholdMember` is mutable. The runtime contract therefore also requires an
immutable MealPlan/member methodology pin containing the authoritative member
reference-target input snapshot.

Existing historical plans remain valid with zero pins; no methodology is
backfilled or invented.

Expected runtime migration after gate merge:
`0036_persisted_nutrition_methodology_selection`.

Reserved `0033_recipe_template_catalogue` remains untouched.

## Current authorization

Docs/state Contract Gate only.

No 0036 migration, runtime selection tables, repository/service implementation,
Planner/API/UI default change, Step 7 transformation applicability, recipes or
later work before this gate is reviewed and merged.

## Stop boundary

Deliver/review the Step 6 Contract Gate. Runtime Step 6 requires separate explicit
authorization.
