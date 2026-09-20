# Current focus

Updated: `2026-09-20`.

## Accepted state

PR74 is merged at `4c9598b623b9042924bb1f8d864c56d3d0a407c4`.
PR75 is synchronized with that accepted main state.

On 2026-09-20 the user explicitly confirmed authorization to implement the PR75
Russian nutrition methodology layer and adapt the nutrition service toward a
working/effective state. The same decision explicitly approves the opt-in
`RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1` policy.

SQLite head remains `0032_meal_plan_serving`; reserved
`0033_recipe_template_catalogue` remains unchanged.

## Current authorized boundary

PR75 implements an explicit, versioned Russian methodology/internal-service layer:

- source-native available carbohydrate remains distinct from total carbohydrate;
- `RU_SOURCE_NATIVE_STRICT_V1` keeps below-detection values unavailable;
- `RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1` may interpret a literal printed
  source zero that remains `below_detection` as numeric `0` only with
  `estimated=true`, preserved censoring provenance, unknown detection limit and
  explicit warnings;
- the estimated-zero policy is not exact-zero authority, allergen absence or a
  default Planner/API/UI truth without pinned methodology;
- MR 2.3.1.0253-21 Appendix 3 energy coefficients are a separate versioned
  calculation path; published energy remains separate;
- Russian population references remain group references, not individualized or
  clinical targets;
- new services are explicit/opt-in and do not replace existing V1/NASEM defaults.

PR75 now binds its five-profile methodology trial to accepted PR74 evidence:
PR74 input/verification receipts, nonnumeric profile reviews and
`BLOCKED_PENDING_RIGHTS_REVIEW`. Numeric source output remains outside Git.

The numeric-free
[trial receipt](../data/curation/russian-methodology/trial-verification-receipt.json)
is the merge-review evidence. External local A/B trial hashes are not required
for merge acceptance and do not establish publication rights.

See
[Russian methodology contract](../docs/family-food/russian-nutrition-methodologies.md).

## Stop boundary

Review/merge of PR75 does not authorize:

- profile/schema migration or partial-profile persistence;
- a new nutrient registry publication;
- Book2002 source reuse or production profile publication;
- Russian target-table publication;
- Planner/API/UI default methodology changes;
- DC3, DC4, Gate1-CLOSE or PR9.

Those remain separately gated despite the approved PR75 calculation/service layer.
No autonomous merge.
