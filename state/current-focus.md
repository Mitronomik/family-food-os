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
- Current authorized operation: [PR #36](https://github.com/Mitronomik/family-food-os/pull/36), Russian normative recipe source corpus and bulk importer.
  Branch `codex/ru-normative-recipe-corpus`; pre-publication source corpus only.
- Verified live acquisition on pre-sync PR #36 head `a0d828105f7d04525abcd11a4571e0a2a1f53c3c`: 214/214 section-scoped cards acquired and imported; exact repeat import inserted 0 cards; focused tests, Ruff, DB invariants and artifact upload PASS.
- PR #36 is being synchronized onto merged PR #35 main and must be re-verified on the synchronized head before final acceptance.
- Current accepted main migration remains `0029_food_composition_core` until PR #36 is merged.
- PR #36 proposes `0030_recipe_source_corpus`; future RecipeTemplate schema becomes `0031_recipe_template_catalogue` if PR #36 is accepted and merged.
- Source-corpus ingestion does not publish RecipeVersion/RecipeTemplate and does not replace FoodIngredient/Nutrition/Composition deterministic truth.
- Assembly A = BLOCKED; Assembly B and PR7+ = NOT STARTED.

[Canonical R4 checkpoint](../docs/family-food/food-composition-and-assembly.md#recipe-assembly-a-r4--n50200-deep-viability),
[complete R4 evidence](../data/curation/recipe-assembly-a-r4-n50200/README.md), and
[Russian normative source-corpus contract](../docs/family-food/ru-normative-recipe-corpus.md).

Next authorized action: finish synchronization and verification of PR #36, then stop for final review.
No automatic merge, Assembly B, PR7, RecipeTemplate publication, or production recipe publication is authorized.
