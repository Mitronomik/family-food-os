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
- Exact accepted `main` after PR #40: `3144997f0464a741eb429325db6497887309a32b`.
- Current accepted SQLite migration head: `0030_recipe_source_corpus`.
- Future RecipeTemplate schema reservation remains `0031_recipe_template_catalogue`; no RecipeTemplate runtime is authorized by PR #36–#40.
- The PR #36 214-card `RU_MR_2_4_0162_19` corpus remains evidence/source material; it does not publish RecipeVersion/RecipeTemplate and does not replace FoodIngredient/Nutrition/Composition truth.
- The v22.13 checkpoint remains a separate hash-pinned external evidence/reference source; its `USSR82-*` lineage is not merged into the PR #36 source identity.
- R1 / R2 / R3 / R4 remain COMPLETE AS BLOCKED RESEARCH; frozen accepted evidence remains unchanged.
- R1-21 and R1-23 remain INDIVIDUALLY_READY; accepted ready count remains 2/3.
- OPEN Assembly-A gates remain `family_count`, `optional_role`, `verified_substitution`.
- Assembly A remains BLOCKED; Assembly B and PR7+ remain NOT STARTED.

## Current authorized operation

`V22-13-267-ENABLE-A` — bounded enablement review for `USSR82-267 — Суп-пюре из моркови или репы`, following accepted Candidate-A.

Goal:

1. resolve the exact identity/form meaning of `Крупа рисовая`, `Молоко пастеризованное 3,2%`, and `Петрушка (корень)` without silent reuse of narrower current foods;
2. determine whether the optional rice can be bound to a truthful cooked-garnish producer/transformation without hidden raw/cooked equivalence or unsupported institutional-batch scaling;
3. seek evidence sufficient to decide complete carrot-vs-turnip substitution applicability under the already accepted Assembly-A gate.

Current delivery branch: `research/v22-13-267-enable-a`.

Scope is research/data enablement + state only. No runtime/domain code, schema/migration, production seed, FoodIngredient mutation, Nutrition/Composition promotion, RecipeVersion/RecipeTemplate/RecipeAssembly publication or accepted prior evidence package is changed.

Exact reviewed external checkpoint SHA-256 remains:

`a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`.

## V22-13-267-ENABLE-A findings

### Food/form identities

The three previous source-label ambiguities are now narrowed to distinct future identity candidates:

- `Крупа рисовая` → candidate `RICE_GROATS_POLISHED`. Russian standards define rice groats broadly enough to include multiple grain types, so the unqualified source term must not silently reuse current long-grain `RICE_WHITE`.
- `Молоко пастеризованное 3,2%` → candidate `MILK_PASTEURIZED_3_2`. The exact fat class + pasteurized form is standardized and current mass-market evidence exists; current 3.25%/2% identities are not exact replacements.
- `Петрушка (корень)` → candidate `PARSLEY_ROOT_RAW`. Root is distinct from current parsley leaf; current availability is supported, but bounded evidence is specialty/B2B/e-commerce rather than accepted ordinary mass-market default coverage.

These are **research identity decisions only**. No FoodIngredient is created. The v22.13 reference nutrient rows remain evidence only and no new full production nutrient-vector authority is accepted.

### Optional rice binding

The 1982 collection contains candidate rice producers (`USSR82-747 — Рис отварной` and `USSR82-748 — Рис припущенный`), but neither can be silently bound to recipe 267:

- recipe 267 gives only 20 g raw rice and no numbered garnish producer/output mass;
- 747/748 contain their own fat and salt/liquid process;
- recipe 267 already contains 20 g butter;
- accepted Assembly-A evidence does not authorize proportional scaling from those published institutional batches.

Therefore the producer/transformation decision is `BINDING_BLOCKED`. Raw rice nutrition is not relabelled as cooked-garnish nutrition. Source optional-rice semantics remain established, while the production `optional_role` gate remains OPEN.

### Carrot / turnip evidence

The carrot-or-turnip family is strongly corroborated across:

- the 1982 Ministry collection;
- the 1973 Ministry collection;
- a 1987 professional culinary textbook.

This supports a canonical culinary-family relationship and Russian familiarity, but the bounded review still does not establish candidate-specific complete-variant kitchen/testing evidence required by the accepted FamilyFoodOS `verified_substitution` gate.

`verified_substitution` therefore remains OPEN.

### Production-data decision

`data/curation/v22-13-267-enable-a/data-enablement-plan.json` records:

- `status = WITHHELD_AUTHORITY_GATES`;
- `production_delta = null`.

Reasons:

- no accepted new full nutrient/profile authority for the three exact food forms;
- parsley-root default availability remains limited;
- rice-garnish producer/output/fat allocation remains ambiguous;
- complete carrot/turnip variant verification remains unestablished.

No accepted architecture or gate is relaxed to force progress.

## Assembly A status after enablement review

Assembly A remains **BLOCKED** at 2/3 individually-ready families.

- `family_count` = OPEN. Recipe 267 remains the primary third-family recovery lead but is not individually ready.
- `optional_role` = OPEN. Source optional-rice semantics are established, but authoritative cooked-garnish binding is blocked.
- `verified_substitution` = OPEN. Cross-edition family evidence is strong, but the accepted tested-complete-variant requirement is not met.

No accepted R1/R2/R3/R4/Candidate-A status or historical evidence package is rewritten.

## Next-step rule

Current next action is proportional docs/data verification and human review of the `V22-13-267-ENABLE-A` delivery. Merge requires separate explicit post-review authorization.

If accepted, the remaining work has split into two bounded problems, neither authorized automatically:

- `V22-13-267-PROFILE-A` — obtain/review production-grade full profile provenance for the three exact forms and decide any FoodIngredient/Nutrition/Composition promotion;
- `V22-13-267-KITCHEN-A` — obtain/run candidate-specific complete carrot/turnip kitchen verification and clarify exact optional-rice garnish process/batch applicability.

No automatic Assembly B, PR7, RecipeTemplate/RecipeVersion publication, FoodIngredient/catalogue mutation, Nutrition promotion, Retail, AI, Auth or bulk production-data import is authorized.
