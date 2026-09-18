# Planner v0 deterministic baseline

Status: corrected PR8 implementation contract for Issue #57. Gate 1 remains a
separate review and is not closed here.

## Boundaries and versions

The pure `app.domain.planner.generate_week` heuristic accepts an already composed
`PlannerRequest`. Production callers use
`PlannerService.generate_authoritative(AuthoritativeGenerationRequest)`, whose
caller can supply only member IDs, generation-time exclusions/preferences and
fixed events. The application service resolves current Household-scoped truth
from the existing Household, Meal Pattern/MealPlan, Recipe, Nutrition and Pantry
services before invoking the pure core. It never accepts caller assertions about
selection snapshots, RecipeVersion currency/verification, kcal/status or Pantry.

- planner/config: `planner-v0.2`;
- compatibility: `meal-role-recipe-v2`;
- recommender: `meal-pattern-recommender-v2`.

No Planner table, migration, process, AI, Retail or optimizer was introduced.
Successful generation delegates one append-only revision write to PR7
`MealPlanService`; failure is returned before any write.

## Configuration and compatibility

Versions must be non-empty lowercase version-safe identifiers. Every weight must
be a finite, non-negative `Decimal` (float is rejected), and the repetition bound
must be a positive non-bool integer.

`MealRole` remains distinct from Recipe classification. Without RecipeAssembly or
an independent standalone-meal authority, component classifications are not
promoted into whole meals. Version 2 permits:

- breakfast: `breakfast`, `sandwich`;
- lunch: `main`, `sandwich`;
- dinner: `main` only;
- snack: `sandwich` only;
- workout/other roles: unsupported and therefore bounded failure.

In particular, `salad` and `side` cannot silently become an entire dinner.

## Authoritative composition and history

The production boundary loads active Household members, each member's current
accepted selection, current active Recipes/current verified immutable versions,
authoritative RecipeVersion Nutrition, current reference-energy targets and the
Household-scoped Pantry. Pantry identities are a read-only score signal.

The bounded history horizon is exactly the current revision for the immediately
preceding semantic week (`HISTORY_HORIZON_WEEKS = 1`). Its exact plan revision ID
and immutable RecipeVersion usage counts enter the readable trace. Historical
counts affect only the soft repetition score. A separate current-week counter
both contributes to that score and alone enforces `max_recipe_repetitions`, so
last week's use cannot consume this week's hard allowance. History is never
mutated; no prior plan is deterministic empty history. The obsolete unvalidated
`previous_plan_id` input was removed.

## Reconciliation, score and Serving

For each local-date/role/occurrence opportunity, fixed non-recipe decisions are
removed first and may cover any non-empty participant subset. The remaining
members are grouped greedily: evaluate each eligible recipe's compatible member
subset, choose the largest subset, then highest score, then ascending immutable
RecipeVersion UUID; repeat until all participants are assigned or bounded failure
is proven. Thus sharedness is preferred, never mandatory, and exclusions are
never weakened.

Hard evidence codes are `NOT_VERIFIED`, `ROLE_INCOMPATIBLE`,
`MEMBER_EXCLUDED_INGREDIENT`, `NUTRITION_UNAVAILABLE` and `MAX_REPETITIONS`.
Scores are preference `+20` per member, Pantry overlap `+4` per ingredient, batch
`+2`, time `-0.01` per minute and repetition `-7` per historical/current use.
Cost stays unknown/unscored.

After selection, each member receives one six-decimal Decimal multiplier:
`7 × daily reference energy / sum(selected recipe base-serving kcal)`. Unknown or
non-positive authoritative energy yields bounded failure; fixed non-recipe
nutrition is not credited.

## Trace and recommender

The readable trace exposes Household/week, member→selection pins, config and
compatibility versions, exact history plan IDs, applied exclusions, candidate
pool, exact recent RecipeVersion usage, compatible and excluded participant
groups, rejections, score components/totals,
selected RecipeVersions, final/fixed source events, warnings and explicit failure
code/reason. SHA-256 covers all deterministic fields. Diagnostic duration is
reported separately and excluded from the fingerprint.

`MealPatternRecommenderService` reads only the catalogue's current published,
eligible programs. Evidence per result contains program/version IDs, deterministic
score, only actually matched authoritative tag reasons, and cautions. It cannot
activate a program; acceptance remains PR7 `accept_member_pattern`. Medical input
and missing/unsafe eligibility return unsupported states.

## Gate 1 fixture and limitations

The checked-in repository fixture invokes `generate_authoritative` over three
real migrated SQLite Households, persisted members/current selections, Recipe,
Nutrition, Pantry and prior-MealPlan repositories. It observes 30 verified
recipes and 80+ FoodIngredients. All 30 authoritative
RecipeVersion Nutrition results remain `INCOMPLETE` with unknown kcal, so the
three materially different fixture households truthfully return reproducible
`NO_ELIGIBLE_CANDIDATE` without a partial revision. Synthetic tests prove the
successful shared, deterministic split, subset-fixed and individualized Serving
paths. This does not complete Gate 1; authoritative nutrition/data readiness must
be corrected in separately authorized work.
