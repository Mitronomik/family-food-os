# Handoff

Updated: `2026-09-17`.

## Accepted base and governance

`main` includes merged PR #46. The verified implementation base for Issue #47 is:

`dbacd07453c4939f703d01f1bbc7897c0a3162eb`

The 2026-09-16 addendum is canonical: technical ingredient/recipe/nutrition datasets are replaceable bootstrap/evidence artifacts; Recipe Constructor validation uses deterministic checks plus web corroboration; mandatory personal kitchen execution is not a Planning Core prerequisite.

PR #31–#45 remain historical evidence and must not be rewritten to hide the old policy.

## Active operation

Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` is the only active milestone operation.

Branch: `feature/pr7-support-meal-pattern-catalogue`.

The operation introduces platform-owned immutable/versioned Meal Pattern Catalogue truth with deterministic validation, Russian display text, structured age/eligibility, ordered semantic meal opportunities, provenance/evidence, SQLAlchemy Core persistence and the next forward migration `0031_meal_pattern_catalogue`.

The accepted `main` migration head before this operation is `0030_recipe_source_corpus`. The old unused RecipeTemplate reservation moves to `0032_recipe_template_catalogue`; no existing migration history is rewritten.

Initial curated catalogue data is intentionally small and adult-only (19+). It is a reviewed seed artifact, not an architecture invariant. USDA/NESR evidence is used to preserve uncertainty about meal/snack frequency rather than to claim one frequency is universally superior.

Child catalogue eligibility must fail closed until separate age-specific evidence and an approved program exist.

## Non-goals / stop conditions

Do not add or start:

- `MemberMealPatternSelection` (PR7 owns it);
- MealPlan / MealSlot / Serving;
- Planner ranking/recommendation logic;
- Recipe Constructor / Assembly implementation;
- Shopping / Prep / Retail;
- AI Gateway;
- Auth/shared deployment;
- frontend/onboarding UI.

After #47 is review-ready and merged, stop. PR7 requires separate explicit user authorization.
