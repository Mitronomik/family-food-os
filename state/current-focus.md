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

`2f643303308f3bb6b95d7161435474109ad91a34`.

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
- a persisted two-member scenario proves the same exclusion remains member-local:
  six unaffected dinner events stay shared, the unaffected member can still
  receive the meatball candidate, and the excluded member never receives it;
- `AI_ENABLED=false`;
- migration head remains 0042; no migration 0043.

Durable receipt:

`data/curation/r1c-production-planner-proof/summary.json`.

## Verification

Exact corrected proof-head verification at `2f643303...`:

- R1-C focused/affected suite — **102 passed**;
- Ruff check — SUCCESS;
- Ruff format --check — SUCCESS;
- scope/whitespace gate — SUCCESS.

The independent final review found one acceptance-evidence gap: the original
hard-exclusion proof used only one HouseholdMember and therefore did not prove
preservation of other members/sharedness. The corrected proof adds the persisted
two-member scenario above and closes that gap without changing runtime behavior,
Planner rules, schema or authority.

Earlier task-local fixture/hygiene failures remain historical evidence only:

- unsupported `moderate` activity correctly failed closed at
  `MISSING_REFERENCE_ENERGY`; the persisted fixture uses supported `active`;
- Ruff/import/format findings were corrected without changing acceptance;
- the first multi-member trace assertion was corrected to use stable
  `applied_exclusions` plus persisted event participation rather than treating
  partial compatibility as a whole-candidate rejection.

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
