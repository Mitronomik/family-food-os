# Handoff

Updated: `2026-09-19`.

## Accepted base and governance

DATA-CORPUS-V1 / DC0 is COMPLETE through merged PR #68.

Accepted post-PR68 main:

`b1ce3e02394bad847f0c4063fe9faf520e208622`

Current bounded operation:

`DATA-CORPUS-V1 / DC1 — Source authority + coverage inventory` — ACTIVE under
Issue #67.

Accepted SQLite migration head:

`0032_meal_plan_serving`

Future RecipeTemplate reservation remains:

`0033_recipe_template_catalogue`

Gate1-CLOSE is NOT STARTED.

PR9 is NOT STARTED.

## Closed superseded work

PR #66 — `feat: publish minimal Russian corpus for Gate1 planning` — was closed
without merge on 2026-09-19.

Closing it accepted none of its proposed production data. Its branch remains
historical implementation evidence only; reusable mechanics may be recovered
selectively later if they conform to DATA-CORPUS-V1.

## DC1 task

Build the coverage/authority inventory required by Issue #67.

Required outputs:

1. initial `50–80+` useful recipe candidates;
2. exact selected source variants/branches;
3. deduplicated required FoodIngredient/form demand;
4. explicit reuse of existing accepted FoodIngredient/profile truth;
5. authoritative source/status for each missing demanded form;
6. rights/use status;
7. exact unresolved blocker inventory;
8. proposed small DC2 food-publication batches;
9. proposed small DC3 recipe-publication batches.

Canonical rules for source hierarchy, authority, food/form semantics, rights,
publication and verification are owned by:

- `docs/family-food/data-corpus-v1.md`;
- `docs/family-food/master-roadmap-addendum-2026-09-19-data-corpus.md`;
- Issue #67.

Do not restate or alter those rules in this handoff.

## Scope boundary

DC1 is evidence/curation only.

No broad production FoodIngredient/Nutrition/Composition/RecipeVersion
publication or schema/migration change belongs in DC1.

DC2/DC3 production work starts only as separately reviewable batches after the
DC1 package identifies exact demand and authority.

## Verification expectation

DC1 must produce a reviewable, reproducible evidence package with explicit
coverage and unresolved inventory. Follow the canonical DATA-CORPUS-V1 contract
and `docs/family-food/verification-policy.md` for exact verification rules.

## Stop condition

After DC1 is review-ready/merged, stop.

Do not automatically start DC2, DC3, DC4, Gate1-CLOSE or PR9.
