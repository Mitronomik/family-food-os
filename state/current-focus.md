# Current focus

Updated: `2026-09-17`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- PR #31–#45 remain accepted historical research/governance evidence.
- PR #46 is MERGED; `main` includes the dataset-independence and web-corroboration governance correction.
- Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` = COMPLETE through merged PR #51.
- Accepted `main` after PR #51: `0648d9483bd9261451194668c274b3c08ad716b3`.
- Accepted SQLite migration head: `0031_meal_pattern_catalogue`.
- The canonical post-PR51 sequencing decision is `docs/family-food/master-roadmap-addendum-2026-09-17-post-pr51.md`.
- Migration `0032` is reserved for the next authorized PR7 MealPlan / Serving persistence change; the future RecipeTemplate reservation moves to `0033_recipe_template_catalogue`.

## Current authorized operation

`POST-PR51-STATE-SYNC` is the only active operation.

Goal: synchronize repository roadmap/state after merged PR #51 and persist the approved migration-number reservation without changing runtime, schema, seed data or product behavior.

Scope:

- record Issue #47 / PR #51 as COMPLETE;
- record accepted `main` and migration head `0031_meal_pattern_catalogue`;
- identify PR7 MealPlan / Serving as the next functional milestone;
- reserve migration number `0032` for PR7;
- move the future RecipeTemplate reservation to `0033_recipe_template_catalogue`;
- update continuation state for the next agent.

## Next functional operation

`PR7 — MealPlan / Serving` is **NEXT / NOT STARTED**.

PR7 implementation is not authorized by this docs-only synchronization. It requires a separate explicit user authorization after this state-sync PR is reviewed and merged.

When authorized, PR7 will own Household-owned accepted planning state, including `MemberMealPatternSelection`, manually constructible MealPlan/Serving structures and member participation/portion allocation. It must consume the published Meal Pattern Catalogue without moving PR8 Planner ranking/recommendation logic forward.

## Architecture boundary

- `MealPatternProgram` remains platform-owned catalogue truth.
- `MemberMealPatternSelection` remains Household-owned state owned by PR7.
- `MealRole != RecipeVersion.meal_type_code`.
- Nutrition Engine remains authoritative for nutrient targets/calculations.
- The initial product must represent heterogeneous member schedules and one to six meal opportunities without making `6` a permanent schema maximum.
- Technical ingredient/recipe/nutrition datasets and seed corpora remain replaceable external/bootstrap evidence artifacts.
- No Planner ranking, Shopping, Prep, Retail, AI, Auth/shared deployment or frontend work is authorized by this sync.

## Active sequence

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         COMPLETE (#47 / PR #51)
→ POST-PR51-STATE-SYNC                       ACTIVE
→ PR7 MealPlan / Serving                     NEXT / NOT STARTED
→ PR8 Planner v0                             NOT STARTED
→ GATE 1 — Planning Core                     NOT STARTED
```

After this docs/state synchronization is reviewed and merged, stop. Do not begin PR7 automatically.
