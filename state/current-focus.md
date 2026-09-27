# Current focus

Updated: 2026-09-27.

## Accepted state

PR106 / PR104 post-merge integrity correction is merged into `main` at:

`cf96e9bb43bb991625a56d7d4c0fa0bad2842b1a`.

This accepted state includes:

- the full restored durable `state/progress.md` history;
- adapter-neutral RecipeVersion historical-schema introspection via SQLAlchemy;
- explicit R1-B cross-context transaction ownership;
- unchanged accepted R1-B runtime/data truth from PR104.

R1-B remains:

- migration `0040_recipe_version_source_output`;
- one published inactive `SOURCE_VERIFIED` USSR82-697 RecipeVersion;
- exact CHICKEN_CATEGORY_1_RAW + ONION_BULB_FRESH V2 Composition bindings;
- deterministic input-composition energy 255.892000 kcal;
- four reviewed blocked candidates;
- no implicit yield/retention/transformation authority.

## Current bounded operation

**#100 PLANNER ENERGY ALLOCATION IMPLEMENTATION CONTRACT GATE — ACTIVE.**

PR:

`#105`.

Branch:

`docs/planner-energy-allocation-contract`.

Canonical gate document:

`docs/family-food/planner-energy-allocation-contract.md`.

## Why this gate is required

Current `planner-v0.3` scales recipe Servings using the member's full weekly
reference energy divided by recipe-backed energy selected for the week.

That over-allocates valid partial-at-home patterns such as dinner-only and mixed
fixed-source days.

Preflight confirmed the current persisted Meal Pattern/selection model stores
opportunity roles/order but no per-opportunity energy allocation share.

Issue #100 explicitly requires an Implementation Contract Gate if current
persisted selection/config cannot represent allocation truth. That condition is met.

## Frozen direction under review

The gate proposes:

- `energy_share: Decimal | None` on platform MealPattern opportunities;
- the resolved/frozen share copied into Household member selections;
- daily planned share may be below 1, with the residual explicitly outside Planner;
- missing allocation fails closed;
- fixed non-recipe events reserve their opportunity share without claiming exact
  Nutrition;
- `planner-v0.4` calculates each recipe Serving from
  `reference_energy × opportunity_share / recipe_kcal`;
- historical `planner-v0.3` plans remain unchanged;
- expected migration:
  `0041_meal_pattern_energy_allocation`.

Exact persisted shares are planning-policy parameters, not medical or physiological
truth. Platform PROGRAM shares require reviewed evidence/provenance. PROGRAM
overrides and CUSTOM shares are explicit user-confirmed Household choices. Planner
must not infer any share from role names or opportunity count.

## Stop boundary

This PR is docs/state only.

Do not start:

- migration 0041;
- Planner v0.4 runtime;
- MealPattern/selection schema changes;
- R1-C;
- Recipe activation/transformation publication;
- R2/R3 corpus expansion;
- Gate1-CLOSE;
- Shopping/PR9;
- Prep/Retail/API/UI/Auth/PostgreSQL/AI.

After this Contract Gate is reviewed and merged, #100 runtime requires the next
explicit authorization.
