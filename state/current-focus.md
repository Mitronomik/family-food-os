# Current focus

Updated: `2026-09-16`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- PR #34 = MERGED.
- PR #35 = MERGED.
- PR #36 — Russian normative recipe source corpus and bulk importer = MERGED.
- PR #37 — Household Food OS product/security integration = MERGED.
- Exact accepted `main` after PR #37: `38de460dfcbf84997a1d9275314c4f3dab7e1d00`.
- Current accepted SQLite migration head: `0030_recipe_source_corpus`.
- Future RecipeTemplate schema reservation remains `0031_recipe_template_catalogue`; no RecipeTemplate runtime is authorized by PR #36/#37.
- The PR #36 214-card `RU_MR_2_4_0162_19` corpus remains evidence/source material; it does not publish RecipeVersion/RecipeTemplate and does not replace FoodIngredient/Nutrition/Composition truth.
- R1 / R2 / R3 / R4 remain COMPLETE AS BLOCKED RESEARCH; frozen accepted evidence remains unchanged.
- R1-21 and R1-23 remain INDIVIDUALLY_READY; accepted ready count remains 2/3.
- OPEN Assembly-A gates remain `family_count`, `optional_role`, `verified_substitution`.
- Assembly A remains BLOCKED; Assembly B and PR7+ remain NOT STARTED.

## Current authorized operation

`V22-13-DATA-INTEGRATION-PREFLIGHT` — read-only research/evidence review of the externally supplied `russian_normative_recipes_v22_13_checkpoint.zip` against current FamilyFoodOS food identity, Nutrition, Composition, Recipe/source provenance and Recipe Assembly A contracts.

Current delivery:

- [PR #38](https://github.com/Mitronomik/family-food-os/pull/38) — `research: preflight v22.13 normative recipe dataset` — OPEN / HUMAN REVIEW REQUIRED.
- Branch: `research/v22-13-data-integration-preflight`.
- Base: accepted `main` after PR #37, `38de460dfcbf84997a1d9275314c4f3dab7e1d00`.
- Scope is research/docs/state only. No runtime/domain code, schema/migration, production seed, FoodIngredient, Nutrition/Composition profile, RecipeVersion/RecipeTemplate/RecipeAssembly or accepted source-corpus row is modified.

External package is **not committed** by this operation. Exact reviewed ZIP SHA-256:

`a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`

Detailed workbook hashes and findings are retained in:

`docs/research/russian-normative-recipes-v22-13-preflight-2026-09-16.md`.

## Current preflight findings

- v22.13 contains 350 recipes and 6,179 ingredient contribution rows.
- 292 recipes are marked `READY_RAW` by the external checkpoint; this is raw/reference completeness, not FamilyFoodOS production readiness.
- The checkpoint contains 363 external ingredient/reference identities; they are not automatically FamilyFoodOS `FoodIngredient` identities.
- 99 reference records remain `UNRESOLVED`; 62 are `C_PROXY`; open reference queue = 58; open field-level nutrient gaps = 578.
- Raw numeric coverage is high, but strict A/B evidence coverage is materially lower.
- Retention coefficients are explicitly not applied; process/retention/cooked-state review remains separate.
- Optional/source-choice structure is useful: 41 optional rows across 13 recipes and 1,665 choice-group rows across 171 recipes.
- Source-listed alternatives do not by themselves satisfy FamilyFoodOS `verified_substitution`.
- A strict internal raw-data triage filter yields 64 leads, but no recipe/family is promoted to production status by this preflight.
- v22.13 source lineage is distinct from the PR #36 `RU_MR_2_4_0162_19` corpus and must remain separate unless later evidence proves an exact source relationship.

Integration decision in PR #38:

- **ADOPT** v22.13 as hash-pinned external evidence/reference material;
- **MAP** its ingredient, recipe and nutrient evidence through FamilyFoodOS authorities before use;
- **NEEDS_REVIEW** for proxy/unresolved/form/process/retention/source-rights/RU-familiarity/kitchen/substitution debt;
- **REJECT** direct production import or any interpretation of `READY_RAW`/`READY` as RecipeVersion/RecipeTemplate readiness.

## Assembly A status after v22.13 preflight

Assembly A remains **BLOCKED**.

- `family_count` = OPEN. Candidate funnel is much larger, but a third production-ready family is not established.
- `optional_role` = OPEN. The checkpoint contains explicit promising optional-role evidence, but candidate-specific mapping/source/rights/kitchen review remains required.
- `verified_substitution` = OPEN. Choice groups/source alternatives are not equivalent to tested substitution compatibility.

No accepted R1/R2/R3/R4 status or historical evidence package is rewritten by this preflight.

## Next-step rule

Next authorized action: human review of PR #38 and its docs-verification evidence.

If the preflight is accepted, the proposed next supporting operation is `V22-13-MAP-A` (map 363 external ingredient/reference identities and classify all 350 recipe candidates). **It is not authorized by this preflight and must not start automatically.**

Merge of PR #38 requires separate explicit post-review authorization. No automatic Assembly B, `V22-13-MAP-A`, PR7, RecipeTemplate/RecipeVersion publication, Nutrition promotion, Retail, AI, Auth or new production-data operation is authorized.