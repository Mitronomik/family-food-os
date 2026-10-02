# R1-C — Production persisted Planner proof

Issue: #124

Accepted production runtime: `e50da0d21a6c740e5d60c257ac64de12e0c5d2b3` (merged PR #123).

Implementation branch base: `5bf5127a238b8bb139903f008ad7c14b9b1309c7`
(merged state-only PR #125).

This package records the bounded R1-C product proof. It does not publish new food,
recipe or Nutrition authority.

The executable proof is
`backend/app/tests/test_r1c_production_planner_proof.py` and uses:

- real SQLite persistence and current migration head;
- persisted Household / HouseholdMember records;
- persisted CUSTOM MemberMealPatternSelection snapshots with explicit v0.4
  energy shares;
- ordinary active production RecipeVersions from merged R1-F/R1-H;
- neutral current Recipe Nutrition projections;
- `PlannerService.generate_authoritative(...)`;
- real MealPlan / Serving persistence.

The proof covers:

1. current production candidate metrics: 1 breakfast + 3 MAIN, all active,
   Planner-eligible and exact-energy-ready;
2. one seven-DINNER week generated and persisted using all three MAIN candidates
   under unchanged max repetition 3;
3. individualized positive persisted Serving portions driven by the accepted
   dinner energy share;
4. semantic replay and identical Planner trace fingerprint;
5. a materially different breakfast+dinner pattern that fails boundedly because
   breakfast capacity is insufficient, with no partial MealPlan;
6. a hard FoodIngredient exclusion that removes the affected meatball candidate,
   preserves unaffected candidate truth and persists no partial MealPlan;
7. migration head remains 0042; no migration 0043;
8. no Planner algorithm, schema or Nutrition-authority change.

`summary.json` is the durable metrics receipt asserted by the executable proof.

After R1-C review and merge, preserve the accepted sequence:
R2/R3 corpus expansion → DC4 / Gate1-CLOSE → PR9 Shopping.
No follow-up starts automatically.
