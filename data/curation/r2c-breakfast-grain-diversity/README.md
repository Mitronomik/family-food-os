# R2-C breakfast grain diversity batch

Issue: #131.

Accepted base: `13a81d2497737f3b275b10055cd084548be02bf3` (merged PR #130).

The batch adds three School2022 milk porridges from different grain families:

- 54-13к — wheat milk porridge — 200 g / 270.3 kcal;
- 54-20к — buckwheat milk porridge — 200 g / 187.3 kcal;
- 54-25.1к — rice milk porridge — 200 g / 184.5 kcal.

Only `WHEAT_GROATS` is new and identity-only. Buckwheat and reviewed rice-groats
identities already exist. Milk 2.5%, butter, sugar, iodized salt and water reuse
accepted exact identities.

Prepared Nutrition remains
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.
Only ENERGY_KCAL is AVAILABLE; all remaining frozen nutrients are UNKNOWN.

Institutional serving-temperature requirements are provenance-only. Consumer
RecipeSteps preserve the source stovetop process, including explicit source time
ranges where present, without inventing scalar cook-time values.
