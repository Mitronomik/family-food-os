# Current focus

Updated: `2026-09-19`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` = COMPLETE through merged PR #51.
- PR7 / Issue #53 = COMPLETE through merged PR #54.
- PR8 / Issue #57 = COMPLETE through merged PR #59.
- Post-PR59 state synchronization = COMPLETE through merged PR #60.
- Gate1-A audit/evidence baseline = COMPLETE through merged PR #63.
- Accepted post-PR65 main / GATE1-A-RU base:
  `9a76a97790b676f36c4c982af825721c3ef2c67e`.
- Accepted SQLite migration head: `0032_meal_plan_serving`.
- Future RecipeTemplate reservation remains `0033_recipe_template_catalogue`.

## Current authorized operation

`GATE1-A-RU — Russian normative corpus acceptance and minimal Gate1 delivery` is **ACTIVE** under Issue #64.

Goal: reuse the already supplied/mapped Russian normative corpus, publish only the smallest clean Russian recipe/data subset needed for Gate1, and prove a complete repository-backed week with individualized Servings.

Issue #64 is the bounded execution contract.

This operation is a **bounded production Gate1 data slice**. Production publication is permitted only for the selected Russian subset and only with authoritative identity/profile/provenance. No broad 350-recipe import is authorized.

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

## GATE1-A-RU primary scope

Selected Russian Gate1 subset:

Breakfast:
1. `USSR82-467` — Омлет (натуральный)
2. `USSR82-492` — Сырники из творога
3. `USSR82-1081` — Блины

Main:
4. `USSR82-208` — Рассольник ленинградский
5. `USSR82-263` — Суп молочный с картофельными клецками
6. `USSR82-462` — Яичница глазунья с жареным картофелем
7. `USSR82-697` — selected chicken main-product variant without garnish/sauce
8. `USSR82-720` — Котлеты по-киевски, main product without garnish

First bounded breakfast fallback if exact authority blocks one selected breakfast:
- `USSR82-453` — Яйца вареные.

Reuse the existing v22.13 mapping/curation work. The currently uploaded v22.5 checkpoint is an older source-data artifact and must not be imported wholesale over v22.13 decisions.

## Architecture / authority boundary

- deterministic core remains `AI_ENABLED=false`;
- exact mass/form/profile/nutrition authority must come from accepted repository truth or exact primary evidence;
- search snippets, LLM-generated numbers and convenience estimates are not authority;
- unknown != zero;
- do not promote `REVIEW_REQUIRED_ESTIMATE` to exact;
- no arbitrary cheese, vegetable, cultivar, form, raw/cooked or size substitution;
- production FoodIngredient/profile/RecipeVersion changes are allowed only for the selected Gate1 subset;
- no broad catalogue publication or ingestion-platform work;
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
→ GATE1-A-RU minimal Russian corpus          ACTIVE (#64)
→ GATE1-CLOSE — Planning Core                NOT STARTED
→ PR9 Shopping Engine                        NOT STARTED
```

## Stop condition

After the GATE1-A-RU production data PR is review-ready/merged, stop for separate Gate1-CLOSE review.

Do not start PR9 automatically.
