# Planner v0 deterministic baseline

Status: PR8 implementation contract. Gate 1 remains a separate review and is
not closed by this document.

## Boundary and versions

`app.domain.planner` owns driver-independent request, result, configuration and
trace values plus the bounded heuristic. `app.services.planner` owns the
application facade and Meal Pattern Recommender. Successful generation delegates
one append-only revision write to the existing PR7 `MealPlanService`; failure is
returned before any write. No Planner table, migration, service process, AI,
Retail or optimizer was introduced.

- Planner configuration: `planner-v0.1`.
- compatibility mapping: `meal-role-recipe-v1`.
- recommender: `meal-pattern-recommender-v1`.

`MealRole` remains distinct from `RecipeVersion.meal_type_code`. The compatibility
table is explicit and versioned in Planner code. It maps breakfast primarily to
`breakfast`/`sandwich`, lunch to `main`/`salad`/`sandwich`, dinner to
`main`/`salad`/`side`, snacks and workout opportunities to bounded compatible
catalogue classifications, and `OTHER` to all existing classifications. It does
not rewrite Recipe truth.

## Generation and trace

The request pins the Household, Monday, accepted member schedule snapshots,
reference-energy values, immutable recipe candidates, per-member exclusions and
preferences, read-only Pantry ingredient identities, optional user-fixed events,
and the prior plan identity for replan evidence. These generation-time values do
not create a persisted preference schema.

Members' seven-day opportunities are reconciled by local date, role and repeated
role occurrence. Compatible opportunities share one event and candidate only
after the union of participant hard exclusions passes. The deterministic
candidate order is immutable RecipeVersion UUID. Hard rejection codes are:

- `NOT_VERIFIED`;
- `ROLE_INCOMPATIBLE`;
- `MEMBER_EXCLUDED_INGREDIENT`;
- `NUTRITION_UNAVAILABLE`;
- `MAX_REPETITIONS`.

Eligible candidates receive these configured score components: preference
`+20` per participating member, Pantry overlap `+4` per ingredient, batch
compatibility `+2`, known time `-0.01` per minute, and repetition `-7` per prior
use. Highest score wins; exact ties use ascending RecipeVersion UUID. Cost is not
scored because authoritative cost truth is unavailable. Pantry is only a scoring
signal and is never reserved or consumed.

After the semantic week is selected, each member receives one Decimal multiplier:
`7 × daily reference energy / sum(selected base-serving kcal)`. That same
member-wide multiplier is applied to all of the member's recipe-backed events,
with six-decimal half-up quantization. Missing/non-positive reference energy or
recipe kcal produces a bounded failure; unknown non-recipe nutrition is never
credited. This is the Issue #57 preferred weekly-normalization baseline and does
not invent meal-role calorie percentages or therapeutic adjustments.

The trace contains both version strings, a SHA-256 canonical request fingerprint,
every candidate rejection/score/selection, explicit warnings, selected immutable
RecipeVersion IDs, and a SHA-256 trace fingerprint. Identical input and config
produce identical events and fingerprints. Duration is deliberately not part of
the deterministic trace.

## Fixed events, replan and bounded failure

Planner autonomously selects only `COOK_RECIPE`. A user-fixed non-recipe event
must identify an existing semantic opportunity and exact participants; Planner
preserves its source kind/reference/explicit portions and never manufactures a
RecipeVersion or supply. A generated plan, including a replan request with a
previous plan pin, uses the existing append-only revision operation. The old
revision is not mutated.

Invalid input or an infeasible opportunity returns a typed failure and trace.
Because selection and Serving reconciliation finish in memory before delegation
to `MealPlanService`, infeasible generation cannot persist a partial MealPlan.

## Repository-backed fixture evidence and limitations

The PR8 fixture test loads the checked-in catalogue through the real SQLite
migration/seed/repository and Nutrition service path. It verifies 30 current
verified recipes and at least 80 FoodIngredients, then exercises three materially
different one-, two- and three-member schedule shapes. At this repository state,
all 30 catalogue RecipeVersions correctly yield `INCOMPLETE` Nutrition with
unknown kcal. All three fixture outcomes are therefore explicit
`NO_ELIGIBLE_CANDIDATE` failures with reproducible traces—not partial plans and
not invented kcal. Unit fixtures separately prove successful heterogeneous
complete-week generation, shared events, individualized allocation, exclusions
and repeatability.

This evidence does not declare Gate 1 complete. A future bounded authoritative
nutrition/data correction must make an adequate recipe pool eligible before the
repository-backed households can demonstrate successful complete plans. That is
a data-readiness limitation, not a reason for Planner persistence or a schema
migration.
