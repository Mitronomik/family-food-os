# R3-A — School2022 10-recipe DC3 batch Contract Gate

**Status:** pre-implementation docs/data/source-authority gate
**Decision date:** 2026-10-03
**Issue:** #143
**Accepted base:** `da6d1e05fd44ecc2733e1a6f472eae3e54b60604` (merged PR #142)

## Goal

Move DC3 from one-recipe/micro-batch proof work to a real reviewable publication
batch without weakening source, identity, Nutrition or transaction contracts.

Freeze exactly **10** future School2022 RecipeVersions under the already accepted
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1` seam.

Role split:

- 5 BREAKFAST;
- 5 MAIN.

No runtime publication happens in this PR.

## Selected batch

### BREAKFAST

| Source card | Future code | Output | Same-card kcal |
| --- | --- | ---: | ---: |
| 54-2о Омлет с зеленым горошком | `SCHOOL2022_54_2O_GREEN_PEA_OMELET` | 150 g | 153.5 |
| 54-3о Омлет с морковью | `SCHOOL2022_54_3O_CARROT_OMELET` | 150 g | 201 |
| 54-4о Омлет с сыром | `SCHOOL2022_54_4O_SEMI_HARD_CHEESE_OMELET` | 150 g | 316 |
| 54-2т Запеканка из творога с морковью | `SCHOOL2022_54_2T_COTTAGE_CHEESE_CARROT_CASSEROLE` | 150 g | 249.5 |
| 54-3т Суфле из моркови с творогом | `SCHOOL2022_54_3T_CARROT_COTTAGE_CHEESE_SOUFFLE` | 150 g | 200.9 |

### MAIN

| Source card | Future code | Output | Same-card kcal |
| --- | --- | ---: | ---: |
| 54-2р Котлета рыбная (горбуша) | `SCHOOL2022_54_2R_PINK_SALMON_CUTLET` | 100 g | 163.6 |
| 54-14р Котлета рыбная любительская (минтай) | `SCHOOL2022_54_14R_POLLOCK_AMATEUR_CUTLET` | 100 g | 112.2 |
| 54-1м Бефстроганов из отварной говядины | `SCHOOL2022_54_1M_BOILED_BEEF_STROGANOFF` | 80 g | 167.5 |
| 54-11м Плов из отварной говядины | `SCHOOL2022_54_11M_BOILED_BEEF_PILAF` | 200 g | 348.3 |
| 54-30м Кнели из говядины с рисом | `SCHOOL2022_54_30M_BEEF_RICE_QUENELLES` | 80 g | 184.6 |

Exact ingredient rows and source-backed steps are frozen in
`data/curation/r3a-school2022-10-recipe-batch/publication-specs.json`.

## Source authority

Reuse the accepted durable School2022 source receipt:

- archive:
  `private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`;
- archive SHA-256:
  `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- School2022 PDF:
  `corpus-work/packages/school2022/raw/source.pdf`;
- PDF SHA-256:
  `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.

The PDF is the retained source document for these cards. The public PDF is
corroboration/discovery only and cannot override retained bytes at runtime.

The source itself states standard ingredients including beef category 1, fish
fillet without skin, milk 2.5%, cottage cheese 5%, sour cream 15% and butter
72.5%; the exact FoodIngredient decisions below preserve those semantics.

## FoodIngredient identity contract

Create exactly two identity-only FoodIngredients:

- `CHEESE_SEMI_HARD_UNSPECIFIED` — Сыр полутвердый;
- `PARSLEY_ROOT_FRESH` — Петрушка, корень свежий.

No NutritionProfile or Composition authority is granted.

Important non-equivalences:

- semi-hard cheese is not collapsed into broader `CHEESE_UNSPECIFIED` and is
  not narrowed to cheddar/mozzarella;
- parsley root is not parsley leaf (`PARSLEY`) or dried parsley.

All other ingredients reuse existing canonical identities. Generic source
labels stay generic: source `морковь` maps to `CARROT`, not the narrower
`CARROT_RED_RAW`; generic wheat bread in fish cards maps to
`WHEAT_BREAD_PLAIN`.

## Household applicability

All ten selected dishes are ordinary non-clinical food. Their recipe-defining
operations are executable with household equipment:

- oven baking for omelets/casserole/fish cutlets;
- stovetop plus oven for pilaf;
- stovetop/saucepan for boiled-beef stroganoff;
- steaming for the selected beef-rice quenelle route;
- ordinary steaming for carrot-cottage soufflé.

Institutional defrosters, meat-shop tables, paraconvection wording and
serving-temperature rules are retained as provenance-only and do not become
consumer execution requirements.

Each of the ten named cards also has independent household corroboration for the
same dish/process family recorded in
`household-applicability-review.json`. Those external recipes establish only
ordinary household executability; they do not override School2022 ingredient
quantities, FoodIngredient identities, output or prepared ENERGY_KCAL.

For 54-30м, the future consumer route is the source-backed **steam 15–20 min**
route. The alternative poaching route mentions added water without an exact
recipe quantity, so that alternative is not published as the executable route.

## Nutrition authority

For every selected RecipeVersion:

- only `ENERGY_KCAL` is AVAILABLE under `PREPARED_OUTPUT_V1`;
- all other frozen nutrient codes are UNKNOWN;
- source macros/micros are QA/reference evidence only;
- no source scaling;
- no raw-to-cooked inference;
- no implicit retention/yield.

4/9/4 macro arithmetic was rechecked for all ten cards and is stored as QA only.
This arithmetic is not treated as proof of component consistency. The gate found
no obvious blocker in the bounded source/identity review, but runtime authority
remains limited to the exact reviewed prepared ENERGY_KCAL contract.

Where menu tables round differently, the exact selected recipe card remains the
authority:

- 54-11м: card 348.3 kcal; menu example 348.2 — menu is QA-only;
- 54-14р: card 112.2 kcal; menu example 112.3 — menu is QA-only.

## Known exclusions from this batch

This gate deliberately does **not** pull in nearby cards merely to increase
count:

- 54-4т — vanillin process requires hot water but exact required water quantity
  is not present in the ingredient table;
- 54-6т — same unquantified vanillin-water problem;
- 54-5м — table/process fat wording requires reconciliation before publication;
- specialized/celiac-labelled variants remain outside ordinary household scope.

Unknown stays unknown; unresolved stays blocked.

## Fresh / replay / conflict semantics

### Fresh

1. validate all frozen gate artifacts and retained source identity;
2. reconcile exactly the two identity-only FoodIngredients;
3. create all ten RecipeVersions inactive;
4. for each fresh RecipeVersion, publish prepared authority in the same
   caller-owned UoW;
5. verify exact positive ENERGY_KCAL projection before commit;
6. activate each candidate only through the existing guarded prepared boundary.

The future runtime may process the batch recipe-by-recipe, but a single
RecipeVersion and its prepared authority must never be partially committed.

### Replay

- exact FoodIngredient identity replay is zero-write;
- exact RecipeVersion + prepared authority replay is zero-write;
- deliberate deactivation remains deactivated;
- live web cannot replace retained source truth.

### Conflict / failure

Fail closed on:

- candidate-set drift;
- source archive/PDF hash mismatch;
- ingredient mapping, quantity, output or energy drift;
- narrower/broader FoodIngredient substitution;
- partial RecipeVersion/authority state;
- wrong prepared energy;
- any non-reviewed nutrient publication;
- injected RecipeVersion/value/authority failure;
- activation before exact authority is readable;
- a newly discovered schema/migration/new-authority requirement.

## Preservation matrix

| Existing truth | R3-A requirement |
| --- | --- |
| R2-F runtime and exact-MILK resilience | Preserve unchanged. |
| Planner v0.4 compatibility/scoring | No change. |
| `max_recipe_repetitions=3` | No change. |
| `PREPARED_OUTPUT_V1` | Reuse only. |
| Frozen nutrient registry | ENERGY_KCAL only; rest UNKNOWN. |
| Existing FoodIngredient semantics | Reuse exactly; no hidden narrowing. |
| Migration head 0042 | No 0043. |
| AI independence | `AI_ENABLED=false`. |
| Runtime source independence | No live-web dependency. |

## Future runtime acceptance

A later R3-A runtime PR must prove at least:

1. exactly two new identity-only foods and zero Nutrition/Composition for them;
2. exactly ten new immutable SOURCE_VERIFIED RecipeVersions;
3. exact 5 BREAKFAST / 5 MAIN classification split;
4. exact source ingredient quantities, output and selected source route per card;
5. exact same-card ENERGY_KCAL for all ten;
6. other frozen nutrients UNKNOWN;
7. source/package tamper fails closed;
8. fresh RecipeVersion + prepared authority atomicity per candidate;
9. injected version/value/authority failure leaves no partial selected recipe;
10. exact replay is zero-write;
11. deliberate deactivation remains deactivated;
12. guarded activation yields exact-energy eligible candidates;
13. existing R2-F exact-MILK week remains feasible;
14. ordinary Planner weeks can consume candidates from both new role groups;
15. no specialized/medical claim;
16. migration head remains 0042;
17. `AI_ENABLED=false`.

## Verification tier

This gate is docs/data/source-evidence only:

- parse all JSON;
- verify candidate count/uniqueness and 5/5 role split;
- verify two and only two new identity-only foods;
- verify all exact ingredient/source/output/energy records;
- verify macro QA arithmetic;
- verify known-blocker exclusions;
- verify archive/PDF lineage against accepted repository receipt;
- Docs verification;
- DC1 corpus verification;
- scope/whitespace.

No runtime/backend regression is required for this gate.

## Non-goals

No runtime publication, migration/schema change, Planner redesign, new Nutrition
authority, bulk School2022 import, specialized diet cards, unresolved-quantity
cards, DC4, Gate1-CLOSE, PR9, Shopping, Prep/PDF, Retail, API/UI,
Auth/PostgreSQL or AI.

## Stop rule

After the gate is review-ready, stop for independent review.

Runtime starts only after this gate is reviewed and merged.
