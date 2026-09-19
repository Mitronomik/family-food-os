# GATE1-A-RU — minimal Russian normative corpus

## Purpose

This package records the bounded production data slice used to unblock the
Planning Core gate. It does **not** import the full Russian normative corpus and
does not replace the later Data Readiness program.

Authorized base:

`main@9a76a97790b676f36c4c982af825721c3ef2c67e`

Issue:

`#64 — GATE1-A-RU — Russian normative corpus acceptance and minimal Gate1 delivery`

## Existing work reused

The project had already reviewed a later v22.13 checkpoint before this operation:

- 350 USSR82 recipes;
- 363 external ingredient/reference identities;
- full `v22-13-map-a` identity mapping;
- candidate/profile/process curation packages.

The workbook itself was intentionally not committed, but its accepted mapping
decisions remain repository evidence.

The user supplied v22.5 checkpoint available to this operation is older:

`russian_normative_recipes_v22_5_checkpoint.zip`

SHA-256:

`e720944aeb66e25fd666884576b10904d00f848fa655fae03f718a163108a1fe`

It is used only for the exact selected source rows and reference profiles.
It is not imported wholesale and does not supersede v22.13 mapping decisions.

## Selected source snapshot

`data/seed/gate1_ru_corpus/source-snapshot.json`

is a bounded immutable projection of the eight selected recipe variants. It
contains the selected source rows, exact published ingredient inputs and curated
technology steps.

The authoritative hash is stored in `package.json`; the seed recomputes it
before any database write and fails closed on mismatch.

## Selected recipes

Breakfast:

1. `USSR82-467` — Омлет натуральный
2. `USSR82-492` — Сырники из творога
3. `USSR82-1081` — Блины

Main:

4. `USSR82-208` — Рассольник ленинградский
5. `USSR82-263` — Суп молочный с картофельными клёцками
6. `USSR82-462` — Яичница глазунья с жареным картофелем
7. `USSR82-697` — Курица отварная, selected III-column main-product variant
8. `USSR82-720` — Котлета по-киевски, main product without garnish

Capacity under `max_recipe_repetitions=3`:

- 3 breakfast recipes → 9 breakfast uses;
- 5 main recipes → 15 lunch/dinner uses.

That is sufficient for the largest current Gate1 fixture shape:
7 breakfasts + 7 lunches + 7 dinners.

## New FoodIngredient/profile scope

Only ten v22.13 `NEW_FOOD_CANDIDATE` / `FORM_SPLIT_CANDIDATE` identities used
by the selected recipes are published:

- `MILK_PASTEURIZED_3_2`
- `MARGARINE_MILK`
- `COTTAGE_CHEESE_9`
- `SOUR_CREAM_30`
- `YEAST_COMPRESSED`
- `RICE_GROATS_POLISHED`
- `CUCUMBER_PICKLED_SALTED`
- `COOKING_FAT`
- `CHICKEN_CATEGORY_I`
- `BREAD_WHEAT_HIGH_GRADE`

Nine already accepted v22.13 exact/alias mappings are reused; no new name matching
is performed at runtime.

## Nutrition authority boundary

The ten new profiles retain the user-supplied checkpoint's explicit source
references, exactness tier, source-quality label and checkpoint SHA.

They are published with source type:

`USER_SUPPLIED_REFERENCE_TRANSCRIPTION`

This operation therefore **does not claim** that these ten profiles have already
been source-upgraded to the 2024 FIC Nutrition and Biotechnology composition
edition. That broader source upgrade belongs to Data Readiness and can later
append immutable profiles without changing these RecipeVersions.

The loader creates:

- FoodNutritionProfile;
- sealed sparse NutrientVector;
- atomic FoodCompositionVersion with `GATE1-A-RU` provenance.

Source-reported numeric zero values are retained in Nutrition v1 where required
by the existing profile contract but are held out of the sparse vector as
`SOURCE_REPORTED_ZERO_HELD`; unknown is never synthesized as zero.

## Mass / transformation boundary

All 40 selected RecipeIngredient inputs are source-backed gram quantities.
No cup/piece/medium-size conversion is used.

Recipe Nutrition is calculated from exact input grams and current canonical
profiles. The external checkpoint explicitly did not apply general retention
coefficients. Therefore:

- raw/input Nutrition is authoritative for the bounded calculation path;
- source output mass is retained as evidence;
- no cooking retention coefficient is invented;
- no raw/cooked profile is silently substituted;
- later transformation/retention enrichment remains an explicit data-quality
  improvement, not hidden Gate1 arithmetic.

## Publication path

`backend/app/seed/gate1_ru_corpus.py`

uses one `B2B2UnitOfWork` transaction to publish:

1. the ten new food forms/profiles/vectors/compositions;
2. eight immutable SOURCE_VERIFIED RecipeVersions;
3. forty `APPROVED_NO_CONVERSION / DIRECT_RECIPE_MASS` row assessments.

The operation is idempotent and fails closed on conflicting existing truth.

No schema or migration change is introduced.

## Gate1 proof

`backend/app/tests/test_planner_gate1_fixtures.py` now exercises the repository
fixture after the accepted current seed chain plus this RU data upgrade.

The third fixture household gives its dinner-only member a hard exclusion for
`CHICKEN_CATEGORY_I`; both chicken recipes must be rejected for that participant
while the complete week remains feasible.

Required proof:

- 38 verified recipes total: historical 30 + selected 8 RU;
- 80+ FoodIngredient remains satisfied;
- authoritative Planner composition;
- deterministic repeated trace;
- persisted complete seven-day plan;
- individualized positive Decimal Servings;
- explicit hard-exclusion evidence;
- old incomplete FNS candidates remain fail-closed.

## Verification

Final command receipts are recorded in the PR after execution on the final head.

Required focused checks:

```bash
PYTHONPATH=backend python -m pytest -q   backend/app/tests/test_gate1_ru_corpus.py   backend/app/tests/test_planner_gate1_fixtures.py
```

Required affected/full checks follow the repository verification policy because
this operation changes production catalogue/Nutrition data.

## Stop condition

After the GATE1-A-RU PR is reviewed and merged:

- stop;
- perform separate Gate1-CLOSE review;
- do not start PR9 automatically.
