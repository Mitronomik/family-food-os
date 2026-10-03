# R3-A — School2022 ten-recipe MAIN batch Contract Gate

**Status:** docs/data implementation contract gate  
**Decision date:** 2026-10-03  
**Issue:** #144  
**Accepted base:** `da6d1e05fd44ecc2733e1a6f472eae3e54b60604` (merged PR #142)  
**Runtime publication authorized before this gate merges:** no

## 1. Goal

Move DC3 from micro-publication to the canonical batch shape by freezing one
reviewable School2022 batch of **10 MAIN RecipeVersions**.

The batch reuses one source family, one rights route and the already accepted
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1` authority seam.

## 2. Selected batch

| Source card | Recipe | Output | Exact same-card kcal |
| --- | --- | ---: | ---: |
| `ru-school2022:recipe:54-1р` | Котлета рыбная из трески | 100 g | 112.6 |
| `ru-school2022:recipe:54-2р` | Котлета рыбная из горбуши | 100 g | 163.6 |
| `ru-school2022:recipe:54-3р` | Котлета рыбная из минтая | 100 g | 114.2 |
| `ru-school2022:recipe:54-9р` | Минтай, запечённый в сметанном соусе | 80 g | 236.6 |
| `ru-school2022:recipe:54-10р` | Горбуша, тушенная в томате с овощами | 70 g | 134.3 |
| `ru-school2022:recipe:54-11р` | Минтай, тушенный в томате с овощами | 70 g | 103 |
| `ru-school2022:recipe:54-4м` | Котлета из говядины | 75 g | 221.3 |
| `ru-school2022:recipe:54-8м` | Тефтели из говядины паровые | 60 g | 117.1 |
| `ru-school2022:recipe:54-11м` | Плов из отварной говядины | 200 g | 348.3 |
| `ru-school2022:recipe:54-18м` | Печень говяжья по-строгановски | 80 g | 189.2 |

All ten are classified `meal_type_code=main`. No Planner role mapping change is
authorized.

## 3. Source authority

Reuse accepted School2022 evidence:

- source PDF SHA-256: `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`;
- durable archive: `private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`;
- archive SHA-256: `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- latest accepted independent archive verification: 2026-10-01.

The official public PDF was rechecked on 2026-10-03 for selected card text.
Public web is corroboration only; runtime must consume the hash-pinned repository
contract and accepted durable source evidence.

## 4. FoodIngredient identity decisions

Create identity-only exactly:

- `COD_FILLET_RAW` — Треска, филе сырое;
- `CHEESE_SEMI_HARD_UNSPECIFIED` — Сыр полутвердый, вид не уточнён;
- `PARSLEY_ROOT_RAW` — Петрушка, корень свежий;
- `BEEF_LIVER_RAW` — Печень говяжья, сырая;
- `WHEAT_BREAD_STALE_UNSPECIFIED_GRADE` — Хлеб пшеничный черствый, сорт муки не уточнён.

No NutritionProfile or Composition authority is granted.

Reuse accepted canonical identities for all remaining source rows, including
species-specific pink-salmon/pollock fillets, beef category I, rice groats,
carrot, onion, milk 2.5%, sour cream 15%, butter, sunflower oil, flour,
breadcrumbs, egg, sugar, tomato puree, iodized salt and water.

Important form rules:

- generic fish-cutlet `хлеб пшеничный` → `WHEAT_BREAD_PLAIN`;
- process-qualified `черствый пшеничный хлеб` →
  `WHEAT_BREAD_STALE_UNSPECIFIED_GRADE`;
- do not narrow stale bread to high-grade flour when the selected card does not
  establish grade;
- semi-hard cheese remains generic semi-hard cheese, not a named variety;
- beef liver is not generic beef.

## 5. Household applicability

Each of the ten cards is reviewed separately as `HOUSEHOLD_APPLICABLE`.

Consumer steps preserve the source-defining preparation. Institutional thawing,
holding, serving-temperature and equipment wording is quarantined where it does
not define ingredient/output truth.

The gate does not grant blanket School2022 household authority.

## 6. Nutrition authority

For every selected RecipeVersion:

- authority kind = `PREPARED_OUTPUT_V1`;
- calculation version = `RECIPE_PREPARED_OUTPUT_NUTRITION_V1`;
- exact same-card `ENERGY_KCAL` is AVAILABLE;
- the other 53 frozen nutrient codes remain UNKNOWN;
- source ingredient macros/micros remain reference evidence only;
- no raw-to-cooked Composition inference;
- no source scaling.

## 7. Fresh / replay / conflict semantics

Future runtime must publish each fresh RecipeVersion and its prepared authority in
one caller-owned UoW, verify exact positive ENERGY_KCAL in-scope, commit, then
activate only through the existing guarded activation boundary.

Replay:

- exact identities are zero-write;
- exact RecipeVersion + prepared authority replay is zero-write;
- deliberate deactivation remains deactivated.

Fail closed on:

- contract/source hash mismatch;
- source card/output/energy/ingredient mismatch;
- FoodIngredient identity narrowing;
- partial RecipeVersion/authority state;
- wrong prepared kcal;
- any non-reviewed nutrient publication;
- activation before exact authority is readable;
- any discovered schema/migration/new-authority requirement.

## 8. Preservation matrix

| Existing truth | R3-A requirement |
| --- | --- |
| PR #142 R2-F runtime | unchanged |
| Planner v0.4 mapping/scoring/repetition | unchanged |
| `max_recipe_repetitions=3` | unchanged |
| migration head 0042 | unchanged; no 0043 |
| `PREPARED_OUTPUT_V1` | reused |
| frozen 54-code nutrient set | ENERGY only; 53 UNKNOWN |
| ingredient Nutrition/Composition | no new authority |
| live web | never runtime authority |
| `AI_ENABLED=false` | required |

## 9. Explicit exclusions

- `54-5м` is rejected from R3-A: table = sunflower oil; process = butter.
- `54-12м` is rejected from R3-A: table = sunflower oil; process = butter.
- `54-15м` is deferred because process uses water and bay leaf without
  quantified ingredient-table rows.
- `54-6м / 54-7м` are deferred for low marginal variety; `54-4м` is the
  clean representative of the near-identical beef cutlet family.
- special-diet cards are not part of R3-A.

No conflict is resolved by silently choosing one source branch.

## 10. Future runtime acceptance

A later runtime PR must prove at least:

1. exactly five new identity-only foods and no Nutrition/Composition for them;
2. exactly ten immutable SOURCE_VERIFIED MAIN RecipeVersions;
3. exact source quantities/output per frozen specs;
4. exact same-card ENERGY_KCAL per RecipeVersion;
5. all other 53 frozen nutrient codes UNKNOWN;
6. fresh RecipeVersion + authority atomicity for every item;
7. batch failure cannot leave partial accepted publication;
8. exact replay is zero-write;
9. deliberate deactivation stays deactivated;
10. guarded activation admits all accepted recipes;
11. ordinary Planner generation remains deterministic;
12. exclusions remove affected candidates without weakening hard constraints;
13. migration head remains 0042;
14. `AI_ENABLED=false`.

## 11. Verification tier

Docs/data/source-evidence only:

- all JSON parse;
- selected count = 10;
- source IDs unique and not already production-published;
- exact quantities/output/kcal cross-check;
- identity mapping/reuse audit;
- household-applicability audit;
- source archive/PDF receipt consistency;
- Docs verification;
- DC1 corpus verification;
- scope/whitespace.

No runtime/backend regression is required for this gate.

## 12. Non-goals

No runtime publication, schema change, migration 0043, Planner redesign, new
Nutrition authority, ingredient Nutrition/Composition, DC4, Gate1-CLOSE, PR9,
Shopping, Prep, Retail, API/UI, Auth/PostgreSQL or AI.

## 13. Stop rule

After this gate is review-ready, stop for independent review.

Runtime implementation starts only after review and merge of this Contract Gate.
