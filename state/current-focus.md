# Current focus

Updated: `2026-09-23`.

## Accepted state

PR86 is merged into `main` at
`ef021c44e3166fbd2aa930c35b57dcb258e11bcc`.

Steps 1–5, the Step 6 Contract Gate and Step 6A runtime are accepted.

## Current bounded state

**Step 6B runtime is review-ready in PR87.**

Verified runtime/test head:
`8853d2a09240d26997c83915bc4167ab39979323`.

Canonical contract:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

Implemented Step 6B:

- MealPlan-owned `MealPlanMemberReferenceMethodologyPin`;
- complete-or-zero methodology pin sets;
- exact immutable Step 6A reference-methodology selection ID;
- immutable authoritative member target-input snapshot;
- `MealPlan.week_start` reference date;
- Russian Step 5 applicability revalidation at pinning;
- SQLite-safe member updated-at CAS/write-intent guard;
- atomic MealPlan + meal-pattern pins + reference pins + events + Servings;
- migration `0037_meal_plan_reference_methodology_pins`;
- historical legacy zero-pin plans remain valid with no backfill.

## Final Step 6B verification

On `8853d2a09240d26997c83915bc4167ab39979323`:

- Docs #331 — SUCCESS;
- DC1 #193 — SUCCESS;
- Russian methodologies #98 — 380 passed;
- Registry V2 #139 — focused 257 passed, 4/4 backend shards SUCCESS,
  launcher 643 passed / 2 skipped;
- Partial profiles #109 — focused 228 passed, 4/4 backend shards SUCCESS,
  launcher 643 passed / 2 skipped.

Additional adversarial closure:

- methodology-aware revision 2 may pin a newer Step 6A selection without
  rewriting revision 1;
- foreign-Household reference selections fail closed;
- snapshot text lengths preserve the accepted 200-character Household contract;
- explicit Planner boundary test proves no automatic
  `reference_methodology_selection_ids` default switch.

## Hard boundaries

Step 6B does **not**:

- change Planner runtime behavior/defaults;
- make Russian group-reference automatic;
- change API/UI;
- persist `RU_SOURCE_NATIVE_*` in member pins;
- implement Step 7 transformation applicability;
- implement Steps 8–10;
- rewrite/backfill historical MealPlans.

## Stop boundary

PR87 is ready for final review after this docs/state receipt passes proportional
docs verification. Do not merge autonomously and do not start Step 7 or Step 10.
