# Current focus

Updated: 2026-10-02.

## Accepted state

PR #125 is merged into `main` at:

`5bf5127a238b8bb139903f008ad7c14b9b1309c7`.

It authorizes Issue #124 / R1-C after merged R1-H production truth established:

- 1 active exact-energy BREAKFAST RecipeVersion;
- 3 active exact-energy MAIN RecipeVersions;
- real seven-DINNER capacity under unchanged `max_recipe_repetitions=3`;
- ordinary authoritative Planner loading and FoodIngredient exclusions;
- migration head `0042_recipe_prepared_output_nutrition`.

## Current bounded operation

**R1-C — Production persisted Planner proof.**

Issue: `#124`.

PR: `#126`.

Branch: `feat/r1c-production-planner-proof`.

Implementation base:

`5bf5127a238b8bb139903f008ad7c14b9b1309c7`.

Production runtime/data base remains:

`e50da0d21a6c740e5d60c257ac64de12e0c5d2b3` (merged PR #123).

Proof freeze:

`a36d8c2876daea4b4f3edd7f47af8b49d09b04cd`.

## R1-C result

R1-C is implemented as a production integration proof. No application runtime,
schema, migration or authoritative production-data behavior is changed.

The proof uses real persisted boundaries:

`Household / HouseholdMember`
→ accepted CUSTOM MealPattern selection with explicit v0.4 energy shares
→ `PlannerService.generate_authoritative(...)`
→ ordinary active RecipeVersion catalogue
→ current neutral Recipe Nutrition
→ existing MealPlan / Serving UoW.

Verified product behavior:

- `planner-v0.4`;
- `meal-role-recipe-v2`;
- active exact-energy pool is exactly 1 BREAKFAST + 3 MAIN;
- a seven-DINNER repository-backed week is generated and persisted;
- all three MAIN RecipeVersions are used, none more than 3 times;
- persisted Serving portions are positive and are driven by the accepted
  opportunity energy share;
- repeated generation produces the same semantic week and identical Planner trace
  fingerprint while appending MealPlan revision history;
- a materially different BREAKFAST+DINNER pattern fails explicitly because one
  BREAKFAST RecipeVersion cannot cover seven breakfasts under repetition=3;
- that infeasible result persists no partial MealPlan;
- hard exclusion of `WHEAT_BREAD_HIGH_GRADE_STALE` rejects the meatball
  candidate through the ordinary authoritative boundary, leaves unrelated MAIN
  candidates unmarked by that exclusion, and persists no partial plan;
- `AI_ENABLED=false`;
- migration head remains 0042; no migration 0043.

Durable receipt:

`data/curation/r1c-production-planner-proof/summary.json`.

## Verification

Exact proof-head verification at `a36d8c2...`:

- R1-C focused/affected suite — **101 passed**;
- Ruff check — SUCCESS;
- Ruff format --check — SUCCESS;
- scope/whitespace gate — SUCCESS;
- Docs verification — SUCCESS;
- Russian nutrition methodologies — SUCCESS.

The two earlier red R1-C attempts were task-local test-fixture/hygiene defects:

- unsupported `moderate` activity caused the deterministic Nutrition target to
  fail closed with `MISSING_REFERENCE_ENERGY`; the persisted member fixture now
  uses the already-supported `active` PAL category;
- Ruff/import/format findings were corrected without changing acceptance.

Status:

`READY_FOR_FINAL_REVIEW`.

## Scope boundaries

Do not:

- change Planner algorithm/scoring/roles/repetition;
- add migration 0043 or schema changes;
- publish additional FoodIngredient/RecipeVersion/Nutrition authority;
- weaken exclusions;
- infer raw→cooked Nutrition, yield or retention;
- start R2/R3;
- start DC4 / Gate1-CLOSE;
- start PR9 Shopping;
- start Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI.

## Next step

Independent final review of PR #126.

After explicit review and merge, reassess and separately authorize the next R2/R3
corpus-expansion operation toward the DATA-CORPUS-V1 baseline.

Do not start R2/R3, DC4, Gate1-CLOSE or PR9 automatically.
