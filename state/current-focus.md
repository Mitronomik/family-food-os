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
- PR #42 — USSR82-267 profile-authority review = MERGED.
- Exact accepted `main` after PR #42: `c9fcaa782a9cb6b1a48d877fb251f3ee69cb4e7d`.
- Current accepted SQLite migration head: `0030_recipe_source_corpus`.
- Future RecipeTemplate schema reservation remains `0031_recipe_template_catalogue`; no RecipeTemplate runtime is authorized by PR #36–#42.
- The PR #36 214-card `RU_MR_2_4_0162_19` corpus remains evidence/source material; it does not publish RecipeVersion/RecipeTemplate and does not replace FoodIngredient/Nutrition/Composition truth.
- The v22.13 checkpoint remains a separate hash-pinned external evidence/reference source; its `USSR82-*` lineage is not merged into the PR #36 source identity.
- R1 / R2 / R3 / R4 remain COMPLETE AS BLOCKED RESEARCH; frozen accepted evidence remains unchanged.
- R1-21 and R1-23 remain INDIVIDUALLY_READY; accepted ready count remains 2/3.
- OPEN Assembly-A gates remain `family_count`, `optional_role`, `verified_substitution`.
- Assembly A remains BLOCKED; Assembly B, `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` and PR7+ remain NOT STARTED.

## Current authorized operation

`V22-13-267-KITCHEN-A` — bounded kitchen/process evidence review for
`USSR82-267 — Суп-пюре из моркови или репы`, following accepted PR #42.

Current delivery:

- [PR #43](https://github.com/Mitronomik/family-food-os/pull/43) — `research: resolve USSR82-267 kitchen/process evidence` — OPEN / VERIFICATION PENDING.
- Branch: `research/v22-13-267-kitchen-a`.
- Base: accepted `main` after PR #42, `c9fcaa782a9cb6b1a48d877fb251f3ee69cb4e7d`.
- Scope is research/data evidence + proposed measurement protocol + state only. No physical kitchen execution, runtime/domain code, schema/migration, production seed, FoodIngredient mutation, Nutrition/Composition promotion or RecipeVersion/RecipeTemplate/RecipeAssembly publication is claimed.

Exact reviewed external checkpoint SHA-256 remains:

`a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`.

## V22-13-267-KITCHEN-A findings

### Complete carrot / turnip branches

The 1982 Ministry collection, 1973 Ministry collection and 1987 professional
culinary textbook strongly corroborate one carrot-or-turnip soup-puree family.

The selected scope remains the published recipe-267 column-II + water batch:

- carrot 320 g **or** turnip 360 g;
- parsley root 10 g;
- onion 20 g;
- wheat flour 20 g;
- optional rice-groats garnish input 20 g;
- butter 20 g;
- milk 150 g;
- egg 10 g;
- water 700 g;
- published dish output 1000 g.

The turnip branch has a branch-specific 1–2 minute blanching step.

The bounded search did not recover a retained candidate-specific record that
separately establishes successful execution/testing of both complete selected
branches. Repeated normative/professional publication and collection-level
standardization therefore remain strong culinary evidence, not the accepted
complete-variant kitchen-verification evidence.

Decision:

`MEASURED_COMPLETE_VARIANT_KITCHEN_VERIFICATION_REQUIRED`.

`verified_substitution` remains OPEN.

### Optional crumbly-rice garnish

The 1973 Ministry collection strengthens the process evidence for crumbly rice:

- per 1 kg raw rice: 2.10 L water, 28 g salt, 180% cooking gain and 2.80 kg output;
- target moisture 70% with ±1.5 percentage-point tolerance;
- the same source states that required liquid varies with vessel size/shape;
- recipe 203 independently gives 72 g rice + 151 g water → 200 g cooked rice and 90 g + 189 g → 250 g.

The base process does not require separate added fat; fat may be added. This means
mandatory-fat double counting is no longer the primary garnish blocker.

For protocol planning only, the per-kilogram table arithmetically corresponds to
20 g raw rice → 42 ml base water, 0.56 g salt and 56 g theoretical output.
Those are not production values: the source itself makes the small-vessel liquid
requirement equipment-sensitive.

Decision:

`INSTITUTIONAL_CRUMBLY_RICE_PROCESS_ESTABLISHED__EXACT_20G_BINDING_BLOCKED`.

Source optionality remains established; production `optional_role` remains OPEN.

### Proposed verification protocol

`data/curation/v22-13-267-kitchen-a/kitchen-verification-protocol.json` defines a
future measured test but explicitly records `PROPOSED_NOT_EXECUTED`.

It requires:

1. the exact published 1000 g carrot branch;
2. the exact published 1000 g turnip branch with the blanching step;
3. retained actual input/output masses, equipment, timing and deviations;
4. a separately measured 20 g raw-rice garnish transformation without added fat;
5. service evaluation with and without the optional garnish;
6. no inference of nutrient retention from kitchen execution.

No physical test is claimed by PR #43.

## Assembly A status after KITCHEN-A research

Assembly A remains **BLOCKED** at 2/3 individually-ready families.

- `family_count` = OPEN. Recipe 267 remains not individually ready.
- `optional_role` = OPEN. Source semantics are clear; exact measured garnish binding is not.
- `verified_substitution` = OPEN. Both complete branches still require applicable retained kitchen evidence.

No accepted R1/R2/R3/R4 or PR40–PR42 evidence is rewritten.

## Next-step rule

Current next action is exact-head proportional verification and human review of
PR #43. Merge requires separate explicit post-review authorization.

The source-only path for recipe 267 has reached a practical boundary:

- if measured human kitchen execution is available, a separately authorized
  `V22-13-267-KITCHEN-B` may execute and retain the PR #43 protocol;
- if measured execution is not available, a separately authorized
  `RECIPE-ASSEMBLY-A-RECOVERY-B` should stop the 267 source-only path and choose
  the smallest alternate route capable of closing the remaining gates.

`V22-13-267-PROFILE-B` is not justified before the kitchen decision. No automatic
Assembly B, `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE`, PR7, Retail, AI, Auth or bulk
production-data import is authorized.
