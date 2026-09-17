# Current focus

Updated: `2026-09-17`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- PR #31–#45 remain accepted historical research/governance evidence.
- PR #46 is MERGED; `main` includes the dataset-independence and web-corroboration governance correction.
- Verified implementation base for the current operation: `dbacd07453c4939f703d01f1bbc7897c0a3162eb`.
- Accepted SQLite migration head on `main` at that base is `0030_recipe_source_corpus`.
- `0031_recipe_template_catalogue` was only an unused reservation; the current operation uses `0031_meal_pattern_catalogue`. Future RecipeTemplate work is therefore reserved as `0032_recipe_template_catalogue` unless a later approved decision changes it.

## Current authorized operation

`PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` (Issue #47) is ACTIVE on `feature/pr7-support-meal-pattern-catalogue`.

Goal: establish platform-owned immutable/versioned `MealPatternProgram` truth that downstream PR7/PR8 can consume without inventing meal-frequency policy inside MealPlan or Planner.

The bounded implementation includes:

- deterministic Meal Pattern domain validation;
- stable program identity plus immutable version snapshots;
- lifecycle `DRAFT / PUBLISHED / INACTIVE`;
- Russian consumer text;
- explicit age/eligibility metadata;
- ordered semantic meal opportunities where the same role may repeat at different positions;
- provenance/evidence and review metadata;
- synchronous SQLAlchemy Core repositories/UoW;
- migration `0031_meal_pattern_catalogue`;
- a small reviewed adult wellness/schedule seed.

Current seed evidence is based on USDA/NESR 2025-DGAC systematic reviews that do not support a universal claim that a particular meal/snack frequency is superior for diet quality or energy intake. The seed therefore treats frequency as a planning schedule, not a therapeutic or outcome promise.

Children are intentionally unsupported by the initial automated catalogue: the reviewed seed starts at age 19. No adult program may be silently inherited by a child.

## Architecture boundary

This operation does **not** add `MemberMealPatternSelection`, MealPlan, MealSlot, Serving, Planner ranking, Recipe Constructor/Assembly, Shopping, Retail, AI, Auth or frontend UI.

`MealPatternProgram` is platform-owned. Future `MemberMealPatternSelection` remains Household-owned state in PR7.

Technical ingredient/recipe/nutrition datasets and seed corpora remain replaceable external/bootstrap evidence artifacts. They do not define FamilyFoodOS domain invariants.

## Active sequence

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         ACTIVE (#47)
→ PR7 MealPlan / Serving                     NOT STARTED
→ PR8 Planner v0                             NOT STARTED
→ GATE 1 — Planning Core                     NOT STARTED
```

After #47 is reviewed and merged, stop. PR7 starts only with separate explicit authorization.
