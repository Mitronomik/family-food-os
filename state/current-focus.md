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

Authorized documentation outcomes:

- preserve the current FastAPI/Python, SQLAlchemy Core/UoW and ordered SQLite migration architecture; no greenfield reboot;
- integrate Household-first product strategy, household reconciliation, mixed meal sources, Reality/replan and execution/mental-load metrics;
- require configurable member meal patterns (initial validated range 1–6 eating opportunities/day, heterogeneous by member) rather than dinner-only or fixed three-meal domain logic;
- define a deterministic, versioned, curated wellness Meal Pattern Recommender that requires user acceptance and does not invent therapeutic diets;
- establish a canonical secure-by-design contract covering object authorization, importer/SSRF boundaries, Retail, Auth, AI/prompt injection/tool abuse, privacy/children data and supply-chain/release controls;
- record the external TAS/RBS/bootstrap package as research/reference, not repository architecture authority;
- amend future PR7/PR8 and later security-gate requirements without automatically starting those milestones.

Current branch for this bounded docs operation: `docs/product-security-integration-final`.

Next authorized action: complete proportional docs-only verification and publish the documentation integration for human review. Stop after review-ready publication. No automatic merge, Assembly B, PR7, Retail, AI, Auth, new production recipe publication or new donor/data-repair operation is authorized by this documentation work.
