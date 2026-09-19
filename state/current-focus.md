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

## Current authorized operation

`DATA-CORPUS-V1 / DC1 — Source authority + coverage inventory` is **ACTIVE**
under Issue #67.

DC1 is evidence/curation work.

Required outcome:

- select an initial `50–80+` useful recipe candidate set;
- preserve exact source card/variant/branch identity;
- build the deduplicated required FoodIngredient/form demand;
- reuse existing accepted mappings and production profiles first;
- assign authoritative source/status and rights/use status for demanded food/forms;
- classify exact unresolved mass/form/process/nutrition blockers;
- produce proposed small DC2 food-publication batches;
- produce proposed small DC3 recipe-publication batches.

Follow the canonical rules in:

- `docs/family-food/data-corpus-v1.md`;
- `docs/family-food/master-roadmap-addendum-2026-09-19-data-corpus.md`;
- Issue #67.

Those sources own source hierarchy, authority, rights, publication and
verification policy. Do not duplicate or redefine those rules in state files.

## Scope boundary

DC1 does not publish broad production FoodIngredient/Nutrition/Composition/
RecipeVersion truth and does not authorize schema/migration changes.

Any later production publication must occur through separately reviewable
DC2/DC3 batches under the canonical DATA-CORPUS-V1 contract.

## Relationship to PR #66

PR #66 was closed without merge on 2026-09-19 and is historical implementation
evidence only.

Its proposed production nutrition/profile/recipe truth is not accepted.
Reusable mechanics may be recovered selectively later if they conform to
DATA-CORPUS-V1.

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

Do not automatically start DC2, DC3, DC4, Gate1-CLOSE, PR9, Retail, AI,
Auth/PostgreSQL or the generalized Data Ingestion Platform.
