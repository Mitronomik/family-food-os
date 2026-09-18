# Current focus

Updated: `2026-09-18`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` = COMPLETE through merged PR #51.
- PR #52 / `POST-PR51-STATE-SYNC` = COMPLETE.
- PR7 / Issue #53 = COMPLETE through merged PR #54.
- Accepted `main`: `3b1c8393c22461a1570d664ba5dcb035ec6cf633`.
- Accepted SQLite migration head: `0032_meal_plan_serving`.
- Future RecipeTemplate reservation remains `0033_recipe_template_catalogue`.

## Current authorized operation

No product implementation milestone is currently authorized.

This post-PR54 state synchronization records the accepted PR7 result only. It does not authorize PR8 implementation.

## Next eligible milestone

`PR8 — Planner v0` is NEXT / NOT STARTED.

PR8 requires a separate explicit user authorization and bounded task contract before implementation begins.

The next planning sequence is:

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         COMPLETE (#47 / PR #51)
→ POST-PR51-STATE-SYNC                       COMPLETE (#52)
→ PR7 MealPlan / Serving                     COMPLETE (#53 / PR #54)
→ PR8 Planner v0                             NEXT / NOT STARTED
→ GATE 1 — Planning Core                     NOT STARTED
```

## Architecture boundary carried forward

- `MealPatternProgram` remains platform-owned catalogue truth.
- `MemberMealPatternSelection` remains Household-owned accepted state.
- `MealRole != RecipeVersion.meal_type_code`.
- `Recipe != Serving`.
- Nutrition Engine remains authoritative for nutrient truth.
- unknown nutrition/cost/supply remains unknown.
- true instants are UTC; planning dates are Household-local calendar dates.
- every Household-owned read/write remains Household-scoped.
- deterministic core works with `AI_ENABLED=false`.

## Stop condition

After this state-sync PR is reviewed and merged, stop.

Do not begin PR8 automatically. PR8 requires separate explicit authorization.
