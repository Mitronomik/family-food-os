# FoodIngredient catalogue seed

This directory contains the reviewed canonical, platform-owned FamilyFoodOS
Food Catalogue. It is application seed data, not a test fixture and not an
upstream USDA bulk-data mirror. The accepted PR3 100-item technical slice is
preserved and expanded only with concepts required by the frozen PR4 MVP0 recipe
corpus.

## Scope

- `ingredients.csv`: 183 Russian-language canonical FoodIngredients.
- `aliases.csv`: deterministic Russian and English/source-resolution aliases.
- `nutrition.csv`: one current authoritative nutrition snapshot per ingredient.
- Source mix: 102 Foundation Foods records and 81 SR Legacy records.
- PR4-DATA expansion: 83 corpus-required concepts, comprising 15 Foundation
  Foods records and 68 SR Legacy records.
- All nutrition is per 100 g edible portion.
- All default units are `g`, so PR3 does not require unprovenanced density or a
  `pcs → grams` unit profile. `IngredientUnitProfile` is explicitly deferred.
- Edible fraction, storage profile and allergen review remain unknown unless a
  reviewed source is added. Unknown allergen state is represented as
  `allergens_reviewed=false`, never as “contains no allergens”.

## Authoritative sources and releases

The subset was curated on 2026-09-02 from the official downloadable CSV
archives published by USDA FoodData Central:

1. Foundation Foods, April 2026 release / FoodData Central Version 15.0,
   archive `FoodData_Central_foundation_food_csv_2026-04-30.zip`.
2. SR Legacy, final April 2018 release,
   archive `FoodData_Central_sr_legacy_food_csv_2018-04.zip`.

Each nutrition row stores the authoritative FDC ID, release identifier, data
type, original USDA food description and the energy nutrient ID used. The full
upstream archives are deliberately not committed.

USDA FoodData Central data are in the public domain, are not copyrighted, and
are published under CC0 1.0 Universal. Attribution:

> U.S. Department of Agriculture, Agricultural Research Service, Beltsville
> Human Nutrition Research Center. FoodData Central.

Source and licensing page: <https://fdc.nal.usda.gov/>. Download inventory:
<https://fdc.nal.usda.gov/download-datasets/>.

## Transformation and review rules

- Only `Foundation` and `SR Legacy` data types are allowed. Branded Foods,
  retailer labels, blogs and model-generated values are excluded.
- Foundation Foods has priority. SR Legacy is used only for ordinary gaps such
  as oils, butter, salt, basic herbs, barley, pasta, quinoa, lemon and white
  beans.
- Required nutrient IDs are protein `1003`, total lipid `1004`, carbohydrate by
  difference `1005`, and energy. Foundation energy priority is `2048`, then
  `2047`, then `1008`; SR Legacy uses `1008`. Fiber `1079` is retained when the
  selected record supplies it and otherwise remains null.
- Selected rows missing energy or any required macro were rejected.
- Negative and non-finite values were rejected.
- Published decimal amounts were parsed as Decimal and normalized to six
  decimal places with the repository's half-up convention before check-in.
- Russian canonical codes, names and aliases were curated manually against the
  selected FDC descriptions. They are catalogue mappings, not USDA translations.
- `estimated` remains null because this slice does not reinterpret USDA's
  analytical and calculated-value methodology as a boolean certainty claim.

Catalogue cardinality is intentionally not enforced by the production loader.
The historical PR3 80–120 range was a technical-slice acceptance criterion, not
a permanent platform maximum. Bounded milestone fixture limits belong in their
curation evidence and tests; the PR4 MVP0 subset is recorded separately under
`data/curation/pr4/mvp0-food-ingredient-codes.txt`.

## Known limitations

This remains a bounded catalogue revision, not complete Russian food-market
coverage. The broader MVP target remains approximately 250–350 canonical
FoodIngredients and may be reached only through later reviewed data work.
Some canonical names intentionally use one practical USDA representative (for
example one apple or potato record), so later catalogue expansion may introduce
materially distinct varieties only when recipes or nutrition behavior justify
them. No shelf-life, density, piece-mass conversion, regulatory allergen review,
retailer identity, price or availability claim is made here.
