# R2-D milk-exclusion breakfast resilience evidence

Issue: #133.

Accepted base: `463fe46f7c40156c1b8ebab5402ca45698d8c2bc` (merged PR #132).

This package records the fail-closed R2-D candidate audit. The product need is
real: five of six active exact-energy BREAKFAST recipes require `MILK_2_5`, so
excluding that FoodIngredient leaves one candidate and only three allowed uses per
week.

The closest retained School2022 candidates were audited:

- 54-1т — blocked by a source-card/menu prepared-energy discrepancy
  (301.2 vs 301.3 kcal for 150 g);
- 54-4т — blocked because process water used for vanillin is unquantified;
- 54-6т — blocked for the same unquantified process-water reason.

USSR82-459 and nearby egg recipes do not provide an accepted shortcut: current
repository inventory requires production reconciliation, and the retained
secondary 459 nutrient row has `EnergyQA=CHECK`.

No runtime publication, activation, FoodIngredient identity, migration or Planner
change is authorized by this package.

See `docs/family-food/r2d-milk-exclusion-breakfast-gate.md`.
