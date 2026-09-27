# Current focus

Updated: 2026-09-27.

## Accepted state

PR104 / R1-B runtime is merged into `main` at:

`75e2854eff82955b5c01ccacaca35fe0fdc534bc`.

Accepted R1-B outcome:

- migration `0040_recipe_version_source_output`;
- immutable RecipeVersion source-output truth;
- one published inactive `SOURCE_VERIFIED` RecipeVersion:
  `USSR82-697 — Курица отварная`;
- exact CHICKEN_CATEGORY_1_RAW + ONION_BULB_FRESH V2 Composition bindings;
- deterministic input-composition energy 255.892000 kcal;
- four reviewed candidates remain blocked;
- no implicit yield/retention/transformation authority;
- one atomic publication transaction covers RecipeVersion + required bindings +
  final input-Nutrition validation.

## Current bounded operation

**PR104 POST-MERGE INTEGRITY CORRECTION — ACTIVE.**

Branch:

`fix/pr104-post-merge-integrity`.

Goal:

1. restore the accepted historical `state/progress.md` bytes accidentally removed
   by PR104 while preserving the legitimate R1-B entries;
2. replace SQLite-specific RecipeVersion schema introspection with SQLAlchemy
   reflection without changing persistence semantics;
3. append an explicit R1-B transaction-ownership clarification to the merged
   contract.

No schema/data/domain calculation change is authorized by this correction.

## Parallel next-step state

Issue #100 remains the next product/runtime dependency for R1-C.

PR105 is the docs-only #100 Planner energy-allocation Contract Gate. It must not be
merged until this post-merge integrity correction is accepted and PR105 is
synchronized with the corrected `main`.

## Stop boundary

Do not start or merge:

- migration 0041;
- Planner v0.4 runtime;
- R1-C;
- Recipe activation/transformation publication;
- R2/R3 corpus expansion;
- Gate1-CLOSE;
- Shopping/PR9;
- Prep/Retail/API/UI/Auth/PostgreSQL/AI.

After this correction is reviewed/merged, synchronize and review PR105.
