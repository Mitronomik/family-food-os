# R1-E Corpus Blocker Map

Accepted base: `48707e1e84eff260726609c4508f05407e9f9448` (merged PR #113).

Status: evidence/curation only. This package does not activate or publish recipes.

## Purpose

Turn the retained 547-recipe universe into one deterministic closure map without
pretending that source presence equals production readiness.

Files:

- `blocker-map.jsonl` — one row per retained recipe identity;
- `summary.json` — counts by source family and blocker;
- `selected-batch.json` — first high-value Planner-capacity closure batch.

## Counts

Retained recipe identities:

- USSR82: 68
- School2022: 265
- RU-MR-2019: 214
- total: 547

The largest current `next_blocker` classes are:

- `HOUSEHOLD_APPLICABILITY`: 478
- `SOURCE_STRUCTURE_OR_VARIANT`: 59
- `FOOD_IDENTITY_OR_FORM`: 5
- `COMPOSITION_AUTHORITY`: 2
- `REQUIRED_QUANTITY_UNRESOLVED`: 2
- `ROLE_OR_MEAL_COMPOSITION`: 1

These are next-action counts, not claims that later blockers are absent.

## Evidence discipline

School2022 and RU-MR-2019 are deliberately classified conservatively.

For School2022, retained evidence proves strong aggregate material readiness but
does not support assigning household applicability or Nutrition readiness to every
card individually. Therefore the map records a household-applicability review as
the next step instead of inventing recipe-level facts.

For RU-MR-2019, the retained interpretation does not establish the ordinary
household path, so household applicability owns the next step.

USSR82 has recipe-level DC1 evidence and later R1 receipts, so more granular
blockers can be assigned there.

## Selected first capacity batch

The first closure batch is:

- USSR82-453 — Яйца вареные
- USSR82-467 — Омлет (натуральный)
- USSR82-492 — Сырники из творога
- USSR82-1081 — Блины

All four are accepted historical Planner-capacity breakfast candidates.

Local blockers:

- USSR82-453 / USSR82-1081 — exact V2 Composition authority;
- USSR82-467 / USSR82-492 — required quantity/process closure.

After those local blockers, all four still require a truthful consumed-Nutrition
authority for cooked/prepared output. No current evidence authorizes treating these
as no-thermal `RECIPE_COMPOSITION_NUTRITION_V1` recipes.

This is therefore a **capacity program**, not a bulk activation manifest.

## Why not the simple School2022 controls?

The retained butter/cheese/vegetable no-thermal cards are useful proof that the
existing V1 path can work when exact form authority exists. They do not by
themselves add meaningful BREAKFAST/MAIN Planner capacity.

## Why not USSR82-697 first?

USSR82-697 remains a valuable MAIN candidate, but it carries an additional exact
source-identity conflict before the same consumed-Nutrition problem. The four
breakfast candidates provide a cleaner first capacity cluster.

## Boundaries

This package does not:

- relabel SIDE/SALAD/OTHER as MAIN;
- infer household applicability;
- infer raw→cooked Nutrition;
- infer yield or nutrient retention;
- grant source-declared recipe Nutrition production authority;
- publish or activate any RecipeVersion;
- introduce a new Recipe Nutrition calculation version.

The next implementation PR should close the four local breakfast blockers first.
A new cooked/prepared consumed-Nutrition runtime/authority seam is opened only
against the exact evidence demonstrated by that batch.
