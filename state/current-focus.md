# Current focus

Updated: 2026-09-30.

## Accepted state

PR115 / R1-E evidence-scoped corpus blocker map is merged into `main` at:

`becc00f0e94c927598f930140c385f84f80aa21d`.

R1-E established:

- 547/547 retained recipe identities remain visible in closure;
- known blockers are separated from unproven later gates;
- all five selected cooked USSR82 candidates retain the known downstream
  `CONSUMED_NUTRITION_AUTHORITY` gap;
- local next blockers remain explicit;
- first mixed cooked-authority pilot is:
  - USSR82-453 — breakfast;
  - boiled-chicken target originally seeded by USSR82-697 — main;
- the pilot is not by itself sufficient for a complete seven-day Planner week.

## Current bounded operation

**R1-F — COOKED-NUTRITION AUTHORITY IMPLEMENTATION CONTRACT GATE.**

Issue:

`#116`.

Branch:

`docs/r1f-cooked-nutrition-authority-gate`.

Repository `AGENTS.md` requires this docs-only gate to be reviewed and merged
before runtime/schema/data publication because R1-F changes an authoritative
immutable Nutrition publication path.

## Contract decision

Current runtime cannot truthfully represent source-backed prepared-dish Nutrition:

- NutrientVector belongs to FoodNutritionProfile;
- Recipe Nutrition authority is currently only LEGACY_V1 or COMPOSITION_V2;
- RECIPE_COMPOSITION_NUTRITION_V1 is INPUT-state only.

R1-F therefore selects a narrow new mode:

`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

It requires RecipeVersion-level immutable persistence and migration
`0042_recipe_prepared_output_nutrition`.

The pilot publishes only explicitly reviewed source nutrients. ENERGY_KCAL is
mandatory; unreviewed frozen nutrients remain UNKNOWN.

## Breakfast evidence

USSR82-453 source allows several boiling states, so generic "boiled egg" is not
sufficiently exact.

R1-F selects the hard-boiled branch only.

MR 2.4.0162-19 Appendix 5 card 4.1 supplies exact matching prepared-output truth:

- chicken egg 40 g;
- hard-boiled 8–10 minutes;
- output 40 g / one egg;
- source-published energy 63 kcal.

The 453 RecipeVersion retains its ingredient identity for exclusions/Shopping and
uses prepared-output Nutrition only after exact hard-boiled applicability review.

## Main evidence

Historical USSR82-697 v1 remains immutable/inactive.

The 1986 row `697/824, 50/50, 144 kcal` is explicitly rejected because 824 is
red sauce and the row is not the historical 75 g chicken-only output.

A separate 1988 source, recipe 303 Variant III `Курица отварная без гарнира`, publishes:

- chicken 155 g gross / 107 g net;
- finished output 75 g;
- energy 167.7 kcal;
- protein 12.6 g;
- fat 12.8 g;
- carbohydrate 0.5 g.

The already accepted source mapping identifies the 155/107 path with category-II
chicken.

R1-F preserves the historical source-coded Recipe
`USSR82_697_BOILED_CHICKEN` unchanged/inactive and publishes a separate
source-neutral production Recipe:

- `BOILED_CHICKEN_MAIN_PRODUCT`;
- Russian name `Курица отварная без гарнира`;
- source `DIETETIC_RECIPES_1988 / 303_VARIANT_III`.

No source-specific USSR82 code becomes the identity of a foreign-source version.

## Source artifact boundary

Public source locators are research evidence only.

Source receipts are now closed in the gate itself:

- MR 2.4.0162-19 uses the existing accepted repository bundle + exact card hash;
- 1988 recipe 303 uses an exact source-page OCR capture, mirrored byte-identically in durable private Library storage with pinned size/SHA;
- both have explicit reviewed rights scope.

Runtime must verify these exact receipts; it must not discover/choose new source
authority.

## Next step

Review and merge the R1-F contract gate.

Only after merge may the runtime PR implement:

1. migration 0042;
2. PREPARED_OUTPUT_V1 domain/persistence/publication;
3. exact source-neutral Recipe publications using the already pinned receipts;
4. exact-energy projection verification;
5. explicit activation;
6. ordinary Planner admission proof.

Then expand the accepted seam to 467 / 492 / 1081 and additional MAIN capacity.

## Hard boundaries

Do not:

- start runtime before this gate is merged;
- use raw input kcal as cooked output;
- infer 100% retention;
- use the incompatible 697/824 50/50 value for 75 g chicken;
- mutate historical USSR82-697 v1;
- silently prefer prepared authority over Composition authority;
- convert missing nutrients to zero;
- bulk-activate recipes;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI;
- start R2/R3 before successful R1-C.
