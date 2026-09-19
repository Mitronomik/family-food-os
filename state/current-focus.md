# Current focus

Updated: `2026-09-19`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` = COMPLETE through merged PR #51.
- PR7 / Issue #53 = COMPLETE through merged PR #54.
- PR8 / Issue #57 = COMPLETE through merged PR #59.
- Post-PR59 state synchronization = COMPLETE through merged PR #60.
- Gate1-A audit/evidence baseline = COMPLETE through merged PR #63.
- DATA-CORPUS-V1 / DC0 = COMPLETE through merged PR #68.
- Accepted post-PR68 main:
  `b1ce3e02394bad847f0c4063fe9faf520e208622`.
- PR #66 = CLOSED / NOT MERGED / SUPERSEDED by DATA-CORPUS-V1.
- Accepted SQLite migration head: `0032_meal_plan_serving`.
- Future RecipeTemplate reservation remains `0033_recipe_template_catalogue`.

## Canonical data strategy

FamilyFoodOS builds a reusable authoritative food + recipe corpus needed by the
service itself, then uses verified subsets of that ordinary production corpus for
Gate1 and later gates.

Canonical contracts:

- `docs/family-food/data-corpus-v1.md`;
- `docs/family-food/master-roadmap-addendum-2026-09-19-data-corpus.md`;
- Issue #67.

The former Gate1-only minimal-eight publication strategy in Issue #64 / PR #66
is historical and no longer active.

## Current authorized operation

`DATA-CORPUS-V1 / DC1 — Source authority + coverage inventory` is **ACTIVE**
under Issue #67.

DC1 is evidence/curation work.

Required outcome:

- select an initial `50–80+` useful recipe candidate set;
- preserve exact source card/variant/branch identity;
- build the deduplicated required FoodIngredient/form demand;
- reuse existing accepted mappings and production profiles first;
- assign an authoritative source candidate/status for every demanded food/form;
- record rights/use status;
- classify exact mass/form/process/nutrition blockers;
- produce proposed small DC2 food-publication batches;
- produce proposed small DC3 recipe-publication batches.

DC1 must not invent missing values or silently resolve ambiguity.

## DC1 authority boundaries

- deterministic core remains `AI_ENABLED=false`;
- FoodIngredient remains the sole canonical food identity;
- exact raw/input/cooked forms are not interchangeable;
- unknown != zero;
- estimate != exact;
- no arbitrary cross-source nutrient synthesis;
- no arbitrary source alternative selection;
- source-declared recipe nutrition remains reference/cross-check evidence unless a
  canonical contract explicitly grants authority;
- FIC/FGBUN material is a preferred Russian exact-authority candidate where
  identity/basis/version and retained-use scope are reviewable;
- FIC 2024 / the official database is not treated as automatically licensed for
  bulk copying;
- USDA FoodData Central is an accepted open official baseline candidate where
  exact semantics match;
- manufacturer labels establish exact product truth, not generic category truth
  by default;
- retailer pages, mirrors, snippets and secondary tables are corroboration/
  discovery by default;
- no LLM numeric authority.

## Production boundary

DC1 does **not** authorize broad production publication.

No production FoodIngredient/Nutrition/NutrientVector/Composition/RecipeVersion
change is made merely because DC1 identifies a usable candidate.

Production publication starts only through separately reviewable DC2/DC3 batches
under the DATA-CORPUS-V1 contract.

No schema/migration change is expected in DC1.

If evidence reveals a genuine schema limitation, stop before consuming a new
migration number.

## Relationship to PR #66

PR #66 was closed without merge on 2026-09-19.

Its branch remains historical implementation evidence only.

Reusable mechanics may be recovered selectively later, including:

- immutable selected-source snapshot/hash validation;
- deterministic publication/idempotency structure;
- Planner fixture structure;
- persisted-week/Serving proof.

Its ten proposed profiles and selected Gate1-specific production truth are not
accepted production data.

## Active sequence

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         COMPLETE
→ PR7 MealPlan / Serving                     COMPLETE
→ PR8 Planner v0                             COMPLETE
→ Gate1-A audit/readiness baseline           COMPLETE
→ DATA-CORPUS-V1 / DC0                       COMPLETE (PR #68)
→ DC1 source authority + coverage inventory  ACTIVE (#67)
→ DC2 food publication batches               NOT STARTED
→ DC3 recipe publication batches             NOT STARTED
→ DC4 readiness audit + Gate1 consumption    NOT STARTED
→ GATE1-CLOSE — Planning Core                NOT STARTED
→ PR9 Shopping Engine                        NOT STARTED
```

## Stop condition

DC1 ends with a reviewable evidence/curation package and exact proposed DC2/DC3
batch plan.

Do not automatically start DC2 production publication, DC3 recipe publication,
Gate1-CLOSE, PR9, Retail, AI, Auth/PostgreSQL or the generalized Data Ingestion
Platform.
