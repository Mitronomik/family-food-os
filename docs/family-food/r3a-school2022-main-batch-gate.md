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
| `ru-school2022:recipe:54-10р` | Горбуша, тушенная в томате с овощами | 70 g | 134.3 |
| `ru-school2022:recipe:54-11р` | Минтай, тушенный в томате с овощами | 70 g | 103 |
| `ru-school2022:recipe:54-4м` | Котлета из говядины | 75 g | 221.3 |
| `ru-school2022:recipe:54-6м` | Биточек из говядины | 75 g | 221.3 |
| `ru-school2022:recipe:54-7м` | Шницель из говядины | 75 g | 221.3 |
| `ru-school2022:recipe:54-8м` | Тефтели из говядины паровые | 60 g | 117.1 |
| `ru-school2022:recipe:54-11м` | Плов из отварной говядины | 200 g | 348.3 |

All ten are classified `meal_type_code=main`. No Planner role mapping change is
authorized.

## 3. Source authority

Reuse accepted School2022 evidence:

- source PDF SHA-256: `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`;
- durable archive: `private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`;
- archive SHA-256: `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- latest independent archive + embedded-PDF verification: 2026-10-03.

The official public PDF was rechecked on 2026-10-03 for selected card text.
Public web is corroboration only; runtime must consume the hash-pinned repository
contract and accepted durable source evidence.

## 4. FoodIngredient identity decisions

Create identity-only exactly:

- `COD_FILLET_RAW` — Треска, филе сырое;
- `PARSLEY_ROOT_RAW` — Петрушка, корень свежий;
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

## 5. Process binding

The batch has a separate reviewed receipt:

`data/curation/r3a-school2022-main-batch/process-binding-review.json`.

Rules:

- exact RecipeIngredient **total** quantity from the selected card is authoritative;
- no per-step gram split may be invented;
- a per-step split may remain explicitly UNKNOWN;
- when a card has exactly one quantified cooking fat and its technology has an
  otherwise unnamed fat-consuming operation (for example sautéing or tray
  oiling), that same-card fat may be bound to those operations without inventing
  the internal gram split;
- if multiple quantified cooking fats exist and the technology does not place
  them unambiguously, the card is rejected from the batch.

This rule admits `54-8м`, `54-10р` and `54-11р` with explicit reviewed
same-card bindings. It rejects `54-9р` and `54-18м`.

## 6. Household applicability

Each of the ten cards is reviewed separately as `HOUSEHOLD_APPLICABLE`.

Consumer steps preserve the source-defining preparation. Institutional thawing,
holding, serving-temperature and equipment wording is quarantined where it does
not define ingredient/output truth.

The gate does not grant blanket School2022 household authority.

## 7. Nutrition authority

For every selected RecipeVersion:

- authority kind = `PREPARED_OUTPUT_V1`;
- calculation version = `RECIPE_PREPARED_OUTPUT_NUTRITION_V1`;
- exact same-card `ENERGY_KCAL` is AVAILABLE;
- the other 53 frozen nutrient codes remain UNKNOWN;
- source ingredient macros/micros remain reference evidence only;
- no raw-to-cooked Composition inference;
- no source scaling.

## 8. Fresh / replay / conflict semantics — option B

The user explicitly selected **option B** for the enlarged batch.

### Publication phase

Publication is per recipe:

`inactive RecipeVersion + prepared authority -> one caller-owned UoW -> commit`.

Therefore a failure may leave an exact **inactive subset** of the 10 recipes.
That is allowed and is not treated as successful batch completion.

Rerun behavior:

- exact persisted recipe publication -> zero-write replay;
- missing recipe publication -> publish that recipe atomically;
- conflicting/partial per-recipe state -> fail closed;
- publication phase never activates a recipe.

### Batch activation phase

Activation is a separate explicit command in the **same future runtime PR**.

Before any activation write, all 10 RecipeVersions + prepared authorities must
reconcile exactly.

State semantics:

- all 10 inactive -> activate all 10 in **one caller-owned batch UoW** and commit once;
- all 10 active -> zero-write replay;
- mixed active/inactive -> fail closed with zero writes;
- any activation failure -> rollback the whole activation UoW, leaving the exact
  inactive publication set intact.

This avoids a giant 10-recipe publication transaction, remains resumable after
publication failures, and preserves deliberate deactivation because a later mixed
state is never silently reactivated.

## 9. Preservation matrix

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

## 10. Explicit exclusions

- `54-5м` — ingredient table sunflower oil vs process butter.
- `54-12м` — ingredient table sunflower oil vs process butter.
- `54-15м` — process water and bay leaf are not quantified.
- `54-9р` — sunflower oil + butter are both quantified, but sunflower-oil
  placement is unresolved.
- `54-18м` — sunflower oil + butter are both quantified, but sunflower-oil
  placement is unresolved.
- special-diet cards are not part of R3-A.

`54-6м` and `54-7м` are now intentionally included as clean source-consistent
replacements. The lower marginal variety is accepted to keep one safe 10-recipe
batch rather than creating extra micro-PRs.

## 11. Future runtime acceptance

A later runtime PR must prove at least:

1. exactly three new identity-only foods and no Nutrition/Composition for them;
2. exactly ten immutable SOURCE_VERIFIED MAIN RecipeVersions;
3. exact source quantities/output per frozen specs;
4. exact same-card ENERGY_KCAL per RecipeVersion;
5. all other 53 frozen nutrient codes UNKNOWN;
6. fresh RecipeVersion + authority atomicity for every item;
7. publication failure may leave only an exact inactive subset; rerun converges missing publications without rewriting exact rows;
8. full-batch activation is blocked until all 10 exact publications exist; activation uses one batch-level UoW and rolls back atomically on failure;
9. exact replay is zero-write;
10. deliberate deactivation stays deactivated; mixed active/inactive activation state fails closed;
11. guarded batch activation admits all accepted recipes only after full preflight;
12. ordinary Planner generation remains deterministic;
13. exclusions remove affected candidates without weakening hard constraints;
14. migration head remains 0042;
15. `AI_ENABLED=false`.

## 12. Verification tier

Docs/data/source-evidence only:

- all JSON parse;
- selected count = 10;
- source IDs unique and not already production-published;
- exact quantities/output/kcal cross-check;
- identity mapping/reuse audit;
- process-binding audit for all ten selected cards;
- option-B publication/recovery + batch-activation semantics audit;
- household-applicability audit;
- source archive/PDF receipt consistency;
- Docs verification;
- DC1 corpus verification;
- scope/whitespace.

No runtime/backend regression is required for this gate.

## 13. Non-goals

No runtime publication, schema change, migration 0043, Planner redesign, new
Nutrition authority, ingredient Nutrition/Composition, DC4, Gate1-CLOSE, PR9,
Shopping, Prep, Retail, API/UI, Auth/PostgreSQL or AI.

## 14. Stop rule

After this gate is review-ready, stop for independent review.

Runtime implementation starts only after review and merge of this Contract Gate.


## 15. 2026-10-03 independent source re-verification

The durable Library archive was independently materialized again:

- file id: `libfile_26d95a7a50108191944b97db85a5c008`;
- size: 206692075 bytes;
- SHA-256: `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`.

The embedded School2022 PDF was independently extracted/re-read:

- size: 4102547 bytes;
- SHA-256: `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.

Both match the pinned authority receipts.
