# Current focus

Updated: `2026-09-19`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` = COMPLETE through merged PR #51.
- PR7 / Issue #53 = COMPLETE through merged PR #54.
- PR8 / Issue #57 = COMPLETE through merged PR #59.
- Post-PR59 state synchronization = COMPLETE through merged PR #60.
- Gate1-A audit/evidence baseline = COMPLETE through merged PR #63.
- Accepted post-PR63 main / GATE1-A-E1 base:
  `7408d161575870149f0d1938e1f126bb41561537`.
- Accepted SQLite migration head: `0032_meal_plan_serving`.
- Future RecipeTemplate reservation remains `0033_recipe_template_catalogue`.

## Current authorized operation

`GATE1-A-E1 — Primary-source authority review for minimum candidate set` is **ACTIVE** under Issue #64.

Goal: determine whether the six-recipe generic minimum repair set identified by PR #63 can be made authoritative using exact primary evidence and the existing FamilyFoodOS data model.

Issue #64 is the bounded execution contract.

This operation is **research/evidence only**. It does not publish production FoodIngredient, Nutrition, measure-evidence, assessment or RecipeVersion truth.

## Accepted Gate1-A audit baseline

Merged PR #63 established:

- 30 current verified RecipeVersions;
- 29 `INCOMPLETE`;
- 1 `CONDITIONAL`;
- only current Planner-eligible candidate:
  `WIC1_OVERNIGHT_OATS_CINNAMON_APPLE:v2`;
- generic/current-largest fixture capacity:
  7 eligible versions = 2 breakfast + 4 main + 1 sandwich;
- generic repair gap:
  6 versions;
- current target-selection status:
  `TARGET_SELECTION_BLOCKED_PENDING_PRIMARY_EVIDENCE_REVIEW`;
- current repository fixture capacities:
  3 / 6 / 7;
- current repository fixture has no fixed event and no explicit hard exclusion;
- blocker classification:
  70 new-primary-evidence / 16 immutable-revision / 7 accepted exact rebind / 1 profile-or-form repair.

PR #63 changed no production truth, schema, migration or Planner behavior.

## GATE1-A-E1 primary scope

Primary candidates:

1. `FNS2_ORANGE_PORK_CHOPS`
2. `FNS4_OVEN_FRIED_FISH`
3. `FNS5_BAKED_LENTILS_CASSEROLE`
4. `SNAP4_DILLED_FISH_FILLETS`
5. `TNC6_EGGS_SPINACH`
6. `WIC1_BEYOND_BASIC_GRILLED_CHEESE`

For each blocking row, E1 must produce a terminal evidence decision and a candidate-level outcome.

Allowed fallback review is limited to:

- `SNAP4_SPANISH_FRITTATA`;
- `SNAP4_BRAISED_CHICKEN_SPINACH`.

Fallback may start only when a primary candidate is explicitly evidence-blocked and only to the minimum extent required to recover a feasible Planner set.

## Architecture / authority boundary

- deterministic core remains `AI_ENABLED=false`;
- exact mass/form/profile/nutrition authority must come from accepted repository truth or exact primary evidence;
- search snippets, LLM-generated numbers and convenience estimates are not authority;
- unknown != zero;
- do not promote `REVIEW_REQUIRED_ESTIMATE` to exact;
- no arbitrary cheese, vegetable, cultivar, form, raw/cooked or size substitution;
- no production data repair in E1;
- no new RecipeVersion publication in E1;
- no schema/migration change;
- migration `0033_recipe_template_catalogue` remains untouched;
- no Planner/MealRole compatibility changes;
- no Shopping / Prep / Retail / AI / Auth/PostgreSQL / frontend scope.

## Active sequence

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         COMPLETE (#47 / PR #51)
→ PR7 MealPlan / Serving                     COMPLETE (#53 / PR #54)
→ PR8 Planner v0                             COMPLETE (#57 / PR #59)
→ GATE1-A audit/readiness baseline           COMPLETE (PR #63)
→ GATE1-A-E1 primary-source evidence         ACTIVE (#64)
→ GATE1-A production data repair             NOT STARTED
→ GATE1-CLOSE — Planning Core                NOT STARTED
→ PR9 Shopping Engine                        NOT STARTED
```

## Stop condition

After GATE1-A-E1 is review-ready and merged, stop.

Do not implement production repairs automatically.

A separate bounded production data-repair operation must be authorized from the accepted E1 evidence package.
