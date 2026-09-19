# Handoff

Updated: `2026-09-19`.

## Accepted base and governance

PR #63 is MERGED.

Accepted post-PR63 main:

`7408d161575870149f0d1938e1f126bb41561537`

Current bounded operation:

`GATE1-A-E1 — Primary-source authority review for minimum candidate set` — ACTIVE under Issue #64.

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

## GATE1-A-E1 purpose

E1 is the evidence step required before production repair.

Primary candidate set:

- `FNS2_ORANGE_PORK_CHOPS`
- `FNS4_OVEN_FRIED_FISH`
- `FNS5_BAKED_LENTILS_CASSEROLE`
- `SNAP4_DILLED_FISH_FILLETS`
- `TNC6_EGGS_SPINACH`
- `WIC1_BEYOND_BASIC_GRILLED_CHEESE`

Issue #64 owns the exact row-level blockers, source hierarchy, terminal dispositions, acceptance criteria and evidence-package requirements.

The evidence review must determine whether the generic six-repair set is actually supportable by exact authority under the current model.

## Bounded fallback

Fallback is conditional, not an automatic extension of scope.

Allowed fallback candidates:

- `SNAP4_SPANISH_FRITTATA` — breakfast;
- `SNAP4_BRAISED_CHICKEN_SPINACH` — main.

A fallback candidate may be researched only after a primary candidate receives a terminal `BLOCKED` outcome and only if it is needed to restore a feasible minimum Planner set.

No other recipe search is authorized.

## E1 invariants

- research/evidence only;
- primary publisher/original recipe source first;
- official exact food-composition/portion evidence second;
- accepted repository evidence may be reused only when exact form/profile/measure semantics match;
- no search-snippet authority;
- no retailer measurement authority by default;
- no LLM numeric facts;
- no estimate promotion;
- no inferred yield/retention;
- no arbitrary alternative selection;
- no production FoodIngredient/Nutrition/evidence/assessment/RecipeVersion changes;
- no schema/migration;
- no `0033` consumption;
- no Planner changes;
- no Gate1-CLOSE;
- no PR9.

## Required E1 outcome

For every primary blocker, produce a terminal evidence disposition.

For every primary candidate, derive:

- `EVIDENCE_READY_FOR_DATA_REPAIR`;
- `EVIDENCE_READY_REQUIRES_IMMUTABLE_RECIPE_REVISION`;
- or `BLOCKED`.

Then determine whether an evidence-ready minimum Planner candidate set exists.

If primary evidence is insufficient, activate only the minimum permitted fallback review.

## Stop condition

After E1 is review-ready/merged, stop.

Do not implement the resulting production repair plan automatically.

The next production data-repair operation requires separate bounded authorization.
