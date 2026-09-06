# Handoff

Updated: `2026-09-06`

## Active agent harness

The [agent harness](../docs/family-food/agent-harness.md) is the active repository
governance/instruction design. [PR #17](https://github.com/Mitronomik/family-food-os/pull/17)
carries this supporting governance change from the verified PR #16 merge/base
`abcb1ca8d464477baed72cdf8e06a0d126b5e743`. The disposition ledger and
[eval evidence](../docs/family-food/agent-harness-evals.md) document the result.
It changes no runtime/schema/data, adds no product milestone and does not start
PR6. The next separately bounded product work is PR6. UI harness P2 is not a
PR6 blocker.

## PR5 — Pantry — COMPLETE

## PR6 — Nutrition Core — AUTHORIZED / NOT STARTED

### PR5 closure evidence

- [PR #15](https://github.com/Mitronomik/family-food-os/pull/15): MERGED;
- accepted/merged head: `4778b6e99fde027be7e70b8a8966db85394e100d`;
- merge commit / verified main: `5f1bb47199ab661d58b92b8cbb9e40b4aeb7b0d0`;
- fully tested implementation: `d5b821ce9969ee2bf167333d9b48675d0f6d470f`;
- final project review: `PR5 FINAL REVIEW: ACCEPT — READY TO MERGE`.

No PR carries unfinished Pantry work. The publication commit changed only state
files; the accepted head and merge commit have identical file trees.
PR5-CLOSE reuses PR #15's accepted verification: **267 passed** focused Pantry,
**167 passed** affected Household/FoodIngredient/Recipe/UoW, **142 passed**
migration selection and **3255 passed in 467.40s**, zero skips, full backend +
launcher. Ruff/diff/staged scope: PASS. No new regression run is claimed.
Details: [progress](progress.md#pr5-closure) and
[accepted Pantry contract](../docs/family-food/pantry-core.md).

### PR6 scope and foundations

Only PR6 Nutrition Core is newly authorized:

```text
FoodIngredient nutrition
→ RecipeVersion nutrition
→ Member target formula/config foundation
```

Read the [master roadmap](../docs/family-food/master-roadmap.md),
[architecture](../docs/family-food/architecture.md) and the PR6 contract in the
[migration plan](../docs/family-food/migration-plan.md) before implementation.

**FoodIngredient:** nutrition truth starts from canonical platform-owned
FoodIngredient nutrition data and its source/version/provenance. Do not use
legacy Ingredient, RetailSKU, Pantry quantity or LLM-generated nutrition facts.

**RecipeVersion:** derive nutrition deterministically through
`RecipeVersion → RecipeIngredient → FoodIngredient nutrition`. RecipeVersion
remains immutable/versioned. PR6 may calculate recipe totals and per-base-serving
nutrition, versioned member target formula/config foundations, explicit
warnings/uncertainty, provenance propagation and deterministic rounding/config
versions within its canonical contract. Serving, member/day totals and week
aggregates begin only in PR7.

**Pantry:** PR5 is complete, but Pantry is outside PR6 nutrition calculation
scope. PR6 must not consume stock, mutate Pantry, calculate Shopping or use
expiry/FEFO as nutrition truth. Later Planner/Shopping contexts may use Pantry
only when their milestones are authorized.

**Persistence:** the current custom SQLite migration chain ends at
`0025_pantry`. If PR6 needs new durable nutrition schema, its implementation PR
must inspect the current chain and use the next authorized migration number.
PR5-CLOSE and harness governance introduce no migration or schema.
Continue the accepted synchronous SQLAlchemy Core / repository / project UoW
boundary and custom SQLite migration authority.

**Deterministic architecture:** `AI_ENABLED=false` must remain sufficient.
Critical calculations belong to backend services/domain. LLM is not a source of
truth for kcal, protein/fat/carbohydrates, nutrient values, serving mass or member
targets. Preserve provenance and explicit uncertainty; do not invent nutrition
facts or medical claims.

### Next product work

PR5-CLOSE is merged. PR6 remains AUTHORIZED / NOT STARTED and belongs to a
separate bounded implementation task from merged `main`. Harness governance
contains no PR6 implementation and does not change its scope or authorization.

PR7 MealPlan / Serving, PR8 Planner and every later milestone remain unauthorized:
Shopping, Prep, Retail, AI, Auth, PostgreSQL, consumer PWA and Billing.
