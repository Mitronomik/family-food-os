# Handoff

Updated: `2026-09-13`.

PR #35 is MERGED; accepted main is `7388d19677cffbf5cd6cb192eabc0b93cad870f7`.
R1/R2/R3/R4 are COMPLETE AS BLOCKED RESEARCH. Assembly A remains BLOCKED at 2/3 individually ready families (R1-21, R1-23); family_count, optional_role and verified_substitution remain open. Assembly B and PR7+ are NOT STARTED.

Current bounded operation is [PR #36](https://github.com/Mitronomik/family-food-os/pull/36) on `codex/ru-normative-recipe-corpus`.
Verified runtime/acquisition head: `5f95530472e83748b67dd9efa9fa4542aeb5c546`.
It adds the pre-publication Russian normative recipe source corpus and migration `0030_recipe_source_corpus`; future RecipeTemplate migration is `0031_recipe_template_catalogue`.

Historical verification on the synchronized runtime/acquisition head (not a new correction run): focused tests PASS; Ruff PASS; full backend + launcher regression PASS; live acquisition PASS at exactly 214/214 section-scoped cards; exact repeat import inserted 0; DB invariants PASS; mirror navigation/footer/scripts are excluded from all 214 raw card bodies. The cleaned durable bundle is `data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19.bundle.json` with SHA-256 recorded in `data/curation/ru-normative-recipe-corpus/verification.json`.

PR #36 remains pre-publication only: no FoodIngredient/Nutrition/Composition authority changes, no RecipeVersion/RecipeTemplate publication, no Planner/MealPlan/Shopping/Prep/API/UI, no Assembly B or PR7 start.

Review `5190228147` corrections are complete and READY FOR FINAL RE-REVIEW on the same PR36 branch, based on prior head `874879db6467eaebd045b853a1727fde539d1503`.
New evidence: 105 focused tests PASS with `AI_ENABLED=false`, Ruff check/format PASS, offline CLI imports 214 then 0 under the same document ID. Stale-hash and valid-rehash conflicting bundles both fail; complete DB dumps remain unchanged. Migration remains 0030 and production recipe versions remain unchanged (0 in the disposable replay).
The six-card bootstrap had six stale hashes hidden by the old reader; only those hash literals were corrected. The frozen 214-card bundle remains byte-identical at `ee0aad55080ba09294625af57800172862a53293518f7869e1b974ed7e9ab0b7`.
[Exact correction verification and initial failures](progress.md#pr36-final-provenanceidempotency-corrections).
Full regression was not rerun: shared runtime/persistence/startup infrastructure is unchanged. Keep the previous successful run as historical evidence only.

Worktree: `/private/tmp/ff-pr36-final`; Python runtime: `/Users/volkilli/Projects/family-food-os/backend/.venv/bin/python`. The primary checkout and unrelated `.DS_Store` were preserved.
Next: final human re-review of PR36. Do not self-merge or start the next milestone. Same-origin/redirect hardening remains a separate follow-up.
