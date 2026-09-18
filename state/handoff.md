# Handoff

Updated: `2026-09-18`.

## Accepted base and governance

PR #54 is MERGED and Issue #53 is CLOSED / COMPLETE.

Post-PR54 state synchronization is COMPLETE through merged PR #55.

Accepted PR7 product merge commit:

`3b1c8393c22461a1570d664ba5dcb035ec6cf633`

Merged PR7 delivery head:

`eea7c7bf61d1e20c5cfbce7a59a6e78e8dbcae70`

Accepted SQLite migration head:

`0032_meal_plan_serving`

Future RecipeTemplate reservation remains:

`0033_recipe_template_catalogue`

Canonical later decisions remain active:

- `master-roadmap-addendum-2026-09-13.md` for flexible meal patterns, mixed sources and PR7/PR8 amendments;
- `master-roadmap-addendum-2026-09-16.md` for dataset independence and Recipe Constructor/web-corroboration policy;
- `master-roadmap-addendum-2026-09-17-post-pr51.md` for the PR7 sequence and migration reservation, now fulfilled by merged PR7.

## Completed operation

`PR7 — MealPlan / Serving` / Issue #53 is COMPLETE through merged PR #54.

PR7 established:

- immutable/versioned Household-owned `MemberMealPatternSelection` history;
- exact PROGRAM-version or CUSTOM provenance with resolved seven-day snapshots;
- append-only Household/week MealPlan revisions with exact member-selection pins;
- explicit household meal source kinds;
- immutable RecipeVersion references for `COOK_RECIPE` without fake recipe requirements for non-recipe sources;
- individualized positive Decimal Servings defining participation;
- deterministic Serving/member/day/week nutrition composition through existing Nutrition truth with unknown propagation;
- Household-scoped SQLAlchemy Core repository/UoW/read boundaries;
- forward migration `0032_meal_plan_serving`.

Final PR7 verification evidence recorded on PR #54:

- focused PR7 verification: 60 passed;
- full launcher regression: GREEN;
- full backend regression on exact final PR head: 3292 passed, 1 warning in 664.05s (11:04);
- no PR8 / Shopping / Prep / Retail / AI / Auth / frontend scope was pulled forward.

## Next eligible operation

`PR8 — Planner v0` is NEXT / NOT STARTED.

No PR8 implementation is authorized by this handoff. Start it only after a separate explicit user authorization with a bounded task contract.

PR8 must consume the accepted PR7 model rather than rewrite it and must preserve the existing deterministic / `AI_ENABLED=false` architecture.

## Canonical invariants

- `MealPatternProgram` is platform-owned; `MemberMealPatternSelection` is Household-owned.
- `MealRole != RecipeVersion.meal_type_code`.
- `Recipe != Serving`.
- `representable != Planner-selectable` for non-recipe sources.
- Nutrition Engine is the only nutrient truth authority.
- true instants are UTC; planning dates are Household-local calendar dates.
- every Household-owned read/write is Household-scoped.
- no existing migration history rewrite.

## Stop condition

`PR8 — Planner v0` remains NOT STARTED. Begin it only after separate explicit user authorization and a bounded task contract.

Do not start Gate 1, Shopping, Prep, Retail, AI, Auth/PostgreSQL, frontend/onboarding or another future milestone automatically.
