# Current focus

Updated: `2026-09-23`.

## Accepted state

PR85 is merged into `main` at
`e38692f7839ecab2da9499dc968dd01638227046`.

Russian-data integration Steps 1–5 and the corrected Step 6 Contract Gate are
accepted.

## Current bounded state

**Step 6A runtime is review-ready in PR86.**

Runtime verification head:
`e03be7b0c4a9b7766a961026cdf8de7d1f56d8d8`.

Canonical contract:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

Implemented Step 6A:

- immutable/versioned Household-owned `MemberReferenceMethodologySelection`;
- `FAMILY_FOOD_NUTRITION_V1` baseline;
- optional Step 5 Russian group-reference methodology;
- persisted request identity for commands that publish a new selection version;
- zero-write semantic no-op with intentionally unconsumed new request ID;
- expected-current optimistic concurrency;
- SQLite-safe Household/member CAS/write-intent token guard;
- household-scoped repository/read history;
- migration `0036_member_reference_methodology_selection`.

## PR86 blocker closure

Independent re-review blockers are resolved:

1. real SQLite concurrency is guarded by exact-token conditional UPDATE/CAS
   write intent; busy/locked competing writer becomes an application conflict and
   publishes no selection;
2. no-op request-id ambiguity is resolved explicitly in the canonical contract:
   no-op is zero-write and does not consume a new request ID;
3. durable state now records review-ready runtime and verification evidence.

## Exact runtime verification

On `e03be7b0c4a9b7766a961026cdf8de7d1f56d8d8`:

- Docs #314 — SUCCESS;
- DC1 #176 — SUCCESS;
- Russian methodologies #81 — 358 passed;
- Registry V2 #110 — focused 257 passed, 4/4 backend shards SUCCESS,
  launcher 643 passed / 2 skipped;
- Partial profiles #92 — focused 228 passed, 4/4 backend shards SUCCESS,
  launcher 643 passed / 2 skipped.

Any later branch-head change after that runtime head is docs/state only unless
explicitly recorded otherwise.

## Hard boundaries

Step 6A still does **not** change:

- MealPlan domain/table/repository/UoW;
- migration 0037 / Step 6B;
- Planner behavior/defaults;
- API/UI;
- source-native `RU_SOURCE_NATIVE_*` policy ownership;
- Step 7+.

Reserved `0033_recipe_template_catalogue` remains untouched.

## Stop boundary

PR86 is ready for final merge review. Do not merge autonomously and do not start
Step 6B before PR86 is merged and Step 6B is separately authorized.
