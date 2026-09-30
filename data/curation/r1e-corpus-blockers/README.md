# R1-E Corpus Blocker Map

Accepted base: `48707e1e84eff260726609c4508f05407e9f9448` (merged PR #113).

Status: evidence/curation only. This package does not activate or publish recipes.

## Purpose

Turn the retained 547-recipe universe into one deterministic closure map without
pretending that source presence equals production readiness.

Files:

- `blocker-map.jsonl` — one row per retained recipe identity;
- `summary.json` — counts by source family and evidence scope;
- `selected-batch.json` — reviewed comparison and first cooked-authority pilot.

## Evidence scopes

Every row separates:

- `known_blockers` — recipe-level or accepted-family evidence proves the blocker;
- `unproven_later_gates` — a later review may be required, but current evidence
  does not justify recording it as per-recipe truth;
- `next_blocker` — the first currently proven action gate.

For selected R1 candidates the map also separates:

- `mode_independent_blockers` — prerequisites required regardless of the future
  consumed-Nutrition calculation mode;
- `mode_dependent_blockers` — requirements that depend on whether the accepted
  path is Composition-based transformation or source-backed prepared-output
  Nutrition.

## School2022 and RU-MR-2019

School2022 retained evidence proves strong aggregate material readiness, but it
does not establish household applicability or consumed-Nutrition authority for
every recipe identity individually.

Therefore each unpublished School2022 row stops at the proven
`HOUSEHOLD_APPLICABILITY` blocker. `CONSUMED_NUTRITION_AUTHORITY` is retained
only as an `unproven_later_gate`, not as known per-recipe truth.

RU-MR-2019 likewise stops first at household applicability under the current
retained interpretation.

## R1-B evidence is mechanically consumed

The four accepted R1-B blocked dispositions are read directly from:

`data/curation/r1b-reviewed-recipes/publication.json`

and mapped from their accepted reason codes. The builder fails closed if an
unknown R1-B blocker reason or candidate-set drift appears.

USSR82-697's accepted inactive activation disposition is also asserted directly
from the same publication package. Its later exact source-identity correction and
cooked-Nutrition gap remain tied to the accepted cross-corpus review.

## Batch comparison

R1-E compares four materially different continuations:

1. **BREAKFAST_CLUSTER_4** — 453 / 467 / 492 / 1081;
   strong shared cooked-Nutrition learning, but no MAIN capacity.
2. **MIXED_AUTHORITY_PILOT** — 453 + 697;
   one breakfast + one main and a concrete cooked-consumption authority decision
   framework.
3. **HISTORICAL_MAIN_BLOCKERS** — 364 + 208;
   MAIN diversity, but both first require unresolved food identity/form work.
4. **SCHOOL2022_PILOT_PATH**;
   promising future corpus, but recipe-level household/role ranking is not yet
   supported by retained evidence.

## Selected first pilot

Selected:

- USSR82-453 — Яйца вареные — breakfast;
- USSR82-697 — Курица отварная — main.

This is not claimed to be an algorithmic optimum. It is the reviewed bounded pilot
that best answers the next architecture/product question while improving both
Planner role families needed by R1-C.

### Mode-independent prerequisites

- USSR82-453: publish an immutable source-backed RecipeVersion when the publication
  operation is ready;
- USSR82-697: correct/close the exact source FoodIngredient identity/form mapping.

### Mode-dependent questions

- USSR82-453: exact input Composition is required if the accepted path is
  Composition-based; it may not be the Planner energy authority under an exact
  prepared-output Nutrition path.
- USSR82-697: consumed-Nutrition authority remains unresolved.

Activation is downstream of accepted consumed-Nutrition authority; it is not a
pre-authority local closure step.

## Follow-up

The next bounded operation should be a **cooked-Nutrition authority pilot plus
mode-independent local closure** for the mixed pair.

It should:

1. close the mode-independent source/identity/publication prerequisites;
2. evaluate the truthful consumed-Nutrition mode on the two concrete recipes;
3. implement only the minimum versioned authority seam actually required;
4. make activation conditional on exact positive consumption Nutrition;
5. report resulting breakfast/main Planner capacity.

After the authority mode is proven, expand immediately to
USSR82-467 / USSR82-492 / USSR82-1081 using the same accepted seam where applicable.

## Boundaries

This package does not:

- relabel SIDE/SALAD/OTHER as MAIN;
- infer household applicability;
- turn aggregate evidence into per-recipe truth;
- infer raw→cooked Nutrition;
- infer yield or nutrient retention;
- grant source-declared recipe Nutrition production authority;
- publish or activate any RecipeVersion;
- introduce a new Recipe Nutrition calculation version.
