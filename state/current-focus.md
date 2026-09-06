# Current focus

Updated: `2026-09-06`

## Latest completed milestone

`PR5 — Pantry — COMPLETE`

[PR #15](https://github.com/Mitronomik/family-food-os/pull/15) is merged;
accepted head `4778b6e99fde027be7e70b8a8966db85394e100d`, merge commit
`5f1bb47199ab661d58b92b8cbb9e40b4aeb7b0d0`. Closure and accepted verification:
[progress](progress.md#pr5-closure). Contract:
[Pantry Core](../docs/family-food/pantry-core.md).

## Active authorized milestone

`PR6 — Nutrition Core — READY FOR REVIEW`

- Starting accepted main: `0979181409d34e4a193d58b60f4bbc8fa8d1e974`
  (PR #17 Agent Harness merged).
- Branch: `feature/pr6-nutrition-core`; [PR #18](https://github.com/Mitronomik/family-food-os/pull/18) → `main`, OPEN.
- Scope: on-demand FoodIngredient → RecipeVersion nutrition and member reference
  target foundation. Canonical policy and data gaps:
  [Nutrition Core](../docs/family-food/nutrition-core.md).
- Evidence and next action: [progress](progress.md#pr6-implementation-evidence)
  and [handoff](handoff.md).

No derived schema/cache, API, frontend or authoritative catalogue data changes.
SQLite migration head remains `0025_pantry`. The 30 production recipes all expose
incomplete totals because reviewed mass conversions are missing; source-backed
data work is a separate follow-up recommendation.

Required verification has passed and PR #18 is open. PR6 is ready for final review.
Implementation readiness is not PR6 COMPLETE; merge needs explicit post-review
authorization. The [agent harness](../docs/family-food/agent-harness.md) remains
active. PR7 MealPlan / Serving, PR8 Planner and every later milestone remain
unauthorized, including Shopping, Prep, Retail, AI, Auth, PostgreSQL, consumer PWA
and Billing.
