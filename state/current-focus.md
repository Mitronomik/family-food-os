# Current focus

Updated: `2026-09-13`.

- PR6 / PR6-CLOSE = COMPLETE.
- PR #34 = MERGED at `a375f005b09880cf6a63cb5c8b1e964a0f558cb7`.
- R1 / R2 / R3 = COMPLETE AS BLOCKED RESEARCH; R1-21 and R1-23 remain the two individually-ready fixed 100-portion evidence families.
- PR #35 / R4-N50200 is OPEN, not merged. Final review result: **ACCEPT / READY TO MERGE** on head `e61c82b6a832c98a5c8f65a21bd26417e4b24549`; research result remains BLOCKED, ready 2/3, no production-data plan.
- Latest explicit user decision authorizes **RU-NORMATIVE-RECIPE-CORPUS** as the current implementation operation.
- Normative/base recipe cards may be retained/published as factual recipe data under the project-approved normative policy; provenance remains mandatory.
- Current branch: `codex/ru-normative-recipe-corpus`; PR #36 is OPEN and must merge only after PR #35 and re-synchronization with the resulting `main`.
- This operation adds a pre-publication source corpus and bulk importer; it does not publish RecipeVersion/RecipeTemplate truth.
- Complete MR 2.4.0162-19 manifest for appendices 5–8 contains **214 section-scoped cards**: 76 + 45 + 33 + 60. Repeated card numbers across appendices are distinct by `source_section_code`.
- Migration target becomes `0030_recipe_source_corpus`; future RecipeTemplate migration becomes `0031_recipe_template_catalogue`.
- Bulk acquisition is fail-closed: the Sudact mode must retrieve exactly the 214-card manifest before writing the document revision. Direct PDF/text import is also appendix-aware.
- The current execution environment has no outbound source-download capability and the Opera connector is not connected, so a live 214-page crawl has not been executed here; no missing card is fabricated or reported as imported.
- Assembly A remains BLOCKED; Assembly B / PR7+ remain NOT STARTED.

[Corpus contract](../docs/family-food/ru-normative-recipe-corpus.md).

Merge order / next state transition:

1. merge accepted PR #35;
2. verify new main and synchronize/rebase PR #36;
3. run affected repository verification for #36 and, in a network-enabled execution environment, execute the fail-closed 214-card acquisition/import;
4. final-review PR #36 before merge.

Never merge either PR autonomously.
