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
| USSR82-453 — Яйца вареные | BLOCKED | accepted EGG authority is historical-registry only; no R1-B V2 Food/Nutrition expansion |
| USSR82-1081 — Блины, III — с маслом | BLOCKED | accepted BUTTER_UNSALTED authority is historical-registry only; no R1-B V2 Food/Nutrition expansion |
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

The package also pins the accepted DC1 relationship inventory
`source-relationships-part1.csv` at SHA-256
`1765b88b0667f66fb106e5b8ec498cd48bf7fb7af77dfc289efe0dac0f296aba`.
Each candidate names its v20 recipe and instruction rows. The published chicken
ingredients point to DC1 CSV rows 154 and 155 (`ING-0025` 107 g and `ING-0028`
2 g); the loader checks those rows and the CSV hash before publication. The
blocked candidates retain their source output masses and quantified row receipts
for review, without creating RecipeVersions.

## Published variant

### USSR82-697 — Курица отварная

- canonical code: `USSR82_697_BOILED_CHICKEN`
- exact branch:
  `III, курица, основной продукт без гарнира/соуса`
- meal type: main
- quantified inputs:
  - CHICKEN_CATEGORY_1_RAW 107 g
  - ONION_BULB_FRESH 2 g
- source output: 75 g
- deterministic input-composition energy: 255.892000 kcal
- garnish/sauce are outside this RecipeVersion

The generic source phrase about "предусмотренные коренья" is conditional source
context. The selected quantified branch contains chicken + onion only; no root
ingredient is invented.
Hot water in the instruction is the unquantified cooking medium for boiling;
the selected output is the chicken main product without broth.

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

The published chicken branch binds only already accepted R1-A V2-compatible
Composition authorities for CHICKEN_CATEGORY_1_RAW and ONION_BULB_FRESH.

R1-B creates no new Food/Nutrition authority. EGG and BUTTER_UNSALTED remain on
accepted historical-registry authorities; because Step10 V2 binding rejects that
registry mismatch, USSR82-453 and USSR82-1081 stay blocked rather than receiving
new FIC profiles inside this RecipeVersion PR.

The published chicken RecipeVersion is a cooked dish. Main currently has Step 7
applicability infrastructure but no reviewed production transformation/yield/retention
authority for its boiling process. Therefore R1-B validates only deterministic
input-composition energy and does not claim final cooked nutrient truth or Planner
readiness. The recipe remains inactive until a separately reviewed Step 7
process-authority batch closes that gap.

## Publication behavior

R1-B publication order:

1. preflight the single publishable trusted Recipe seed;
2. accept only all-FRESH or all-EXACT_REPLAY state;
3. publish one RecipeVersion as inactive;
4. publish two exact RecipeIngredient Composition bindings using already accepted R1-A Composition versions;
5. calculate deterministic canonical Recipe Nutrition with unknown propagation;
6. validate reviewed deterministic input-composition energy while preserving unknown nutrients;
7. keep the published recipe inactive with `INACTIVE_PENDING_TRANSFORMATION_AUTHORITY` until separately reviewed Step 7 transformation/retention authority exists.

A partial prior Recipe batch fails closed rather than being filled in.

## Explicit non-goals

R1-B does not:

- publish 453/1081 without V2-compatible Food/Nutrition authority;
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
- exact 1 PUBLISH / 4 BLOCKED package validation;
- two Composition bindings;
- deterministic input-composition energy validation;
- explicit inactive disposition pending Step 7 transformation/retention authority;
- exact replay;
- partial-batch failure;
- injected rollback;
- no new yield/retention/transformation authority;
- Step10/Planner regression for unchanged semantics;
- broad backend + launcher verification before review-ready.
