# Current focus

Updated: 2026-10-03.

## Accepted state

PR #138 / R2-E runtime is merged into `main` at:

`561c13aad6ce978de399dfd807071232af06b71c`.

Current exact-energy production state:

- active `breakfast` classification: 7 RecipeVersions;
- active MAIN classification: 5 RecipeVersions;
- `max_recipe_repetitions=3`;
- hard exact `MILK_2_5` exclusion leaves `HARD_BOILED_EGG` and
  `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`;
- unaffected BREAKFAST-compatible capacity = 6/week;
- seven-BREAKFAST remains bounded-infeasible under that exact exclusion.

## Current bounded operation

**R2-F — cheese-sandwich resilience-closure Contract Gate.**

Issue: `#139`.

Branch: `docs/r2f-sandwich-resilience-gate`.

Accepted base:

`561c13aad6ce978de399dfd807071232af06b71c`.

Status:

`SOURCE_PROVENANCE_CORRECTION_VERIFICATION_PENDING`.

## Corrected frozen candidate

Future runtime publishes exactly:

- `SAD28_SANDWICH_CHEESE_20_10` — 30 g / exact same-card 83 kcal.

The butter sandwich is rejected from prepared-output publication because the
source lists 5 g cream butter but only 0.98 g total sandwich fat; under
TR TS 033/2013 cream butter is at least 50% fat, so that component alone implies
at least 2.5 g fat.

Create identity-only:

- `WHEAT_BREAD_PLAIN`;
- `CHEESE_UNSPECIFIED`.

No Nutrition/Composition is granted to those identities.

## Durable source boundary

Future RecipeVersion source document:

`data/curation/r2f-sandwich-resilience/raw-cheese-card.txt`

SHA-256:

`77bc74917305adb0d4fee7a54910c9675068b1ec093a051f7c58bd34cc7dd27c`

Byte size: 1783.

Durable Library:
`library:/FamilyFoodOS/source-artifacts/sad28-cheese-card-raw-text-2026-10-03.txt` / `libfile_baff1ee2870081918170b98d1cec3c5d`.

Library materialize/readback re-hash: PASS, same 1783 bytes / SHA-256.

SAD28 is recorded only as official host. Document/card issuer is not established
from the retained card. Upstream recipe collection is Kutkina 2008.

The upstream PDF remains discovery/corroboration only; no PDF SHA is invented.

## Product boundary

Projected after later runtime:

- active `breakfast` classification remains 7;
- active `sandwich` classification +1;
- BREAKFAST-compatible pool becomes 8;
- hard exact `MILK_2_5` unaffected pool becomes 3 / capacity 9;
- LUNCH and SNACK each gain 1 compatible candidate.

This is exact `MILK_2_5` resilience only, not a dairy-allergy claim.

## Scope boundaries

Do not:

- publish/activate runtime data in this gate;
- add migration 0043 or schema changes;
- change Planner algorithm/mapping/repetition;
- add a new Nutrition authority;
- grant Nutrition/Composition to new identities;
- publish the rejected butter or deferred povidlo cards;
- bulk-import the website/PDF;
- start DC4/Gate1-CLOSE/PR9;
- start API/UI/Prep/Retail/Auth/PostgreSQL/AI.

## Verification pending

Source-provenance correction requires fresh exact-head verification:

- JSON parse/consistency;
- raw-card SHA/size;
- Library materialize/readback receipt;
- source tuple coherence;
- provenance role separation;
- Docs/DC1;
- scope/whitespace.

Do not start runtime publication before corrected PR #140 is independently
reviewed and merged.
