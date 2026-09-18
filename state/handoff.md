# Handoff

Updated: `2026-09-18`.

## Accepted base and governance

PR #60 is MERGED.

The user explicitly authorized **GATE 1 — Planning Core** work.

Current bounded operation:

`GATE1-A — Planning Core candidate data readiness` — ACTIVE under Issue #61.

The exact `ce5cf6e2` implementation-base audit is now reproducible in
`data/curation/gate1a-data-readiness/`. It finds 29 `INCOMPLETE` versions and
one technically eligible conditional breakfast version. The minimum actual
three-meal capacity is eight versions (three breakfast, four main, one
sandwich), leaving a seven-version evidence gap. Existing accepted rows do not
contain enough exact same-form mass authority to bind that set without
promoting rejected estimates or inventing form/piece truth. Gate1-A is therefore
not review-ready; no schema, production truth, Gate1-CLOSE or PR9 work started.

Accepted starting main:

`792d855448e16edcf36b41e0f6e321346fb915ed`

Accepted SQLite migration head:

`0032_meal_plan_serving`

Future RecipeTemplate reservation remains:

`0033_recipe_template_catalogue`

## Why GATE1-A exists

PR8 is COMPLETE and the deterministic Planning Core is implemented and verified.

Accepted PR8 evidence:

- `planner-v0.2`;
- `meal-role-recipe-v2`;
- `meal-pattern-recommender-v2`;
- repository-backed authoritative application composition;
- deterministic trace;
- focused suite: **25 passed**;
- affected-context suite: **291 passed**;
- exact-head full backend run `35364987805`: **3317 passed, 1 warning in 537.77s (8:57)**.

Current authoritative blocker:

- the accepted 30-recipe corpus is present and verified;
- all 30 current RecipeVersion Nutrition results are `INCOMPLETE` with unknown kcal in the PR8 repository fixture;
- therefore no repository-backed fixture yet demonstrates the successful complete-week → individualized-Serving path required by the Planning Core gate.

The 2026-09-16 roadmap addendum permits a bounded data-gap closure when available data cannot supply enough valid candidates. It forbids redesigning Planner around the dataset or inventing missing truth.

## GATE1-A execution contract

Issue #61 owns the bounded task.

The first implementation step must recompute current truth from the exact base. Historical PR6 audits may guide prioritization but are not current authority.

Required operation:

1. fresh-database current 30-recipe blocker matrix;
2. mathematical role-capacity proof under current Planner compatibility/repetition rules and actual Gate fixtures;
3. smallest truthful repair target selection;
4. bounded authoritative data/evidence repair with no schema change by default;
5. real `PlannerService.generate_authoritative()` fixture proving at least one persisted complete seven-day MealPlan with individualized positive Decimal Servings;
6. explicit hard-exclusion repository fixture and deterministic trace;
7. reproducible evidence package;
8. focused/affected/full-backend verification.

Historical audit inspection suggests nearby candidates exist in the required `main`, `breakfast` and `sandwich` classifications, but Issue #61 explicitly forbids selecting targets until the current matrix is recomputed.

## Invariants

- `AI_ENABLED=false`;
- Nutrition/mass/form/kcal remain deterministic backend truth;
- unknown != zero;
- no REVIEW_REQUIRED_ESTIMATE is accepted merely for convenience;
- no global density/piece-mass shortcut that violates composition/measure authority;
- Planner eligibility is not weakened to accept `INCOMPLETE`;
- immutable RecipeVersion truth is not mutated in place;
- unresolved recipes remain explicit;
- no Retail/Shopping/Prep/AI/Auth/frontend scope;
- no `0033` consumption.

## Gate status

GATE1-A being ACTIVE does **not** mean Gate 1 is COMPLETE.

After GATE1-A merge, perform a separate **Gate1-CLOSE** evidence review against the canonical roadmap.

PR9 remains **NOT STARTED** until Gate1-CLOSE is explicitly accepted.

## Stop condition

After GATE1-A is review-ready/merged, stop for Gate1-CLOSE.

Do not begin PR9 automatically.
