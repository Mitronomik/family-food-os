# Current focus

Updated: `2026-09-16`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- PR #34 = MERGED.
- PR #35 = MERGED.
- PR #36 — Russian normative recipe source corpus and bulk importer = MERGED.
- PR #37 — Household Food OS product/security integration = MERGED.
- PR #38 — v22.13 normative recipe dataset preflight = MERGED.
- PR #39 — v22.13 identity mapping and recipe-candidate classification = MERGED.
- PR #40 — bounded v22.13 Assembly-A candidate recovery = MERGED.
- PR #41 — USSR82-267 enablement blocker review = MERGED.
- PR #41 merge commit: `2b71c76c523c1b8a1ebeda9c5a2ba8fdc7157ced`.
- Current `main` before PR #42 branch: `63e35817503723e4cdc6a82c9000a13f1360d271`. Its tree is byte-identical to the PR #41 merge tree after immediate removal of an accidentally-created temporary placeholder on `main`.
- Current accepted SQLite migration head: `0030_recipe_source_corpus`.
- Future RecipeTemplate schema reservation remains `0031_recipe_template_catalogue`; no RecipeTemplate runtime is authorized by PR #36–#41.
- The PR #36 214-card `RU_MR_2_4_0162_19` corpus remains evidence/source material; it does not publish RecipeVersion/RecipeTemplate and does not replace FoodIngredient/Nutrition/Composition truth.
- The v22.13 checkpoint remains a separate hash-pinned external evidence/reference source; its `USSR82-*` lineage is not merged into the PR #36 source identity.
- R1 / R2 / R3 / R4 remain COMPLETE AS BLOCKED RESEARCH; frozen accepted evidence remains unchanged.
- R1-21 and R1-23 remain INDIVIDUALLY_READY; accepted ready count remains 2/3.
- OPEN Assembly-A gates remain `family_count`, `optional_role`, `verified_substitution`.
- Assembly A remains BLOCKED; Assembly B and PR7+ remain NOT STARTED.

## Current authorized operation

`V22-13-267-PROFILE-A` — production-profile authority review for the three exact food forms isolated by PR #41 for `USSR82-267 — Суп-пюре из моркови или репы`.

Current delivery:

- [PR #42](https://github.com/Mitronomik/family-food-os/pull/42) — `research: resolve USSR82-267 profile authority` — OPEN / READY FOR HUMAN REVIEW.
- Branch: `research/v22-13-267-profile-a`.
- Base: `63e35817503723e4cdc6a82c9000a13f1360d271`.
- Scope is research/data authority + state only. No runtime/domain code, schema/migration, production seed, FoodIngredient mutation, Nutrition/Composition promotion, RecipeVersion/RecipeTemplate/RecipeAssembly publication or accepted prior evidence package is changed.

Exact reviewed external checkpoint SHA-256 remains:

`a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`.

## V22-13-267-PROFILE-A findings

### `RICE_GROATS_POLISHED`

Official CREA food `000100 — Riso, brillato / Rice polished, raw` is an acceptable **profile-source candidate** for the generic polished-rice identity:

- 100 g basis, `Oryza sativa`, edible part 100%;
- 334 kcal, protein 6.7 g, fat 0.4 g, available carbohydrate 80.4 g, total fibre 1.0 g;
- analytical/method metadata are exposed per nutrient;
- source-imputed zero values are explicitly withheld rather than promoted.

Decision: `SOURCE_CANDIDATE_ACCEPTABLE_MAPPING_PENDING`.

No FoodNutritionProfile/NutrientVector/Composition is created.

### `PARSLEY_ROOT_RAW`

Norwegian Food Composition Table food `06.051 — Parsley root, Norwegian, raw` is an acceptable exact-form **profile-source candidate**:

- standardized parsley-root / raw classification;
- 46 kcal, protein 1.7 g, fat 0.3 g, carbohydrate 7.3 g, fibre 4.0 g per 100 g;
- source IDs are retained per nutrient;
- estimated-natural-zero and missing source classes remain non-authoritative.

The official API is not versioned, so any future production import must pin the exact source response/snapshot and retrieval/version identity.

Decision: `SOURCE_CANDIDATE_ACCEPTABLE_MAPPING_PENDING`.

PR #41's separate default-pool Russian market-eligibility limitation remains.

### `MILK_PASTEURIZED_3_2`

Current Russian retailer labels support the exact pasteurized 3.2% identity and show strong macro convergence, but retail product labels do not establish a generic category-level canonical profile.

NIZP PZH documents a comprehensive 1045-food full composition database, IV edition 2017, distributed under a license agreement. No licensed XLSX is present in the repository, so this operation does not assert an exact milk row or import any values from that database.

Decision: `BLOCKED_GENERIC_PROFILE_AUTHORITY`.

No cross-source hybrid profile is constructed.

### Production-data decision

`data/curation/v22-13-267-profile-a/data-enablement-plan.json` records:

- `status = WITHHELD_IMPLEMENTATION_AND_MILK_AUTHORITY`;
- `production_delta = null`.

Two source candidates are now strong enough for a later bounded source-pin/mapping/import operation. Milk profile authority remains a true data blocker.

## Assembly A status after profile-authority review

Assembly A remains **BLOCKED** at 2/3 individually-ready families.

- `family_count` = OPEN.
- `optional_role` = OPEN.
- `verified_substitution` = OPEN.

Profile-source discovery does not close PR #41's indepent carrot/turnip complete-variant kitchen requirement or cooked-rice-garnish process/batch binding.

## Next-step rule

Exact-head proportional docs/data verification is PASS for the current PR #42 delivery. Current next action is human review. Merge requires separate explicit post-review authorization.

If accepted, the proposed next bounded operation is `V22-13-267-KITCHEN-A`:

1. obtain/run candidate-specific complete carrot/turnip kitchen verification under the accepted substitution gate;
2. clarify the exact optional-rice garnish process/batch applicability without unsupported institutional-batch scaling or hidden fat allocation;
3. decide whether recipe 267 is still viable as the third Assembly-A family before implementing new production food profiles.

Only if recipe 267 remains viable should a later bounded `V22-13-267-PROFILE-B` implement the actually needed approved FoodIngredient/profile/vector/composition additions.

No automatic Assembly B, `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE`, PR7, RecipeTemplate/RecipeVersion publication, Retail, AI, Auth or bulk production-data import is authorized.
