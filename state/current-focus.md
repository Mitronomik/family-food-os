# Current focus

Updated: `2026-09-06`

## Latest completed milestone

`PR5 — Pantry — COMPLETE`

- [PR #15](https://github.com/Mitronomik/family-food-os/pull/15): MERGED;
- accepted/merged head: `4778b6e99fde027be7e70b8a8966db85394e100d`;
- merge commit / verified main: `5f1bb47199ab661d58b92b8cbb9e40b4aeb7b0d0`;
- fully tested implementation: `d5b821ce9969ee2bf167333d9b48675d0f6d470f`;
- final project review: `PR5 FINAL REVIEW: ACCEPT — READY TO MERGE`.

The publication commit after the fully tested implementation changed only state
files. The accepted head and merge commit have identical file trees.
Accepted contract: [Pantry core](../docs/family-food/pantry-core.md).

Delivered: Household PantryItem and immutable PantryMovement, canonical
FoodIngredient units, exact Decimal balances, transactional add/consume/waste/
target-adjustment commands, metadata-only PATCH and deterministic FEFO/expiring
queries. SQLAlchemy Core repositories use the project UoW and additive SQLite
migration `0025_pantry`. Household isolation applies throughout.

## Accepted verification

PR5-CLOSE reuses the accepted verification from PR #15; no regression was rerun.
Focused Pantry: **267 passed**. Affected Household/FoodIngredient/Recipe/UoW:
**167 passed**. Migration selection: **142 passed**. Full backend + launcher:
**3255 passed in 467.40s**, zero skips. Ruff/diff and the PR5 30-file staged
scope audit: PASS. Exact evidence: [progress](progress.md#pr5-closure).

## Next authorized milestone

`PR6 — Nutrition Core — AUTHORIZED / NOT STARTED`

PR6 is the only newly authorized product milestone. Its bounded scope remains:

```text
FoodIngredient nutrition
→ RecipeVersion nutrition
→ Member target formula/config foundation
```

PR5-CLOSE is merged. The [agent harness](../docs/family-food/agent-harness.md)
is the active repository governance/instruction design. Its supporting governance
work does not start PR6 or add a product milestone. The next product work is a
separately bounded PR6 task from merged `main`, using the [handoff](handoff.md).

PR7 MealPlan / Serving, PR8 Planner and every later milestone remain unauthorized:
Shopping, Prep, Retail, AI, Auth, PostgreSQL, consumer PWA and Billing.
