# PR7 — MealPlan / Serving implementation contract

**Status:** ACTIVE implementation contract for Issue #53
**Accepted base:** `ded1cca29e165e0c459288d8de58df114abdeabb`
**Migration reservation:** `0032_meal_plan_serving`

PR7 introduces Household-owned accepted meal-pattern selection history and a manually constructible, revisioned seven-day MealPlan with explicit meal sources and individualized Servings.

Canonical invariants:

- `MealPatternProgram` remains platform-owned catalogue truth.
- `MemberMealPatternSelection` is Household-owned immutable/versioned accepted state.
- A PROGRAM selection pins an exact published program version and also stores the resolved accepted seven-day schedule snapshot; CUSTOM stores only the resolved Household-owned schedule.
- The initial product validates one to six opportunities/day, but the persistence schema does not encode six as a permanent maximum.
- `MealRole != RecipeVersion.meal_type_code`.
- MealPlan revisions are append-only; authoritative changes create a new revision rather than rewriting history.
- Household meal events have explicit source kinds; `COOK_RECIPE` pins an immutable RecipeVersion, while non-recipe source kinds never require a fake RecipeVersion.
- A Serving is a member-specific positive Decimal allocation and defines participation in an event.
- Serving/member/day/week nutrition scales existing Nutrition truth; unknown source nutrition remains unknown rather than zero.
- Every Household-owned persistence operation is Household-scoped.
- PR7 does not implement Planner ranking/recommendation/reconciliation automation, Shopping, Prep, Retail, AI, Auth or frontend.

The final implementation and verification evidence belong to the PR/Issue #53 delivery report.
