# PR4 verified Recipe Catalogue seed

This directory is the bounded, repository-owned production seed for
`PR4 — Verified Recipe Catalogue`. It was curated from the exact 30-source
corpus frozen in `data/curation/pr4/recipe-corpus.json`; it is not a runtime
import pipeline and performs no network access.

## Frozen result

- Recipes: **30** active platform-owned identities.
- RecipeVersions: **30** immutable `SOURCE_VERIFIED` v1 records.
- RecipeIngredients: **365** ordered lines using exactly the accepted 119
  FoodIngredient codes.
- RecipeSteps: **315** ordered, source-language instructions.
- RecipeEquipment rows: **0**. The reviewed cards contain contextual utensil
  words in directions but no dedicated source equipment inventory. PR4 does
  not infer equipment from culinary knowledge.

The PR4-DATA coverage matrix has 363 rows. One Bean Burrito Bowl row is the
explicit structural marker for its source-supplied pico de gallo subrecipe and
does not become an ingredient. Three water rows contain two explicit quantities
joined by “plus”; each becomes two RecipeIngredients so neither the initial nor
the added amount is lost. Thus `363 - 1 + 3 = 365`. No source ingredient is
hidden in free text.

## Source collection mix

| Collection | Recipes | Meal-type mapping |
| --- | ---: | --- |
| USDA FNS CACFP Home Childcare — Breakfasts | 3 | `breakfast` |
| USDA FNS CACFP Home Childcare — Main Dishes | 8 | `main` |
| USDA FNS CACFP Home Childcare — Side Dishes | 11 | `side` |
| USDA FNS CACFP Home Childcare — Salads | 3 | `salad` |
| USDA FNS CACFP Home Childcare — Sandwiches | 3 | `sandwich` |
| USDA FNS CACFP — Standardized Recipes Project 2024 | 2 | source title: Vegetable Frittata Bites → `main`; Cauliflower Rice → `side` |

## Deterministic transcription rules

- Prefer a source-supplied gram weight, then a source-supplied fluid measure,
  then an explicit count.
- Exact physical conversions are `1 oz = 28.349523125 g`,
  `1 lb = 453.59237 g`, `1 cup = 240 ml`, `1 Tbsp = 15 ml`,
  `1 tsp = 5 ml`, and `1 qt = 960 ml`.
- No ingredient-specific density, household-size mass, or nutrition conversion
  is inferred. Volumes remain `ml`; explicit counts remain `pcs` and are not
  rounded.
- Source alternatives retain their full wording in `source_amount_text`; the
  selected PR4-DATA branch is recorded in `normalization_note`.
- Time ranges use the maximum stated duration so `total_time_minutes` is a
  deterministic upper bound. Missing difficulty, batch, freezer, and storage
  claims remain null.
- `source_version` is `sha256:<full source_document_sha256>` and retrieval and
  review instants are frozen as `2026-09-04T00:00:00+00:00`.

## Provenance and rights review

`source-manifest.json` records the URL, collection, original serving count,
retrieval instant, full SHA-256, review status, rights basis, and evidence URL
for every source. All 30 documents are identified USDA Food and Nutrition
Service works. Each was reviewed for third-party copyright notices; none was
found. The recorded basis applies USDA ARS guidance that works prepared by
federal employees as part of official duties are public domain under
17 U.S.C. §105, while retaining USDA attribution.

## Reproduction

`scripts/build_pr4_recipe_seed.py` reconstructs both JSON files only when the
exact 30 source PDFs are supplied. The production seed loader reads only these
checked-in JSON artifacts and validates the frozen identity, provenance,
rights, serving, FoodIngredient-code, and count invariants before opening a
database.
