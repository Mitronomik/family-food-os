# Current focus

Updated: `2026-09-23`.

## Accepted state

PR85 is merged into `main` at
`e38692f7839ecab2da9499dc968dd01638227046`.

Russian-data integration Steps 1–5 and the corrected Step 6 Contract Gate are
accepted.

Current bounded work is **Step 6A runtime — MemberReferenceMethodologySelection
persistence only**.

Canonical contract:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

## Authorized Step 6A scope

Implement:

- immutable/versioned Household-owned `MemberReferenceMethodologySelection`;
- exact baseline + optional Step 5 Russian group-reference version resolver;
- persisted `acceptance_request_id` replay identity;
- `expected_current_selection_id` optimistic concurrency;
- Household/member state-token binding/revalidation;
- household-scoped repository/read history;
- additive migration
  `0036_member_reference_methodology_selection`;
- focused migration/service/repository/domain tests;
- required full regression from the merged contract.

## Hard boundaries

Step 6A does **not** change:

- MealPlan domain/table/repository/UoW;
- migration 0037 / Step 6B;
- Planner behavior/defaults;
- API/UI;
- source-native `RU_SOURCE_NATIVE_*` policy ownership;
- Step 7+.

Reserved `0033_recipe_template_catalogue` remains untouched.

## Stop boundary

Deliver Step 6A through exact-head verification and final review. Do not merge
autonomously and do not start Step 6B.
