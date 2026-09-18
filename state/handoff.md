# Handoff

Updated: `2026-09-17`.

## Accepted base and governance

PR #52 is MERGED. PR7 is explicitly authorized by the user under Issue #53.

Accepted PR7 base:

`ded1cca29e165e0c459288d8de58df114abdeabb`

Accepted SQLite migration head:

`0031_meal_pattern_catalogue`

PR7 branch:

`feature/pr7-mealplan-serving`

Next reserved migration:

`0032_meal_plan_serving`

Future RecipeTemplate reservation remains `0033_recipe_template_catalogue`.

Canonical later decisions remain active:

- `master-roadmap-addendum-2026-09-13.md` for flexible meal patterns, mixed sources and PR7/PR8 amendments;
- `master-roadmap-addendum-2026-09-16.md` for dataset independence and Recipe Constructor/web-corroboration policy;
- `master-roadmap-addendum-2026-09-17-post-pr51.md` for PR7 sequencing and migration reservation.

## Current operation

`PR7 — MealPlan / Serving` / Issue #53 is ACTIVE.

Goal: create the Household-owned planning/history boundary that PR8 can automate later.

Implementation contract is in GitHub Issue #53. Core requirements:

- immutable/versioned `MemberMealPatternSelection` history;
- PROGRAM selection pins exact published `MealPatternProgramVersion`; CUSTOM remains available;
- persist the resolved accepted seven-day schedule snapshot so historical user overrides remain reproducible;
- initial validation supports 1–6 opportunities/day, but DB schema must not hardcode max six;
- append-only MealPlan revisions scoped by Household/week;
- each plan revision pins exact member-selection snapshots;
- Household events carry local date, deterministic position, `MealRole`, explicit source kind and conditional source reference;
- `COOK_RECIPE` requires immutable RecipeVersion; non-recipe sources do not require fake RecipeVersions;
- Servings define member participation and exact positive Decimal allocation;
- Serving nutrition and member/day/week aggregates scale existing Nutrition outputs; unknown stays unknown;
- synchronous SQLAlchemy Core repositories/UoW/read scopes; domain/services remain driver-independent;
- migration `0032` must preserve populated 0031 databases and update lineage/schema guards/legacy head expectations;
- full backend + launcher regressions are required before review-ready because persistence/migration/startup compatibility changes.

## Canonical invariants

- `MealPatternProgram` is platform-owned; `MemberMealPatternSelection` is Household-owned.
- `MealRole != RecipeVersion.meal_type_code`.
- `Recipe != Serving`.
- `representable != Planner-selectable` for non-recipe sources.
- Nutrition Engine is the only nutrient truth authority.
- true instants are UTC; planning dates are Household-local calendar dates.
- every Household-owned read/write is Household-scoped.
- deterministic core works with `AI_ENABLED=false`.
- no existing migration history rewrite.

## Explicit non-goals / stop conditions

Do not pull forward:

- PR8 Planner generation, recommender ranking or automated reconciliation;
- RecipeTemplate / RecipeAssembly implementation;
- Shopping / Prep / PreparedBatch / authoritative leftover supply;
- Retail / ready-food provider truth;
- AI Gateway;
- Auth/PostgreSQL/shared deployment;
- consumer frontend/onboarding;
- medical/therapeutic planning;
- legacy Order reuse as MealPlan.

After PR7 is review-ready and merged, stop. PR8 requires separate explicit user authorization.
