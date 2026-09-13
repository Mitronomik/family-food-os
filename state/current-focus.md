# Current focus

Updated: `2026-09-13`.

- PR6 / PR6-CLOSE = COMPLETE.
- [PR #34](https://github.com/Mitronomik/family-food-os/pull/34) = MERGED.
- [PR #35](https://github.com/Mitronomik/family-food-os/pull/35) = MERGED.
- Exact accepted main after PR #35: `7388d19677cffbf5cd6cb192eabc0b93cad870f7`.
- R1 / R2 / R3 / R4 = COMPLETE AS BLOCKED RESEARCH; R1/R2/R3 evidence packages remain frozen.
- R1-21 and R1-23 = INDIVIDUALLY_READY, unchanged exact published 100-portion scopes.
- ready = 2/3; third_candidate = none.
- OPEN Assembly-A evidence gates: family_count, optional_role, verified_substitution.
- R4-N50200 = COMPLETE AS BLOCKED RESEARCH; no executable production-data enablement plan was issued.
- Current authorized operation: [PR #36](https://github.com/Mitronomik/family-food-os/pull/36), Russian normative recipe source corpus and bulk importer; OPEN / REVIEW-READY, not merged.
- PR #36 is synchronized on accepted main. Runtime/acquisition verification head: `5f95530472e83748b67dd9efa9fa4542aeb5c546`.
- Live acquisition = PASS: exactly 214/214 section-scoped cards; exact repeat import inserted 0; page-chrome rows 0.
- Focused tests, Ruff, full `backend/app/tests + launcher/tests` regression, migration/import invariants and artifact capture = PASS on the verified head.
- Durable cleaned source snapshot: `data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19.bundle.json`.
- Current accepted main migration remains `0029_food_composition_core` until PR #36 is merged.
- PR #36 introduces `0030_recipe_source_corpus`; future RecipeTemplate schema is `0031_recipe_template_catalogue`.
- Source-corpus ingestion does not publish RecipeVersion/RecipeTemplate and does not replace FoodIngredient/Nutrition/Composition deterministic truth.
- Assembly A = BLOCKED; Assembly B and PR7+ = NOT STARTED.

Next authorized action: final human review / merge decision for PR #36, then stop.
No automatic merge, Assembly B, PR7, RecipeTemplate publication, production recipe publication or new donor/data-repair operation is authorized.
