# Current focus

Updated: `2026-09-16`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- PR #34 = MERGED.
- PR #35 = MERGED.
- PR #36 — Russian normative recipe source corpus and bulk importer = MERGED.
- PR #37 — Household Food OS product/security integration = MERGED.
- PR #38 — v22.13 normative recipe dataset preflight = MERGED.
- Exact accepted `main` after PR #38: `a852b169323cd4061c150107d7b75aebd67a9bc7`.
- Current accepted SQLite migration head: `0030_recipe_source_corpus`.
- Future RecipeTemplate schema reservation remains `0031_recipe_template_catalogue`; no RecipeTemplate runtime is authorized by PR #36/#37/#38.
- The PR #36 214-card `RU_MR_2_4_0162_19` corpus remains evidence/source material; it does not publish RecipeVersion/RecipeTemplate and does not replace FoodIngredient/Nutrition/Composition truth.
- The v22.13 checkpoint remains a separate hash-pinned external evidence/reference source; its `USSR82-*` lineage is not merged into the PR #36 source identity.
- R1 / R2 / R3 / R4 remain COMPLETE AS BLOCKED RESEARCH; frozen accepted evidence remains unchanged.
- R1-21 and R1-23 remain INDIVIDUALLY_READY; accepted ready count remains 2/3.
- OPEN Assembly-A gates remain `family_count`, `optional_role`, `verified_substitution`.
- Assembly A remains BLOCKED; Assembly B and PR7+ remain NOT STARTED.

## Current authorized operation

`V22-13-MAP-A` — map all 363 external v22.13 ingredient/reference identities against current FamilyFoodOS `FoodIngredient` truth and classify all 350 recipe candidates without promoting external Nutrition/Composition or publishing recipes/templates/assemblies.

Current delivery:

- [PR #39](https://github.com/Mitronomik/family-food-os/pull/39) — `data: map v22.13 identities and recipe candidates` — OPEN / VERIFICATION PENDING.
- Branch: `data/v22-13-map-a`.
- Base: accepted `main` after PR #38, `a852b169323cd4061c150107d7b75aebd67a9bc7`.

Scope is research/data curation plus state only. No runtime/domain code, schema/migration, production seed, FoodIngredient mutation, Nutrition/Composition promotion, RecipeVersion/RecipeTemplate/RecipeAssembly publication or accepted PR #36 source-corpus row is changed.

The accepted preflight is:

`docs/research/russian-normative-recipes-v22-13-preflight-2026-09-16.md`.

Exact reviewed source checkpoint SHA-256 remains:

`a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`.

## V22-13-MAP-A findings

All **363 / 363** external ingredient/reference identities are classified into one explicit mapping state:

- `EXACT_EXISTING`: 25;
- `ALIAS_EXISTING`: 27;
- `NEW_FOOD_CANDIDATE`: 103;
- `FORM_SPLIT_CANDIDATE`: 68;
- `COMPOSITE_OR_PROCESS_OUTPUT`: 114;
- `UNRESOLVED`: 25;
- `REJECT_TECHNICAL`: 1.

The 52 exact/alias mappings reuse FamilyFoodOS identity only; every mapping row explicitly keeps `nutrition_profile_promoted=NO`.

Across 6,177 nutrient-input-eligible contribution rows, exact/alias identity mappings cover 2,591 rows (~41.95%) and 386,274.014 g of 777,592.011 g represented input mass (~49.68%). These are mapping-coverage metrics, not Nutrition authority.

All **350 / 350** recipes are classified:

- `DIRECT_EXISTING_MAP_LEAD`: 3;
- `CATALOGUE_EXTENSION_LEAD`: 65;
- `PROCESS_REVIEW`: 88;
- `IDENTITY_REVIEW`: 134;
- `RAW_EVIDENCE_REVIEW`: 60.

The PR #38 strict raw-data triage set remains 64 recipes and decomposes after mapping into 3 direct-existing leads, 42 catalogue-extension leads, 12 process-review leads and 7 identity-review leads. Every recipe row explicitly keeps `production_ready=NO`.

Direct existing-identity leads are:

- `USSR82-323` — `Картофель отварной`;
- `USSR82-442` — `Макаронные изделия отварные`;
- `USSR82-453` — `Яйца вареные`.

They are candidate leads only. Rights/source lineage, exact quantity/form authority, kitchen verification, yield/retention/output semantics, RU familiarity where required and publication gates remain separate.

Detailed mapping package is under `data/curation/v22-13-map-a/`.

## Assembly A status after mapping

Assembly A remains **BLOCKED**.

- `family_count` = OPEN. Mapping yields 45 strict-raw direct/catalogue-extension leads, but no third production-ready family is established.
- `optional_role` = OPEN. Seven `READY_RAW` recipes contain explicit optional rows; none closes the original candidate-specific identity/source/rights/kitchen evidence gate.
- `verified_substitution` = OPEN. Fifteen strict-raw recipes contain explicit choice groups; a source-listed alternative is not a tested FamilyFoodOS substitution rule.

No accepted R1/R2/R3/R4 status or historical evidence package is rewritten.

## Next-step rule

Current next action is current-head proportional docs/data verification followed by human review of PR #39. Merge requires separate explicit post-review authorization.

If this mapping is accepted, the proposed next bounded research operation is `V22-13-CANDIDATE-A`: take a small candidate set and attempt to close one Assembly-A evidence objective at a time (`family_count`, `optional_role`, `verified_substitution`). It is **not** authorized to start automatically.

No automatic Assembly B, PR7, RecipeTemplate/RecipeVersion publication, FoodIngredient/catalogue mutation, Nutrition promotion, Retail, AI, Auth or bulk production-data import is authorized by this operation.
