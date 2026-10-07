# DC4 Correction B — Planner → MealPlan heterogeneous role/order mismatch

**Status:** ROOT CAUSE IDENTIFIED / no runtime authorization in this investigation
**Issue:** #167
**Accepted main:** `c521e6d89a4d9fcc2900804ff7e05de66f14b093` (merged PR #165)
**Owner:** Planner domain; consumer contract: MealPlan + Serving
**Frozen fixture:** `docs/family-food/dc4-corpus-readiness-contract.md` §5, Fixture 3

## FACT — exact accepted failure

DC4 machine evidence and report confirm:

- Week `2026-09-14..2026-09-20` / `CUSTOM`, shared home events.
- Member 1 daily accepted roles = `BREAKFAST → LUNCH → DINNER`.
- Member 2 daily accepted roles = `BREAKFAST → DINNER`.
- Member 3 daily accepted roles = `DINNER`, excluded `BEEF_CATEGORY_1_RAW`.
- Pure Planner v0.4 returns a deterministic 21-event week with zero
  selected member-specific hard-exclusion violations.
- `MealPlanService.create_plan_revision()` rejects it with
  `Member event roles and order must match the accepted resolved schedule.`
- No persisted `MealPlan` Servings are accepted for Fixture 3. Fixtures 1 and
  2 persist successfully; bounded `MILK_2_5 + EGG` infeasibility is fail-closed.

## FACT — code-level disagreement

`backend/app/domain/planner.py::generate_week` builds household slots by
`(date, MealRole, occurrence)` and computes a *single global* `slot_order`
using:

```python
slot_order[key] = min(slot_order.get(key, order), order)
```

It then sorts household slots by:

```python
(local_date, slot_order[key], role.value, occurrence)
```

For Fixture 3, the global slot positions are:

| Role | Member 1 position | Member 2 position | Member 3 position | Global minimum |
| --- | ---: | ---: | ---: | ---: |
| BREAKFAST | 1 | 1 | — | 1 |
| LUNCH | 2 | — | — | 2 |
| DINNER | 3 | 2 | 1 | **1** |

The resulting deterministic order on each day is:

```text
BREAKFAST (min=1)
DINNER    (min=1)
LUNCH     (min=2)
```

This order is **valid only as a global min-priority sort**, not as the
accepted per-member order. For Member 1, the selected event sequence becomes
`BREAKFAST → DINNER → LUNCH` instead of the accepted
`BREAKFAST → LUNCH → DINNER`.

`backend/app/services/planner.py::PlannerService.generate_authoritative`
does not reorder this sequence; it converts each `PlannedEvent` to a
`MealEventDraft` with the Planner position and participant-specific portions.

`backend/app/domain/meal_plans.py::validate_complete_plan` sorts persisted
`HouseholdMealEvent` by `(local_date, position)` and reconstructs each
member's actual roles via their associated persisted
`Serving(event_id, member_id)`. It compares them against that member's
accepted resolved schedule using **ordered tuple equality**. The validator is
enforcing the existing contract and correctly rejects the Planner's sequence.

### Disposition

**LOCAL_PLANNER_ORDERING_BUG**, not a demonstrated need to relax or change
the Planner↔MealPlan cross-context contract.

The existing approved contract requires each member's accepted opportunity
order to be preserved. A global minimum position is not a valid substitute for
the union of participating members' precedence constraints.

## Expected minimally correct behavior

For Fixture 3, a valid shared household ordering is:

```text
BREAKFAST → LUNCH → DINNER
```

Even though Member 3 has only DINNER, that member's personal schedule order is
still respected: the projected subsequence is `DINNER`.

A runtime implementation should derive **deterministic household event ordering
that preserves every participating member's local precedence**. The design
should treat each member's accepted opportunity order as a partial-order
constraint, including repeated semantic roles and distinct occurrences.
Simple `min` sorting is insufficient; blindly replacing `min` with
`max` is not approved as a general algorithm without adversarial tests.

The next bounded runtime PR may adjust Planner's local ordering algorithm
**without changing the accepted cross-context contract**, provided the focused
reproduction and tests confirm there is no other contract discrepancy.

If implementation uncovers incompatible or cyclic per-member precedence,
it must return a bounded unsupported/failure result rather than silently
reordering a member's accepted pattern, deleting events or weakening
`validate_complete_plan`. Any need to redefine ordering identity, transaction
ownership, data shape or an immutable boundary **reopens the mandatory docs-only
Implementation Contract Gate before runtime implementation**.

## Required B2 tests

1. Exact frozen Fixture 3, unmodified:
   `3 / 2 / 1` roles; `21` MealEvents and `42` individualized persisted
   Servings; same seven-day week; real source-backed production catalogue.
2. Verify `[event.role for each member/day]` equals the accepted resolved
   `MemberMealPatternSelection` schedule **in order** before persistence.
3. Verify persisted `Serving` participation reconstructs the same member
   role sequence, including shared DINNER.
4. Member 3's hard beef exclusion remains enforced on selected shared DINNER.
5. Single-member DINNER and two-member BREAKFAST/DINNER regressions still pass.
6. Distinct repeated-role occurrences, varying opportunity counts and member
   permutations are deterministic; no missing/duplicate day slots.
7. Failure on genuinely incompatible cyclic ordering is bounded, has an
   actionable reason and persists no partial MealPlan.
8. Existing `MealPlanService.create_plan_revision` completeness checks remain
   unchanged and continue to reject invalid manually supplied weeks.
9. Planner trace/request fingerprint replay remains stable for identical inputs
   and version; changed algorithm output is versioned/justified under existing
   Planner configuration and trace contracts as applicable.
10. Migration head `0042`, no `0043`, `AI_ENABLED=false`.

Verification: focused Planner, MealPlan domain/application/persistence and
DC4 fixture integration; broaden if a shared cross-context seam changes.

## Proposed action and stop rule

**DECISION PROPOSED:** make a standalone Planner ordering correction PR after
this investigation is independently reviewed. No contract gate is needed *for
the identified ordering bug alone*, because no accepted contract change has
yet been shown. Verify this premise before implementation; if the runtime fix
requires a new cross-context contract, stop and do the docs-only gate instead.

This investigation changes no runtime/schema/data/Planner tests, does not
declare DC4 PASS and does not start Gate1-CLOSE or PR9.
