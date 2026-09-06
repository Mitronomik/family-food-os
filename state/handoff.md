# Handoff

Updated: `2026-09-06`

## PR6 — Nutrition Core — READY FOR REVIEW

- Accepted starting main: `0979181409d34e4a193d58b60f4bbc8fa8d1e974`
  (PR #17 Agent Harness merged).
- Branch: `feature/pr6-nutrition-core`.
- PR5 Pantry remains COMPLETE; accepted closure evidence is in
  [progress](progress.md#pr5-closure).
- The [Nutrition Core contract](../docs/family-food/nutrition-core.md) owns the
  PR6 calculation/result policy and scientific source references.

Implemented on-demand Decimal FoodIngredient/RecipeVersion calculations and
member reference targets. Existing canonical profiles and immutable recipe
versions are reused. One SQLAlchemy Core read transaction supplies a coherent
input snapshot; Household member reads remain Household-scoped. No schema,
production data, API or frontend changes. Migration head is `0025_pantry`.

Verified focused Nutrition: **131 passed in 2.56s**. Affected catalogue,
Household and UoW: **225 passed in 10.20s**. Production audit: all 30 recipes
INCOMPLETE; 123 missing-density rows, 35 unsupported piece-mass rows. Full
reason counts and limitations are in the canonical contract. Required full
backend + launcher regression: **3386 passed in 485.55s**, zero skips, with
`AI_ENABLED=false` and loopback access.

The prior sandbox run returned 3100 passed, 162 failed, 121 errors in 230.19s;
all failure/error entries were launcher tests, with loopback bind denied
(`PermissionError: [Errno 1] Operation not permitted`). No tests were weakened.
Ruff/format pass for all 13 changed Python files. Working/staged diff checks
and the final 18-file scope audit pass; publication changes only docs/state.

The only pre-existing unrelated local change is tracked `.DS_Store`; leave it
untouched and exclude it from every PR commit. No personal database was audited:
the coverage test seeded a temporary database from the accepted loaders.

## Next authorized action

Review the delivered PR6 branch/PR against its canonical contract and acceptance
evidence. Runtime verification is complete; final project acceptance is pending. PR6 is not COMPLETE. Never merge
without explicit post-review authorization. PR7 MealPlan/Serving and all later
milestones remain unauthorized. Source-backed density/piece-mass/fiber/estimation
curation is a follow-up recommendation only, not work authorized inside PR6.
