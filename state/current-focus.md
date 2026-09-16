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
- Exact accepted `main` after PR #39: `2707fab16f003c9942d0eb09edf99c790d98a16f`.
- Current accepted SQLite migration head: `0030_recipe_source_corpus`.
- Future RecipeTemplate schema reservation remains `0031_recipe_template_catalogue`; no RecipeTemplate runtime is authorized by PR #36–#39.
- The PR #36 214-card `RU_MR_2_4_0162_19` corpus remains evidence/source material; it does not publish RecipeVersion/RecipeTemplate and does not replace FoodIngredient/Nutrition/Composition truth.
- The v22.13 checkpoint remains a separate hash-pinned external evidence/reference source; its `USSR82-*` lineage is not merged into the PR #36 source identity.
- R1 / R2 / R3 / R4 remain COMPLETE AS BLOCKED RESEARCH; frozen accepted evidence remains unchanged.
- R1-21 and R1-23 remain INDIVIDUALLY_READY; accepted ready count remains 2/3.
- OPEN Assembly-A gates remain `family_count`, `optional_role`, `verified_substitution`.
- Assembly A remains BLOCKED; Assembly B and PR7+ remain NOT STARTED.

## Current authorized operation

`V22-13-CANDIDATE-A` — review a very small candidate set from the accepted PR #39 MAP-A funnel and attempt to reduce the open Assembly-A evidence objectives without changing production food/nutrition/composition truth or publishing templates/assemblies.

Current delivery:

- [PR #40](https://github.com/Mitronomik/family-food-os/pull/40) — `research: narrow v22.13 Assembly A candidate recovery` — OPEN / HUMAN REVIEW REQUIRED.
- Branch: `research/v22-13-candidate-a`.
- Base: accepted `main` after PR #39, `2707fab16f003c9942d0eb09edf99c790d98a16f`.
- Scope is research/data curation + state only. No runtime/domain code, schema/migration, production seed, FoodIngredient mutation, Nutrition/Composition promotion, RecipeVersion/RecipeTemplate/RecipeAssembly publication or accepted prior evidence package is changed.

The accepted MAP-A package is:

`data/curation/v22-13-map-a/`.

Exact reviewed source checkpoint SHA-256 remains:

`a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`.

## V22-13-CANDIDATE-A findings

Exactly three leads are reviewed:

1. `USSR82-267` — `Суп-пюре из моркови или репы` — PRIMARY third-family recovery lead.
2. `USSR82-459` — `Яичница глазунья (натуральная)` — SECONDARY source-choice/substitution lead.
3. `USSR82-323` — `Картофель отварной` — `family_count` fallback.

For `USSR82-267`, the source establishes at source level:

- carrot **or** turnip as an explicit alternative with exact distinct net masses;
- rice as a separate garnish and an explicit permission to prepare the soup without rice;
- exact source net masses for the bounded column-II branch;
- broth **or** water as the liquid branch.

The bounded recovery scope is column II + the source-authorized water branch. Carrot is the fixed branch for recovery review and turnip remains the source alternate branch.

Already reusable FamilyFoodOS identities in that bounded scope include `CARROT`, `TURNIP`, `ONION_YELLOW`, `FLOUR_WHEAT`, `BUTTER_UNSALTED`, `EGG`, and `WATER`.

Three exact food/form blockers remain:

- `Крупа рисовая` — current generic source identity is not silently mapped to long-grain `RICE_WHITE`;
- `Молоко пастеризованное 3,2%` — not silently mapped to current 3.25%, 2%, or another milk identity;
- `Петрушка (корень)` — not current parsley leaf.

Additional candidate-specific blockers remain:

- optional rice needs a truthful cooked-garnish producer/transformation binding;
- collection-level standardization evidence does not prove that complete carrot and turnip branches are a tested interchangeable FamilyFoodOS substitution pair;
- publication-rights scope remains separate;
- RU familiarity/editorial publication review remains separate.

For `USSR82-459`, the source has an exact 10 g table-margarine **or** 10 g butter choice, and an older collection corroborates that source structure. This remains source-choice evidence, not a verified substitution. The specific margarine identity is not current catalogue truth, the candidate has no clean optional-food role, and the family overlaps accepted egg family R1-23.

For `USSR82-323`, the fixed column-III + butter branch has low identity debt and explicit source input/output masses, but raw-to-cooked transformation binding, kitchen, rights and RU review remain. It can help `family_count` only and does not cover the collective optional/substitution requirements.

Detailed evidence is under `data/curation/v22-13-candidate-a/`.

## Assembly A status after Candidate-A

Assembly A remains **BLOCKED** at 2/3 individually-ready families.

- `family_count` = OPEN. `USSR82-267` is now the primary third-family recovery lead, but is not individually ready.
- `optional_role` = OPEN. Optional rice semantics are established at source level for `USSR82-267`, but the production template/process/identity/kitchen gate is not satisfied.
- `verified_substitution` = OPEN. Carrot/turnip and margarine/butter are source alternatives, but complete tested FamilyFoodOS substitution applicability is not established.

No accepted R1/R2/R3/R4 status or historical evidence package is rewritten.

## Next-step rule

Current next action: proportional verification and human review of PR #40. Merge requires separate explicit post-review authorization.

If Candidate-A is accepted, the proposed next bounded operation is `V22-13-267-ENABLE-A`:

1. resolve only the three exact food/form blockers for recipe 267 (`Крупа рисовая`, `Молоко пастеризованное 3,2%`, `Петрушка (корень)`);
2. define the optional-rice producer/transformation binding without treating raw rice nutrition as cooked-garnish nutrition;
3. search for candidate-specific evidence sufficient to decide complete carrot-vs-turnip kitchen/substitution applicability.

If candidate-specific kitchen/substitution evidence remains absent, `verified_substitution` stays OPEN even if the three food/form blockers are resolved.

`V22-13-267-ENABLE-A` is not authorized to start automatically. No automatic Assembly B, PR7, RecipeTemplate/RecipeVersion publication, FoodIngredient/catalogue mutation, Nutrition promotion, Retail, AI, Auth or bulk production-data import is authorized by this operation.
