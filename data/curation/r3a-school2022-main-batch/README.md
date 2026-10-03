# R3-A School2022 MAIN batch Contract Gate

Issue: #144.

Accepted base: `da6d1e05fd44ecc2733e1a6f472eae3e54b60604` (merged PR #142).

This package freezes the first enlarged DC3 recipe batch: **10 MAIN RecipeVersions**
from one School2022 source family, using the existing
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1` seam.

The batch is deliberately broader than the previous micro-PRs but remains bounded:

- 10 exact source cards;
- 5 new identity-only FoodIngredients;
- all other identities reused;
- no schema/migration/Planner change;
- ENERGY_KCAL only AVAILABLE; other 53 frozen nutrient codes UNKNOWN;
- no runtime publication in this gate.

The accepted durable source remains the existing private corpus archive and pinned
School2022 PDF. The public PDF was rechecked on 2026-10-03 only as corroboration.

See `docs/family-food/r3a-school2022-main-batch-gate.md`.

## Fail-closed source corrections

During gate review, School2022 `54-5м` and `54-12м` were removed from the selected batch because their ingredient tables name sunflower oil while their technology text names butter for the same cooking operation. No authority branch is inferred.

They were replaced by clean cards `54-4м` and `54-11р`. The gate also uses `WHEAT_BREAD_STALE_UNSPECIFIED_GRADE` where process text proves stale wheat bread but not flour grade.
