# Handoff

Updated: `2026-09-13`.

PR #35 is MERGED; accepted main is `7388d19677cffbf5cd6cb192eabc0b93cad870f7`.
R1/R2/R3/R4 are COMPLETE AS BLOCKED RESEARCH. Assembly A remains BLOCKED at 2/3 individually ready families (R1-21, R1-23); family_count, optional_role and verified_substitution remain open. Assembly B and PR7+ are NOT STARTED.

Current bounded operation is [PR #36](https://github.com/Mitronomik/family-food-os/pull/36) on `codex/ru-normative-recipe-corpus`.
Verified runtime/acquisition head: `5f95530472e83748b67dd9efa9fa4542aeb5c546`.
It adds the pre-publication Russian normative recipe source corpus and migration `0030_recipe_source_corpus`; future RecipeTemplate migration is `0031_recipe_template_catalogue`.

Final verification on the synchronized head: focused tests PASS; Ruff PASS; full backend + launcher regression PASS; live acquisition PASS at exactly 214/214 section-scoped cards; exact repeat import inserted 0; DB invariants PASS; mirror navigation/footer/scripts are excluded from all 214 raw card bodies. The cleaned durable bundle is `data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19.bundle.json` with SHA-256 recorded in `data/curation/ru-normative-recipe-corpus/verification.json`.

PR #36 remains pre-publication only: no FoodIngredient/Nutrition/Composition authority changes, no RecipeVersion/RecipeTemplate publication, no Planner/MealPlan/Shopping/Prep/API/UI, no Assembly B or PR7 start.

Next: final review / merge decision for PR #36. Do not self-merge and do not start the next milestone automatically.
