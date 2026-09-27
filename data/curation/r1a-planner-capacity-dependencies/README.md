# R1-A — Planner-capacity recipe dependency closure

**Status:** production data publication package for Issue #99 / PR #101
**Accepted base:** `9f72f6883e092cbf79930c7ac4a5a1314c7488d8` (merged PR #98)
**Operation:** `R1-A_PLANNER_CAPACITY_DEPENDENCIES`

## Goal

Restore the original product meaning of Russian-data Step 8 for the first
Planner-capacity recipe batch.

R1-A does not publish recipes. It closes only the FoodIngredient/form/Nutrition
dependencies directly required by the seven selected R1 recipes.

## Selected recipes

Breakfast:

- `USSR82-453 — Яйца вареные`
- `USSR82-467 — Омлет (натуральный)`
- `USSR82-492 — Сырники из творога`
- `USSR82-1081 — Блины`

Main-target candidates:

- `USSR82-697` — exact chicken/main branch only;
- `USSR82-364 — Шницель из капусты`;
- `USSR82-208 — Рассольник ленинградский`.

The exact dependency partition is in
[dependency-manifest.json](dependency-manifest.json).

## Source recovery

The accepted durable source artifact was independently retrieved on 2026-09-27:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

Verified:

- size: `206692075` bytes;
- archive SHA-256:
  `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- embedded `corpus-work/packages/nutrition/raw/ion-db.html` SHA-256:
  `155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d`;
- exact RU-NUT-DB record count: `3216`.

No source values are reconstructed from OCR or web snippets in this package.
The publication payload is extracted from those exact retained source bytes.

## Late-state reconciliation

Old DC1 statuses are not copied forward mechanically.

Later accepted decisions close several dependencies without a new R1-A write:

- `RICE_GROATS` and `CARROT_RED_RAW` — accepted Step 4 FIC publications;
- `EGG`, `BUTTER_UNSALTED`, `CABBAGE_GREEN`, `SUGAR` — accepted current
  RU-ready/ATOMIC authorities;
- `BREADCRUMBS` — accepted RU-ready/ATOMIC authority plus the later v0.3
  `сухари панировочные → BREADCRUMBS` review hint.

R1-A publishes eleven exact FIC authorities:

| Dependency | FamilyFoodOS | FIC code / DB index |
|---|---|---|
| ING-0030 | MARGARINE_MILK_TABLE | 1432 / 509 |
| ING-0034 | MILK_PASTEURIZED_3_2 | 929 / 549 |
| ING-0047 | SOUR_CREAM_30 | 942 / 681 |
| ING-0056 | TVOROG_9 | 968 / 813 |
| ING-0097 | YEAST_BAKERS_COMPRESSED | 31 / 915 |
| ING-0025 | CHICKEN_CATEGORY_1_RAW | 158 / 110 |
| ING-0019 | POTATO (reuse existing identity) | 46 / 77 |
| ING-0028 | ONION_BULB_FRESH | 1186 / 118 |
| ING-0036 | FLOUR_WHEAT_HIGH_GRADE | 82 / 132 |
| ING-0006 | WATER (reuse existing identity, ATOMIC v2) | 3000 / 360 |
| ING-0050 | SALT (reuse existing identity, ATOMIC v2) | 125 / 932 |

Each record publishes the same frozen Step 4B set of 18 V2 concepts and retains
all 26 reviewed source observations. This includes source-published
`ENERGY_KCAL=0.0` for WATER and SALT; those zeros are published source values,
not inferred replacements for unknowns. Carbohydrate remains unavailable in the
legacy five-field profile because the frozen FIC `carbh` definition remains
ambiguous.

## Explicit blockers

Two dependencies remain blocked and are **not** substituted:

### ING-0014 — Жир кулинарный

No exact RU-NUT-DB record exists in the accepted snapshot. Records such as
`Жир свиной` or `Жир свиной топленый` are not silently treated as equivalent
to generic source `Жир кулинарный`.

### ING-0038 — Огурцы соленые

RU-NUT-DB contains exact label record `code=1240 / DB/3121`, but the retained
record has a structural field-layout anomaly: Eurocode fields are shifted/type
inconsistent relative to normal source records, with corresponding suspicious
numeric placement.

R1-A pins the raw record hash in the dependency manifest but does not repair,
reinterpret or publish it. A later bounded review may resolve it from an
independent same-publisher/source representation.

## Allergen / exclusion boundary

R1-A does not infer allergen truth from a product name or a nutrition record.
The accepted FIC composition snapshot is not an allergen-label source.

New R1-A FoodIngredients therefore remain `allergens_reviewed=false` with no
invented allergen codes. This is an explicit limitation, not a silent pass.

For R1 product proof:

- hard ingredient exclusions remain authoritative and must be exercised in R1-C;
- a member exclusion must remove every R1 recipe containing that FoodIngredient;
- household sharedness must never override that exclusion;
- automatic allergen-code filtering is not claimed until separately reviewed
  FoodIngredient allergen truth exists.

## Expected result

After successful R1-A publication:

- 20 unique R1 dependencies have exact dispositions;
- 18 are accepted/reusable;
- WATER and SALT now have exact FIC zero-energy authority for the Step10 Planner path;
- 2 remain blocked;
- 5 of 7 selected recipes have all food dependencies closed for R1-B:
  - USSR82-453;
  - USSR82-467;
  - USSR82-492;
  - USSR82-1081;
  - USSR82-697;
- USSR82-364 remains blocked on ING-0014;
- USSR82-208 remains blocked on ING-0038.

R1-B still owns process/output/transformation review and RecipeVersion
publication. Dependency readiness is not automatic Recipe activation.

## Publication behavior

The runtime entry point is:

`backend/app/seed/ru_nut_db_r1a.py`

It reuses the accepted Step 3 transactional batch publisher and the frozen Step
4B field mapping:

- one UoW / one fresh commit;
- exact replay = zero writes;
- conflict fails closed;
- partial prior batch fails closed;
- failure at any bundle rolls back the whole batch;
- existing current profiles are not replaced;
- new profiles remain non-current;
- no migration/schema change.

## Non-goals

- no RecipeVersion publication;
- no Planner/Serving change;
- no energy-allocation fix (#100);
- no Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI;
- no generalized ingestion;
- no unrelated catalogue expansion.

## Verification

Focused runtime tests must prove:

- exact 11-record / 198-value / 286-observation package;
- source hash pins;
- fresh + replay;
- existing-current preservation;
- created identity count (8 new + 3 existing-identity reuses: POTATO/WATER/SALT);
- exact ATOMIC versions;
- conflict / partial-state / rollback behavior;
- dependency-manifest partition and 5/2 recipe readiness result;
- FK cleanliness.
