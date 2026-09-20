# Current focus

Updated: `2026-09-20`.

## Accepted state

PR70 and PR71 are merged. Accepted base:
`9b1d5c73da4f1d779336a35e0e7e2c2d32363e85`.
PR6/PR7/PR8, DC0 and DC1 recovery/reconciliation evidence are accepted.
No production DC2/DC3 publication, DC4, Gate1-CLOSE or PR9 completion is implied.
SQLite head remains `0032_meal_plan_serving`; reserved
`0033_recipe_template_catalogue` remains unchanged.

## Current authorized boundary

The bounded first DC2 source/form review package is complete in the PR #72
changeset. It reviews `DC2-REVIEW-001`; it does not publish production data or
change canonical nutrient/rights authority. See
[first-batch review](../data/curation/dc2-first-batch-review/README.md).

25 groups cover 1532 source occurrences, 24 book candidates and 14 prior visual
profiles. Group-level decisions are not 1532 individually accepted mappings.
359 routes are affected; 91 have all dependencies in review scope; 0 are newly
production-ready. Required policy and source decisions remain explicit in
[publication conditions](../data/curation/dc2-first-batch-review/publication-decisions.md).

Review/merge of this evidence package does not authorize production publication
or the next milestone.

## Stop boundary

After PR #72 review/merge, stop pending explicit scope for closing the concrete
form/source/rights/nutrient-method conditions and preparing a separately reviewed
DC2 publication payload through existing profile/vector/ATOMIC contracts.

Do not start DC3, DC4, Gate1-CLOSE, PR9/Shopping, Retail, AI,
Auth/PostgreSQL or generalized ingestion automatically.
