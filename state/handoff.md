# Handoff

Updated: `2026-09-19`.

## Accepted base and governance

PR #63 is MERGED.

Accepted post-PR63 main:

`7408d161575870149f0d1938e1f126bb41561537`

Current bounded operation:

`GATE1-A-RU — Russian normative corpus acceptance and minimal Gate1 delivery` — ACTIVE under Issue #64.

Gate1-A / Issue #61 remains ACTIVE.

Gate1-CLOSE is NOT STARTED.

PR9 is NOT STARTED.

Accepted SQLite migration head:

`0032_meal_plan_serving`

Future RecipeTemplate reservation remains:

`0033_recipe_template_catalogue`

## Accepted PR63 evidence baseline

PR #63 is accepted audit/blocker evidence only.

It established:

- 30 current verified RecipeVersions;
- 29 `INCOMPLETE`;
- 1 `CONDITIONAL`;
- one current Planner-eligible oatmeal candidate with positive kcal;
- generic/current-largest fixture minimum:
  7 eligible versions;
- generic repair gap:
  6 versions;
- current repository fixture capacities:
  3 / 6 / 7;
- no current fixed-event or hard-exclusion fixture;
- target selection:
  `TARGET_SELECTION_BLOCKED_PENDING_PRIMARY_EVIDENCE_REVIEW`;
- final blocker classes:
  70 `NEW_PRIMARY_EVIDENCE_REQUIRED`;
  16 `IMMUTABLE_RECIPE_REVISION_REQUIRED`;
  7 `ALREADY_ACCEPTED_EVIDENCE_REBIND`;
  1 `PROFILE_OR_FORM_DATA_REPAIR`.

PR #63 changed no production truth, schema, migration or Planner behavior.

## GATE1-A-RU purpose

The user has superseded the previous six-FNS evidence-repair direction.

Repository inspection proves that Russian normative data work already exists:

- committed 214-card `RU_MR_2_4_0162_19` source corpus;
- v22.13 preflight/mapping over the 350-recipe USSR82 checkpoint;
- identity mapping for all 363 external ingredient identities;
- candidate/profile curation packages.

The production Recipe Catalogue still contains no `USSR82-*` RecipeVersions. The missing step is a bounded publication/integration, not another broad research pass.

Selected Gate1 subset:

Breakfast:
- `USSR82-467` — Омлет (натуральный)
- `USSR82-492` — Сырники из творога
- `USSR82-1081` — Блины

Main:
- `USSR82-208` — Рассольник ленинградский
- `USSR82-263` — Суп молочный с картофельными клецками
- `USSR82-364` — Шницель из капусты
- `USSR82-697` — selected chicken main-product variant without garnish/sauce
- `USSR82-720` — Котлеты по-киевски, main product without garnish

First bounded breakfast fallback:
- `USSR82-453` — Яйца вареные.

This 3-breakfast + 5-main set provides capacity 9 / 15 under max repetitions=3 and avoids the artificial sandwich dependency.

## GATE1-A-RU invariants

- reuse existing v22.13 mapping/curation before doing any new mapping;
- current v22.5 upload is older source evidence and must not overwrite later mapping decisions;
- production publication is limited to the selected Gate1 subset;
- primary publisher/original recipe source first;
- official exact food-composition/portion evidence second;
- accepted repository evidence may be reused only when exact form/profile/measure semantics match;
- no search-snippet authority;
- no retailer measurement authority by default;
- no LLM numeric facts;
- no estimate promotion;
- no inferred yield/retention;
- no arbitrary alternative selection;
- production FoodIngredient/Nutrition/RecipeVersion changes are permitted only where required by the selected subset and backed by accepted authority;
- no schema/migration;
- no `0033` consumption;
- no Planner changes;
- no Gate1-CLOSE;
- no PR9.

## Required GATE1-A-RU outcome

Publish the smallest authoritative Russian subset needed to make Gate1 executable.

Required outcome:
- selected/fallback Russian RecipeVersions have non-INCOMPLETE Nutrition and positive kcal;
- repository-backed Planner persists a complete seven-day week for at least one real fixture household;
- individualized positive Decimal Servings are persisted;
- exclusions and deterministic trace remain correct;
- current incomplete FNS recipes remain explicitly incomplete.

## Stop condition

After the GATE1-A-RU production data PR is review-ready/merged, stop for separate Gate1-CLOSE review.

Do not start PR9 automatically.
