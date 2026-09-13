# Current focus

Updated: `2026-09-13`.

- PR6 / PR6-CLOSE = COMPLETE.
- PR #34 = MERGED.
- PR #35 = MERGED.
- PR #36 — Russian normative recipe source corpus and bulk importer = MERGED.
- Exact accepted main after PR #36: `077d054373cc5f8e1813acdc2cbacb3746e1c11a`.
- Current accepted SQLite migration head: `0030_recipe_source_corpus`.
- Future RecipeTemplate schema reservation remains `0031_recipe_template_catalogue`; no RecipeTemplate runtime is authorized by PR #36.
- The 214-card source corpus remains evidence/source material; it does not publish RecipeVersion/RecipeTemplate and does not replace FoodIngredient/Nutrition/Composition truth.
- R1 / R2 / R3 / R4 remain COMPLETE AS BLOCKED RESEARCH; R1/R2/R3 evidence packages remain frozen.
- R1-21 and R1-23 remain INDIVIDUALLY_READY; ready = 2/3; third_candidate = none.
- OPEN Assembly-A evidence gates remain: family_count, optional_role, verified_substitution.
- Assembly A remains BLOCKED; Assembly B and PR7+ remain NOT STARTED.

Current authorized operation: documentation-only integration of the September 2026 Household Food OS product/security research and the explicit user decision for flexible member meal patterns plus a deterministic meal-pattern recommender.

Current delivery:

- [PR #37](https://github.com/Mitronomik/family-food-os/pull/37) — `docs: integrate Household Food OS product and security decisions` — OPEN / READY FOR HUMAN REVIEW.
- Branch: `docs/product-security-integration-final`.
- Base: accepted main after PR #36, `077d054373cc5f8e1813acdc2cbacb3746e1c11a`.
- Scope is documentation/governance only: no runtime code, schema/migration, corpus, RecipeTemplate/RecipeVersion publication or Nutrition/Composition authority changes.

Authorized documentation outcomes:

- preserve the current FastAPI/Python, SQLAlchemy Core/UoW and ordered SQLite migration architecture; no greenfield reboot;
- integrate Household-first product strategy, household reconciliation, mixed meal sources, Reality/replan and execution/mental-load metrics;
- require configurable member meal patterns (initial supported product range 1–6 eating opportunities/day, heterogeneous by member) rather than dinner-only or fixed three-meal domain logic;
- define a deterministic, versioned, curated wellness Meal Pattern Recommender that requires user acceptance and does not invent therapeutic diets;
- establish a canonical secure-by-design contract covering object authorization, importer/SSRF boundaries, Retail, Auth, AI/prompt injection/tool abuse, privacy/children data and supply-chain/release controls;
- record the external TAS/RBS/bootstrap package as research/reference, not repository architecture authority;
- amend future PR7/PR8 and later security-gate requirements without automatically starting those milestones;
- preserve the implemented Recipe Catalogue classification contract: `MealRole` is not `RecipeVersion.meal_type_code`, and future planning uses deterministic suitability/mapping rather than repurposing the existing recipe enum;
- make MealPlan source explicit so RecipeVersion/RecipeAssembly references are conditional on source kind and leftovers/prepared/ready/out-of-home events do not require synthetic recipes.

Compatibility correction included in PR #37:

- `docs/family-food/architecture-addendum-2026-09-13.md` is the canonical compatibility addendum for these PR7/PR8 seams;
- `meal-pattern-programs.md`, `master-roadmap-addendum-2026-09-13.md` and `technical-spec-addendum-2026-09-13.md` reference and enforce the same rules;
- no runtime/schema/migration/corpus change is introduced by this correction.

Review-blocker resolution included in PR #37:

- mixed-source authority/capability matrix separates PR7 representation from Planner auto-selection; PR8 baseline auto-selects only RecipeVersion/RecipeAssembly-backed sources, while LEFTOVER/PREPARED/READY_MEAL/out-of-home sources remain gated by their authoritative state;
- `MealPatternProgram` ownership is assigned to the platform Meal Pattern Catalogue, while accepted member selection remains Household-owned;
- required supporting operation `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` is inserted after Assembly B and before PR7 without changing numbered milestone order;
- `validated 1–6` terminology is corrected to an initial supported product range; evidence/safety remains program-specific;
- canonical base documents link to their 2026-09-13 addenda;
- `.github/workflows/docs-verification.yml` implements the required docs-tier `git diff --check`, staged `git diff --cached --check`, scope listing and repository-relative link gate.

Next authorized action: current-head docs verification must PASS, then human re-review of corrected PR #37. Merge requires separate explicit post-review authorization. No automatic merge, Assembly B, PR7, Retail, AI, Auth, new production recipe publication or new donor/data-repair operation is authorized by this documentation work.
