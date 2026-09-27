# Current focus

Updated: 2026-09-27.

## Accepted state

PR105 / #100 Planner energy-allocation Contract Gate is merged into `main` at:

`690a17a8c220e7e8f8e93bd63ba46356c73f0503`.

Canonical contract:

`docs/family-food/planner-energy-allocation-contract.md`.

PR106 remains accepted and preserves the repaired durable project history plus
the R1-B post-merge transaction/persistence corrections.

## Current bounded operation

**#100 PLANNER ENERGY ALLOCATION RUNTIME — AUTHORIZED / ACTIVE.**

Branch:

`feat/planner-energy-allocation-v04`.

Authorized scope:

1. migration `0041_meal_pattern_energy_allocation`;
2. optional immutable `energy_share` on Meal Pattern opportunities;
3. frozen per-opportunity shares on Household member selections;
4. reviewed allocation-ready versions of the bounded initial adult programs;
5. idempotent exact target-version program publication;
6. Planner `planner-v0.4` per-opportunity Serving allocation;
7. fixed non-recipe allocation reservation without inventing Nutrition;
8. deterministic allocation trace/replay and explicit unsupported states;
9. preservation of historical `planner-v0.3` behavior and persisted plans.

## Hard boundaries

- reference energy remains Nutrition-owned;
- Recipe Nutrition calculation/version remains unchanged;
- no exact Nutrition is invented for EAT_OUT/READY_MEAL/fixed sources;
- no role-name/equal-split allocation inference;
- PROGRAM overrides/CUSTOM allocation is explicit user-confirmed Household state;
- historical null-share selections remain readable but are unsupported for v0.4
  automatic generation;
- no R1-C production proof in this PR;
- no Recipe activation/transformation authority;
- no R2/R3 corpus expansion;
- no Gate1-CLOSE;
- no Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.

## Stop boundary

This operation ends at a review-ready runtime PR with migration, reviewed data
publication, Planner v0.4 and required adversarial verification.

Do not start R1-C merely because #100 runtime becomes review-ready.
