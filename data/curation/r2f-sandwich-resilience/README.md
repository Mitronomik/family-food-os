# R2-F cheese-sandwich resilience-closure contract evidence

Issue: #139.

Accepted main: `561c13aad6ce978de399dfd807071232af06b71c` (merged PR #138).

After independent review, the original two-sandwich batch was narrowed fail-closed
to one production candidate:

- `SAD28_SANDWICH_CHEESE_20_10` — Бутерброд с сыром — 30 g / 83 kcal.

The butter card remains retained discovery/review evidence but is **rejected** from
prepared-output publication. It lists 5 g cream butter while declaring only 0.98 g
fat for the whole sandwich. TR TS 033/2013 defines cream butter at at least 50% fat,
so that component alone contributes at least 2.5 g fat.

Future runtime creates only two identity-only FoodIngredients:

- `WHEAT_BREAD_PLAIN`;
- `CHEESE_UNSPECIFIED`.

No Nutrition or Composition authority is granted to those identities.

## Durable publication source

The future SOURCE_VERIFIED RecipeVersion is pinned to the complete selected-card
raw text snapshot:

`data/curation/r2f-sandwich-resilience/raw-cheese-card.txt`

SHA-256:

`77bc74917305adb0d4fee7a54910c9675068b1ec093a051f7c58bd34cc7dd27c`

Byte size: 1783.

Immutable Git locator:

`https://raw.githubusercontent.com/Mitronomik/family-food-os/97ed76c7009229b5c947c63f1ace09b63a32147b/data/curation/r2f-sandwich-resilience/raw-cheese-card.txt`

Durable Library locator:

`library:/FamilyFoodOS/source-artifacts/sad28-cheese-card-raw-text-2026-10-03.txt`

Library file id: `libfile_baff1ee2870081918170b98d1cec3c5d`.

The Library copy was materialized again and independently re-hashed to the same
1783 bytes / SHA-256 on 2026-10-03.

Provenance roles are deliberately separated:

- SAD28 / МАДОУ №28 — official host of the public technological-card file;
- document/card issuer — `NOT_ESTABLISHED_FROM_RETAINED_CARD`;
- upstream recipe collection — Kutkina M.N., Saint Petersburg, 2008.

The upstream PDF is discovery/corroboration only. Its exact bytes were not
retrievable through the available execution environment, so no PDF byte hash is
invented and the PDF is not used as RecipeVersion source truth. Future expansion
of this source family requires reacquisition and a new review.

## Product effect

Under hard exact `MILK_2_5` exclusion:

- current unaffected BREAKFAST-compatible pool: 2 / capacity 6;
- projected after cheese runtime: 3 / capacity 9;
- required BREAKFAST opportunities: 7.

The existing Planner mapping already permits `sandwich` for
BREAKFAST/LUNCH/SNACK, so no Planner change is required.

This is not a dairy-allergy claim: the selected cheese sandwich contains dairy.

See `docs/family-food/r2f-sandwich-resilience-gate.md`.
