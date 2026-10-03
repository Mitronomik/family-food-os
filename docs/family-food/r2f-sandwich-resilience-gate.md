# R2-F — Sandwich resilience-closure Contract Gate

**Status:** docs/data/source-authority implementation contract gate  
**Decision date:** 2026-10-03  
**Issue:** #139  
**Accepted base:** `561c13aad6ce978de399dfd807071232af06b71c` (merged PR #138)  
**Runtime publication authorized before this gate merges:** no

## 1. Goal

Close the remaining exact-`MILK_2_5` BREAKFAST resilience gap **as one meaningful
batch**, not as another single-recipe research step.

The future runtime batch contains exactly two `sandwich` RecipeVersions:

- `SAD28_SANDWICH_BUTTER_25_5` — Бутерброд со сливочным маслом;
- `SAD28_SANDWICH_CHEESE_20_10` — Бутерброд с сыром.

This batch is valuable beyond the immediate gap because the accepted Planner v0
compatibility already permits `sandwich` for BREAKFAST, LUNCH and SNACK.

No Planner algorithm, compatibility mapping, repetition limit, schema or Nutrition
authority is changed here.

## 2. FACT — accepted production state after PR #138

Current exact-energy production truth:

- active `breakfast` classification: 7 RecipeVersions;
- active MAIN classification: 5 RecipeVersions;
- `max_recipe_repetitions=3`;
- hard exact `MILK_2_5` exclusion leaves:
  - `HARD_BOILED_EGG`;
  - `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`;
- unaffected capacity = 2 × 3 = 6/week;
- a seven-BREAKFAST week therefore remains bounded-infeasible.

This is a corpus/coverage gap, not a Planner algorithm defect.

## 3. FACT — source discovery and fail-closed filtering

A broader sandwich search was performed because a `sandwich` candidate has higher
role value than another breakfast-only candidate.

### Rejected source family

An official GBDOU №118 technological-card source was investigated first.

Its sandwich cards were **not** accepted for prepared-output authority because the
published kcal values disagree materially with the source's own declared
macronutrients/component evidence.

**DECISION:** `REJECT_PREPARED_OUTPUT_AUTHORITY_INTERNAL_ENERGY_CONFLICT`.

No runtime or retained production authority may be built from those rejected
values by silently choosing one side of the conflict.

### Selected source family

The selected public source is an institution-published technological-card PDF
from МАДОУ «Детский сад комбинированного вида № 28» д. Лупполово,
Всеволожский район, Ленинградская область.

Publisher site:

`https://sad28.vsevobr.ru/`

Public source locator:

`https://sad28.vsevobr.ru/images/22-23/%D0%BF%D0%B8%D1%82%D0%B0%D0%BD%D0%B8%D0%B5/%D0%A2%D0%B5%D1%85%D0%BD%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B5-%D0%BA%D0%B0%D1%80%D1%82%D1%8B-22-23%20%281%29.pdf`

The cards cite the upstream collection:

`Сборник методических рекомендаций по организации питания детей и подростков
в учреждениях образования Санкт-Петербурга. СПб.: Речь, 2008, Куткина М.Н.`

Only a bounded reviewed structured derivative is committed. The project does not
copy the source PDF layout/photos/logos and does not require live web access at
runtime.

## 4. DECISION — bounded source-authority policy

Institution-published technological cards are not automatically Tier-A recipe
authority under DATA-CORPUS-V1.

R2-F creates the bounded reviewed policy:

`BOUNDED_INSTITUTION_PUBLISHED_TECH_CARD_REVIEW_V1`

It authorizes **only these two exact reviewed cards** to feed the existing
`PREPARED_OUTPUT_V1` publication seam.

It does **not** authorize the whole SAD28 website/PDF, the upstream collection,
future same-publisher cards without review, or bulk source import.

Runtime source truth is the reviewed structured derivative:

`data/curation/r2f-sandwich-resilience/source-cards.json`

Canonical reviewed-derivative SHA-256:

`575efc619c9aaf7b2933218985ee5b73a91a4dda3e8c79ffdd55745e6033b189`

The hash is computed over UTF-8 canonical JSON with sorted keys and compact
separators, excluding the self-referential `reviewed_derivative_sha256` field.

Original public URL, publisher identity and retrieval date remain provenance.

## 5. Selected cards

### 5.1 Бутерброд со сливочным маслом

Source record: `sad28-luppolovo:techcard:butter-sandwich:25-5`.

Reviewed card SHA-256: `facf8c892a76e4ea9283ecc4e9136ed6ea1769674bc643e11aa9c1c26d428ddc`.

Exact facts:

- `Хлеб пшеничный` — 25 g net;
- `Масло сливочное (Б)` — 5 g net;
- source output `25/5`;
- total serving mass = 30 g from the exact two component outputs;
- source-published `ENERGY_KCAL = 66.3`;
- source-declared P/F/C = 2.11 / 0.98 / 12.26 g.

The ordinary 4/9/4 macro cross-check equals 66.30 kcal exactly. This is **QA
corroboration only**; same-card 66.3 remains the prepared-output authority.

### 5.2 Бутерброд с сыром

Source record: `sad28-luppolovo:techcard:cheese-sandwich:20-10`.

Reviewed card SHA-256: `2eb846cdb80737c0b4f65202beda1e352f3610c6bb6634b832901615ca3a8f97`.

Exact facts:

- `Хлеб пшеничный` — 20 g net;
- `Сыр` — 11 g gross / 10 g net;
- source output `20/10`;
- total serving mass = 30 g;
- source-published `ENERGY_KCAL = 83`;
- source-declared P/F/C = 3.9 / 3.15 / 9.7 g.

The ordinary 4/9/4 cross-check equals 82.75 kcal; the 0.25 kcal difference is
rounding-level corroboration and does not replace same-card 83 kcal authority.

### 5.3 Deferred third card

The same source contains `Бутерброд с повидлом (20/20)`.

Its published 97.2 kcal diverges more materially from the simple source-macro
cross-check (~101.92 kcal).

R2-F does not need that card to close the product gap and there is no canonical
project tolerance allowing us to invent a reconciliation rule.

**DECISION:** `DEFER_ENERGY_QA_RECONCILIATION_NOT_NEEDED_FOR_CLOSURE`.

## 6. DECISION — FoodIngredient identities

Create exactly three identity-only FoodIngredients:

- `WHEAT_BREAD_PLAIN` — Хлеб пшеничный;
- `BUTTER_CREAM_UNSPECIFIED` — Масло сливочное;
- `CHEESE_UNSPECIFIED` — Сыр.

Explicit non-equivalences:

- `WHEAT_BREAD_PLAIN != BREAD_WHOLE_WHEAT`;
- `WHEAT_BREAD_PLAIN != WHEAT_BREAD_HIGH_GRADE_STALE`;
- `BUTTER_CREAM_UNSPECIFIED != BUTTER_PEASANT_72_5_UNSALTED`;
- `BUTTER_CREAM_UNSPECIFIED != BUTTER_UNSALTED`;
- `CHEESE_UNSPECIFIED != CHEESE_CHEDDAR` and no automatic substitution to any
  specific cheese identity.

No NutritionProfile or Composition authority is published for the three new
identities. Prepared sandwich Nutrition remains independent same-card
prepared-output truth.

## 7. DECISION — household applicability

Both selected recipes are `HOUSEHOLD_APPLICABLE`.

Their defining processes are ordinary household sandwich assembly and require no
institutional equipment or clinical context.

Institutional serving-temperature and realization/shelf-life instructions remain
source provenance only; they are not promoted as household execution rules.

## 8. Recipe classification and Planner compatibility

Both future RecipeVersions use:

`meal_type_code = sandwich`.

No compatibility mapping changes are authorized.

Existing Planner v0 mapping already permits:

- BREAKFAST → `breakfast`, `sandwich`;
- LUNCH → `main`, `sandwich`;
- SNACK → `sandwich`.

Therefore this batch expands role coverage without changing Planner code.

## 9. Nutrition authority

Reuse `PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

For each selected RecipeVersion:

- `ENERGY_KCAL` is the only AVAILABLE frozen nutrient;
- all other 53 frozen nutrient codes remain UNKNOWN;
- no ingredient-composition calculation is required;
- no source scaling is authorized;
- macro values are QA/source evidence only.

| Recipe | Output | ENERGY_KCAL |
|---|---:|---:|
| Butter sandwich | 30 g | 66.3 |
| Cheese sandwich | 30 g | 83 |

## 10. Preservation matrix

| Existing truth | Required preservation |
|---|---|
| PR #138 R2-E runtime | Byte/semantic behavior unchanged. |
| Existing active exact-energy corpus | No deactivation/relabeling. |
| Planner v0.4 mapping | Unchanged. |
| `max_recipe_repetitions=3` | Unchanged. |
| `PREPARED_OUTPUT_V1` | Reused; no new authority kind. |
| Frozen 54-code nutrient set | ENERGY_KCAL only for these cards; other 53 UNKNOWN. |
| Existing FoodIngredient identities | No narrowing/broadening to absorb the three new identities. |
| Migration chain through 0042 | No 0043. |
| Medical/wellness boundary | Unchanged. |
| Runtime web independence | Runtime pins reviewed derivative; no live web dependency. |

## 11. Future runtime fresh/replay/conflict semantics

After this gate merges, one bounded runtime PR may publish exactly the two
selected recipes.

### Fresh

1. reconcile the three identity-only FoodIngredients;
2. create both Recipes inactive;
3. create immutable SOURCE_VERIFIED RecipeVersions;
4. publish each prepared-output authority in the caller-owned UoW;
5. verify exact positive ENERGY_KCAL projection before commit;
6. activate each only through the existing guarded prepared activation boundary.

### Replay

- exact identity replay is zero-write;
- exact RecipeVersion + prepared authority replay is zero-write;
- deliberately deactivated Recipes remain deactivated;
- replay cannot replace reviewed bytes with live-web data.

### Conflict / failure

Fail closed on:

- changed reviewed-derivative/card hash;
- source output/component quantity mismatch;
- narrower FoodIngredient substitution;
- same-code FoodIngredient identity conflict;
- Recipe without matching prepared authority or inverse;
- prepared value outside reviewed ENERGY_KCAL;
- any non-reviewed nutrient publication;
- activation before exact authority is readable;
- unapproved schema/migration need.

## 12. Projected product effect

Before R2-F runtime:

- exact-`MILK_2_5` unaffected BREAKFAST-compatible pool = 2;
- capacity = 6/week.

After both selected sandwiches:

- unaffected BREAKFAST-compatible pool = 4;
- capacity = 12/week;
- required opportunities = 7.

The future runtime PR must prove a persisted seven-BREAKFAST week under hard exact
`MILK_2_5` exclusion with no RecipeVersion exceeding repetition=3.

Classification counts must remain truthful:

- active `breakfast` **classification** remains 7;
- two new active `sandwich` classifications are added;
- BREAKFAST-compatible candidate pool becomes 9 through the existing mapping;
- LUNCH gains 2 compatible sandwich candidates;
- SNACK gains 2 compatible sandwich candidates.

This is **not a dairy-allergy claim**. Butter and cheese are dairy foods; closure
concerns only exact canonical `MILK_2_5`.

## 13. Required runtime acceptance

A later R2-F runtime PR must prove at least:

1. exactly three new identity-only foods and no Nutrition/Composition;
2. exactly two immutable SOURCE_VERIFIED `sandwich` RecipeVersions;
3. exact ingredient net/gross quantities and 30 g output;
4. prepared ENERGY_KCAL exactly 66.3 / 83;
5. all other 53 frozen nutrient codes UNKNOWN;
6. reviewed derivative/card-hash tampering fails closed;
7. fresh RecipeVersion + prepared authority publication is atomic;
8. exact replay is zero-write;
9. deliberate deactivation remains deactivated;
10. guarded activation yields exact-energy eligible candidates;
11. hard `MILK_2_5` rejects affected milk recipes but not egg, casserole or
    either sandwich;
12. persisted seven-BREAKFAST week succeeds under hard `MILK_2_5`;
13. no selected recipe exceeds repetition=3;
14. both RecipeVersions are compatible with BREAKFAST, LUNCH and SNACK under the
    existing mapping;
15. no dairy-allergy/medical claim;
16. migration head remains 0042;
17. `AI_ENABLED=false`.

## 14. Verification tier

This PR is docs/data/source-evidence only.

Required:

- all committed JSON parses;
- reviewed-derivative/card hash recomputation;
- macro QA arithmetic;
- source-policy scope exactly two cards;
- identity review consistency;
- capacity arithmetic;
- Docs verification;
- DC1 corpus verification where triggered;
- scope/whitespace audit.

No runtime/backend regression is required for this gate.

## 15. Non-goals

No runtime publication/activation, migration 0043, schema changes, Planner
algorithm/mapping/repetition changes, new Nutrition authority, ingredient
Nutrition/Composition, third sandwich, bulk web/PDF ingestion, DC4, Gate1-CLOSE,
PR9 Shopping, Prep/Retail/API/UI/Auth/PostgreSQL/AI.

## 16. Stop rule

After the R2-F Contract Gate is review-ready, stop for independent review.

Runtime implementation starts only after this gate is reviewed and merged. The
runtime PR must implement the two selected sandwiches as one batch and stop again.
