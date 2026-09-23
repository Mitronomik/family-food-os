# Current focus

Updated: `2026-09-23`.

## Accepted state

PR86 is merged into `main` at
`ef021c44e3166fbd2aa930c35b57dcb258e11bcc`.

Steps 1–5, the Step 6 Contract Gate and Step 6A runtime are accepted.

Current bounded work is **Step 6B runtime — MealPlan member reference-methodology
pins + immutable member target-input snapshots only**.

Canonical contract:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

## Authorized Step 6B scope

Implement:

- `MealPlanMemberReferenceMethodologyPin` as a MealPlan-owned dependent record;
- complete-or-zero reference-methodology pin sets;
- authoritative member snapshot:
  birth_date / sex / height_cm / weight_kg / activity_level / goal /
  member_updated_at;
- exact Step 6A selection ownership validation;
- `MealPlan.week_start` as the frozen target reference date;
- Russian Step 5 applicability revalidation at plan pinning;
- member state-token CAS/write-intent revalidation before commit;
- atomic persistence with MealPlan + meal-pattern pins + events + Servings;
- migration `0037_meal_plan_reference_methodology_pins`;
- legacy zero-pin plan compatibility;
- focused + full verification required by the merged contract.

## Hard boundaries

Step 6B does **not**:

- change current Planner behavior/defaults;
- make Russian group-reference automatic;
- change API/UI;
- persist `RU_SOURCE_NATIVE_*` in member pins;
- implement Step 7 transformation applicability;
- implement Steps 8–10;
- rewrite/backfill historical MealPlans.

## Stop boundary

Deliver Step 6B through exact-head verification and final review. Do not merge
autonomously and do not start Step 7 or Step 10 Planner integration.
