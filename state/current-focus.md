# Current focus

Updated: `2026-09-20`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` = COMPLETE through merged PR #51.
- PR7 / Issue #53 = COMPLETE through merged PR #54.
- PR8 / Issue #57 = COMPLETE through merged PR #59.
- Gate1-A audit/evidence baseline = COMPLETE through merged PR #63.
- DATA-CORPUS-V1 / DC0 = COMPLETE through merged PR #68.
- Post-DC0 state activation = COMPLETE through merged PR #69.
- Accepted current main:
  `d8c76a64483e3d5814e702be33c12cbe2e144160`.
- PR #66 = CLOSED / NOT MERGED / SUPERSEDED by DATA-CORPUS-V1.
- Accepted SQLite migration head: `0032_meal_plan_serving`.
- Future RecipeTemplate reservation remains `0033_recipe_template_catalogue`.

## Current authorized operation

`DATA-CORPUS-V1 / DC1 — Source authority + coverage inventory` remains **ACTIVE**
under Issue #67.

The recovered DC1 delivery is **REVIEW-READY**, not merged and not COMPLETE.

Delivery branch:

`data/data-corpus-v1-dc1`

## Recovered DC1 package

Canonical evidence package:

`data/curation/data-corpus-v1-dc1/`

Pre-rebuild recovery checkpoint:

`data/curation/data-corpus-v1-dc1/recovery/pre-rebuild-b7bc19e8881ddc90/`

Reproducible tooling:

- `scripts/build_data_corpus_v1_dc1.py`;
- `scripts/validate_data_corpus_v1_dc1.py`.

Recovered reconciliation:

- 68 candidate recipe families;
- 991 retained source relationship/calculation rows;
- 96 external ingredient identities;
- 33 accepted existing/alias identity mappings;
- 63 identities requiring later DC2-level closure if pursued;
- full accepted PR39 inputs required: 350 recipe rows / 363 ingredient identities;
- 31 one-source-Variant / 37 multiple-source-Variant families structurally;
- 5 `SIMPLE_SOURCE_BRANCH_CANDIDATE`;
- 63 `REVIEW_REQUIRED`;
- 33 existing mappings have identified current USDA FDC profile provenance but
  remain `PROFILE_PRESENT_FORM_REVIEW_REQUIRED`;
- 28 non-existing identities have an official source-family candidate with the
  exact record still unpinned;
- 35 identities are blocked on identity/form semantics before exact authority
  can be assigned.

A single source `Variant` is not treated as an exact publication decision.
Relationship compatibility and semantic-label debt also force review.

## Open DC1 blockers retained

- exact v22.13 row-nutrient shards were not available to recovery;
- 20 candidate families have additional v22.13 non-calculation relationship rows;
- 20 used external identities have v22.5/v22.13 label differences requiring review;
- all 33 existing profiles still require exact recipe-form suitability review;
- candidate source-family assignment is not exact-record authority closure;
- the original 68-family funnel has assortment gaps for a realistic family week.

These are recorded blockers, not permission to invent or auto-expand data.

Follow canonical authority, rights and publication rules in
`docs/family-food/data-corpus-v1.md` and Issue #67.

## Scope boundary

DC1 is evidence/curation only.

No production FoodIngredient/Nutrition/Composition/RecipeVersion truth, schema,
migration, Planner, API or UI is changed by this delivery.

DC2 and DC3 remain **NOT STARTED**.

## Active sequence

```text
PR8 Planner v0                             COMPLETE
→ Gate1-A audit baseline                  COMPLETE
→ DATA-CORPUS-V1 / DC0                    COMPLETE
→ DC1 source authority + coverage         ACTIVE / REVIEW-READY
→ DC2 food publication batches            NOT STARTED
→ DC3 recipe publication batches          NOT STARTED
→ DC4 readiness audit + Gate1 consumption NOT STARTED
→ GATE1-CLOSE                             NOT STARTED
→ PR9 Shopping Engine                     NOT STARTED
```

## Stop condition

Review/merge the DC1 evidence package only.

After DC1 review/merge, stop. Do not automatically start DC2, DC3, DC4,
Gate1-CLOSE, PR9, Retail, AI, Auth/PostgreSQL or the generalized Data Ingestion
Platform.
