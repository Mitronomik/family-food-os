# R2 breakfast Planner-capacity batch

Issue: #127.

Accepted base: `8995e85e4cda2ae30fc62fdc63daaf441f4226bd` (merged PR #126 / completed R1-C).

This bounded R2 batch follows Issue #99's selection rule: maximize the marginal
increase in realistic weekly variety and Planner capacity from accepted corpus
truth.

The current production bottleneck is BREAKFAST: one active exact-energy recipe can
cover only three opportunities under the unchanged repetition limit of 3. MAIN
already has three active exact-energy recipes and capacity for nine opportunities.

Selected School2022 cards:

- 54-1о — **Омлет натуральный** — 150 g / exact 225.5 kcal;
- 54-9к — **Каша вязкая молочная овсяная** — 200 g / exact 272.9 kcal.

Together with `HARD_BOILED_EGG`, the projected breakfast pool becomes three
RecipeVersions and capacity becomes nine opportunities/week.

The package deliberately creates identity-only `MILK_2_5` and `OAT_GROATS`.
It does not substitute nearby 2%/3.2% milk or rolled oats, and it publishes no
Nutrition/Composition authority for those new identities.

Prepared Nutrition reuses only the proven R1-F seam:
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.
Only ENERGY_KCAL is AVAILABLE; all other frozen nutrient codes remain UNKNOWN.

Household corroboration is used only to establish ordinary domestic executability.
School2022 remains the sole recipe/output/prepared-energy authority. Institutional
serving-temperature/equipment context and the unselected steam omelet alternative
are not promoted to consumer RecipeSteps.

No migration, Planner algorithm or new Nutrition authority is part of this batch.
