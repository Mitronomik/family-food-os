# PR4 Recipe seed

This directory is the deterministic production seed for the FamilyFoodOS PR4 Recipe Catalogue.

Authoritative curation inputs are the merged `data/curation/pr4-data2/**` corpus plus the reviewed ordered-step handoff at `data/curation/pr4-runtime/recipe-steps.json`. The compiler is `scripts/build_pr4_recipe_seed.py` and performs no network access.

Expected technical-slice output:

- 30 `Recipe` records;
- 30 immutable initial `RecipeVersion` records;
- 189 `RecipeIngredient` rows using exactly 81 existing `FoodIngredient` codes;
- 169 ordered source-derived `RecipeStep` rows;
- 86 ordered `RecipeEquipment` rows across 34 normalized equipment codes.

`source_document_sha256`, source identity, servings, meal type and source-specific rights basis are inherited from accepted PR4-DATA2 evidence. `source_retrieved_at` is optional: three exact historical acquisition instants are retained where they were independently recovered; unknown instants remain `null` rather than being invented.

Source binaries are not required at runtime. The checked-in JSON is reviewed structured data and the loader fails closed if it diverges from accepted DATA2 identities, hashes, servings, meal types, rights review or FoodIngredient coverage.
