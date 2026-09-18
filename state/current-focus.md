# Current focus

Updated: `2026-09-18`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` = COMPLETE through merged PR #51.
- PR7 / Issue #53 = COMPLETE through merged PR #54.
- PR8 / Issue #57 = COMPLETE through merged PR #59.
- Post-PR59 state synchronization = COMPLETE through merged PR #60.
- Accepted current main / Gate1-A base: `792d855448e16edcf36b41e0f6e321346fb915ed`.
- Accepted SQLite migration head: `0032_meal_plan_serving`.
- Future RecipeTemplate reservation remains `0033_recipe_template_catalogue`.

## Current authorized operation

`GATE1-A — Planning Core candidate data readiness` is **ACTIVE** under Issue #61.

Goal: close only the authoritative Nutrition/data gap required to exercise a successful repository-backed Planning Core fixture, while preserving the full 30-recipe corpus, provenance, uncertainty and deterministic Planner contracts.

Issue #61 is the bounded execution contract.

The exact-base fresh audit now records an evidence-capacity blocker: 29 current
versions are `INCOMPLETE`; the only technically eligible version is one
`breakfast` candidate. The three-meal fixture needs three breakfast, four main
and one sandwich versions under the repetition cap. No accepted exact evidence
on the starting tree closes the minimum seven-version gap. See
`data/curation/gate1a-data-readiness/`; Gate1-A remains active/not review-ready
pending authoritative primary evidence, with no production-data or schema
change made by the audit.

## GATE1-A bounded scope

- recompute the exact current blocker matrix for all 30 current verified RecipeVersions from a fresh migrated/seeded database;
- prove the minimum Planner-compatible candidate capacity required by the actual Gate 1 fixture schedules, `meal-role-recipe-v2` and `max_recipe_repetitions=3`;
- select the smallest evidence-backed repair subset instead of attempting to make all 30 recipes complete;
- repair only authoritative data/evidence/seed/immutable RecipeVersion truth justified by current evidence;
- update the real SQLite-backed Gate fixture so at least one Household reaches a persisted complete seven-day MealPlan with individualized positive Decimal Servings;
- keep an explicit hard-exclusion repository fixture and deterministic trace evidence;
- preserve unresolved recipes as unresolved;
- produce durable machine-readable readiness/capacity/before-after evidence;
- run focused/affected and exact-head full backend verification before review-ready.

## Architecture / migration boundary

- deterministic core must work with `AI_ENABLED=false`;
- Planner behavior must not be weakened to compensate for incomplete data;
- unknown Nutrition remains unknown and never becomes zero;
- estimates are not promoted to exact merely to obtain GREEN;
- current RecipeVersions are immutable; recipe-truth corrections publish a new version;
- provenance/version history remains append-only;
- technical fixture data is evidence, not architecture;
- no schema/migration is expected by default;
- migration `0033_recipe_template_catalogue` must not be consumed or renumbered;
- if a schema change is proven necessary, stop and request a separate migration decision.

## Explicit non-goals

Do not add or start:

- Gate1-CLOSE declaration;
- PR9 Shopping Engine;
- Prep / Freezer / PDF;
- Retail;
- AI Gateway / LLM;
- Auth/PostgreSQL/shared deployment;
- frontend;
- RecipeTemplate / RecipeAssembly implementation;
- advanced solver;
- therapeutic/medical planning;
- broad catalogue expansion or an attempt to make all 30 recipes consumer-ready.

## Active sequence

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         COMPLETE (#47 / PR #51)
→ PR7 MealPlan / Serving                     COMPLETE (#53 / PR #54)
→ PR8 Planner v0                             COMPLETE (#57 / PR #59)
→ GATE1-A candidate data readiness           ACTIVE (#61)
→ GATE1-CLOSE — Planning Core                NOT STARTED
→ PR9 Shopping Engine                        NOT STARTED
```

## Stop condition

After GATE1-A is review-ready and merged, stop for a separate Gate1-CLOSE review.

Do not begin PR9 automatically.
