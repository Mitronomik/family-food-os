# Current focus

Updated: 2026-10-02.

## Accepted state

PR #123 / R1-H School2022 MAIN prepared-output runtime batch is merged into
`main` at:

`e50da0d21a6c740e5d60c257ac64de12e0c5d2b3`.

R1-H delivered the frozen R1-G batch without changing Planner rules or schema:

- `HARD_BOILED_EGG` remains the active exact-energy breakfast candidate;
- `BOILED_CHICKEN_MAIN_PRODUCT` remains an active exact-energy MAIN candidate;
- `SCHOOL2022_54_29M_BEEF_MEATBALLS` is active at exact 153 kcal / 80 g;
- `SCHOOL2022_54_2M_BEEF_GOULASH` is active at exact 185.6 kcal / 80 g;
- the four new supporting FoodIngredients are identity-only and carry no invented
  Nutrition/Composition authority;
- prepared Nutrition continues to use only
  `PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`;
- migration head remains `0042_recipe_prepared_output_nutrition`.

The ordinary authoritative Planner boundary proves that the three active MAIN
RecipeVersions can cover seven DINNER opportunities with the unchanged
`max_recipe_repetitions=3`.

## R1-C readiness decision

The prerequisite in
`docs/family-food/r1c-production-planner-proof-prerequisite.md` is now satisfied.

That contract previously blocked R1-C because the active exact-energy R1
candidate count was zero. Merged R1-F and R1-H runtime truth supersedes that
historical blocker:

- active exact-energy breakfast candidates: 1;
- active exact-energy MAIN candidates: 3;
- seven-opportunity MAIN/DINNER capacity: proven through the real Planner path;
- hard FoodIngredient exclusion behavior: proven;
- Planner algorithm/scoring/repetition: unchanged.

This closes the **minimum production-capacity prerequisite**. It does not itself
complete R1-C, DC4 or Gate1-CLOSE.

## Current bounded operation

**R1-C — Production persisted Planner proof.**

Issue:

`#124`.

Accepted base:

`e50da0d21a6c740e5d60c257ac64de12e0c5d2b3`.

Status:

`AUTHORIZED_NOT_STARTED`.

Goal:

Prove that the production Planner can generate and persist a real
repository-backed seven-day household week through the ordinary
Household / MealPattern / RecipeVersion / Nutrition / MealPlan / Serving
boundaries.

The success path must use real active production RecipeVersions and current
deterministic Nutrition authority. Synthetic Planner candidates are not an
accepted substitute.

## Required R1-C proof

At minimum:

- ordinary `PlannerService.compose_authoritative_request(...)`;
- `planner-v0.4`;
- `meal-role-recipe-v2`;
- real repository-backed household/member meal-pattern state;
- one complete seven-day generated **and persisted** week;
- individualized persisted Servings;
- deterministic semantic replay / trace fingerprint;
- one explicit bounded infeasible case with no partial persisted plan;
- hard FoodIngredient exclusion through the ordinary authoritative path;
- `AI_ENABLED=false`.

The newly feasible seven-DINNER MAIN-heavy pattern is the default success fixture
unless implementation discovers a contract-backed reason to use another already
authorized repository-backed pattern.

## Scope boundaries

Do not:

- change Planner algorithm/scoring/roles/repetition;
- add migration 0043 or any schema change;
- add another Nutrition authority kind/calculation version;
- publish additional FoodIngredient/RecipeVersion/Nutrition truth;
- infer raw→cooked Nutrition, yield or retention;
- weaken exclusions to obtain a successful week;
- start DC4 / Gate1-CLOSE;
- start PR9 Shopping;
- start Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI;
- start R2/R3.

If the R1-C implementation discovers a need for a new persisted contract,
migration or authority decision, stop and reopen the applicable Implementation
Contract Gate instead of expanding scope.

## Verification baseline

R1-H final review evidence on merged runtime/test bytes:

- focused/affected R1-H suite — 135 passed;
- Ruff check / format — SUCCESS;
- Russian nutrition methodologies — SUCCESS;
- Docs / DC1 — SUCCESS;
- Nutrient registry V2 — focused + four backend shards + launcher SUCCESS;
- Partial nutrition profiles — focused + four backend shards + launcher SUCCESS.

R1-C receives its own affected verification; this historical receipt is not a
substitute for new R1-C tests.

## Next step

Implement Issue #124 as one bounded R1-C PR.

After independent review and merge, reassess DC4 / Gate1-CLOSE readiness.
Do not start Gate1-CLOSE or PR9 automatically.
