# R2-B fish MAIN diversity batch

Issue: #129.

Accepted base: `1e4a0e137dee87f2aaef7d885481fef17f6e324c` (merged PR #128).

This batch moves from role-capacity closure to realistic weekly variety. It adds two
source-backed fish MAIN RecipeVersions with one shared, low-risk preparation
surface:

- School2022 54-6р — pink salmon in milk — 80 g / 144.8 kcal;
- School2022 54-7р — pollock in milk — 80 g / 105.3 kcal.

Both cards use exact 2.5% milk, onion, sunflower oil and iodized salt. The only new
FoodIngredients are identity-only species/form records for pink-salmon fillet and
pollock fillet. No Nutrition/Composition is inferred for them.

The retained source has a thawing alternative. One route is pinned for deterministic
corpus identity, but thawing logistics are deliberately not promoted to consumer
RecipeSteps. Consumer execution starts with already-thawed fillet. Institutional
serving-temperature and paraconvection context is also quarantined.

Prepared Nutrition reuses only
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.
Only ENERGY_KCAL is AVAILABLE; every other frozen nutrient remains UNKNOWN.

The earlier cod-cutlet follow-up is deferred because its exact retained source does
not establish the narrower high-grade/stale wheat-bread form proposed in an older
R1-G note. No unsupported identity narrowing is carried forward.
