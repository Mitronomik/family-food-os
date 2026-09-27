# R1-B — reviewed USSR82 RecipeVersion publication

**Status:** bounded runtime publication package
**Accepted base:** `fb89cfeb84f4052233f82daa7dcc2d1c07aa971a` (merged PR103)
**Contract:** `docs/family-food/r1b-source-output-contract.md`
**Parent:** #102 / #99 / #67

## Outcome

The original five dependency-ready R1-B source candidates were reviewed against
retained source process + quantified ingredient evidence.

Final R1-B disposition:

| Source recipe | Disposition | Reason |
| --- | --- | --- |
| USSR82-453 — Яйца вареные | PUBLISH | exact quantified ingredient/process/output evidence |
| USSR82-1081 — Блины, III — с маслом | PUBLISH | exact selected variant, quantified process ingredients and output |
| USSR82-697 — selected chicken/main branch | PUBLISH | exact chicken/onion branch and output; garnish/sauce excluded |
| USSR82-467 — Омлет (натуральный) | BLOCKED | verified instruction requires salt but retained quantified rows contain no salt quantity |
| USSR82-492 — Сырники из творога | BLOCKED | verified instruction requires salt but retained quantified rows contain no salt quantity |

No salt quantity is inferred, estimated or omitted from source process truth.

## Source authority

Durable archive:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

Archive SHA-256:

`c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`

RecipeVersion source snapshot:

`russian_normative_recipes_v20_complete_master.xlsx`

SHA-256:

`6ac7dfb300844fd996aee6d20b4e7e6aa421dd517367ab1f59120812fee104d5`

Supporting mass/relationship evidence:

`russian_normative_recipes_v22_13_mass_nutrients.xlsx`

SHA-256:

`5ea78ead82568f8aff019a4076215c6598675783cb81e0d1d5b4f913016de4cc`

RecipeVersion provenance uses:

```text
source_name = USSR82
source_version = sha256:6ac7dfb300844fd996aee6d20b4e7e6aa421dd517367ab1f59120812fee104d5
source_document_sha256 = 6ac7dfb300844fd996aee6d20b4e7e6aa421dd517367ab1f59120812fee104d5
```

Per-card SourceURL and exact `USSR82-*` source identity remain in the reviewed
publication payload.

## Published variants

### USSR82-453 — Яйца вареные

- canonical code: `USSR82_453_BOILED_EGGS`
- meal type: breakfast
- quantified input: EGG 40 g edible source calculation mass
- source output: 40 g
- exact energy after Composition binding: 62.840000 kcal
- process contains no extra unquantified material ingredient

### USSR82-1081 — Блины

- canonical code: `USSR82_1081_BLINI`
- selected branch: `III — с маслом`
- meal type: breakfast
- quantified inputs:
  - FLOUR_WHEAT_HIGH_GRADE 75 g
  - SUGAR 3 g
  - WATER 118 g
  - YEAST_BAKERS_COMPRESSED 3 g
  - SALT 1.5 g
  - MARGARINE_MILK_TABLE 5 g
  - BUTTER_UNSALTED 10 g
- source output: 160 g
- exact energy after Composition binding: 371.184000 kcal
- alternatives are not mixed

### USSR82-697 — Курица отварная

- canonical code: `USSR82_697_BOILED_CHICKEN`
- exact branch:
  `III, курица, основной продукт без гарнира/соуса`
- meal type: main
- quantified inputs:
  - CHICKEN_CATEGORY_1_RAW 107 g
  - ONION_BULB_FRESH 2 g
- source output: 75 g
- exact energy after Composition binding: 255.892000 kcal
- garnish/sauce are outside this RecipeVersion

The generic source phrase about "предусмотренные коренья" is conditional source
context. The selected quantified branch contains chicken + onion only; no root
ingredient is invented.

## Output / Nutrition boundary

`source_output_g` is immutable source recipe truth.

It does not authorize:

- `output / input` as reusable yield;
- implicit FoodIngredient transformation;
- retention coefficients;
- rescaling Recipe Nutrition;
- cooked/raw substitution.

Step10 Recipe Nutrition remains:

```text
exact input grams
→ pinned FoodCompositionVersion
→ deterministic V2 Recipe Nutrition
```

## Composition authority

The package cross-checks reviewed Composition versions and nutrient values
against accepted hash-pinned loaders:

- Step4 FIC/V2 authority for SUGAR (ATOMIC v2);
- merged R1-A authorities for exact new forms and WATER/SALT;
- R1-B bounded FIC/V2 dependency closure for existing EGG and BUTTER_UNSALTED
  identities (ATOMIC v2).

The R1-B EGG/BUTTER profiles are non-current and preserve historical current
profiles/ATOMIC v1. They exist only to provide exact V2-compatible Composition
authority for the reviewed RecipeIngredient bindings.

The package cannot silently redefine those vectors.

## Publication behavior

R1-B publication order:

1. preflight all three trusted Recipe seeds;
2. accept only all-FRESH or all-EXACT_REPLAY state;
3. publish three RecipeVersions as initially inactive;
4. publish ten exact RecipeIngredient Composition bindings;
5. calculate deterministic canonical Recipe Nutrition;
6. require reviewed exact energy and `exact_energy_ready=true`;
7. activate the three recipes only after every validation succeeds.

A partial prior Recipe batch fails closed rather than being filled in.

## Explicit non-goals

R1-B does not:

- publish blocked 467/492;
- infer missing salt;
- publish 364/208 from R1-A blockers;
- create YieldModel/Retention/Transformation rows;
- alter Planner or Serving algorithms;
- implement #100;
- run R1-C;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.

## Required verification

- migration 0040 fresh/upgrade/restore;
- historical RecipeVersion preservation;
- domain/repository/replay tests;
- exact 3 PUBLISH / 2 BLOCKED package validation;
- ten Composition bindings;
- exact energy validation;
- activation after validation only;
- exact replay;
- partial-batch failure;
- injected rollback;
- no new yield/retention/transformation authority;
- Step10/Planner regression for unchanged semantics;
- broad backend + launcher verification before review-ready.
