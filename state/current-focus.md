# Current focus

Updated: 2026-10-03.

## Accepted state

PR #142 / R2-F runtime is merged into `main` at:

`da6d1e05fd44ecc2733e1a6f472eae3e54b60604`.

Accepted production Planner catalogue now includes the R2-F cheese sandwich;
hard exact `MILK_2_5` seven-BREAKFAST resilience is proven at three unaffected
candidates × repetition 3 = capacity 9.

DATA-CORPUS-V1 / DC3 remains active. The canonical DC3 batch guidance is
~10–20 recipes; after the merged micro-publication sequence, the next operation
is intentionally enlarged.

## Current bounded operation

**R3-A — School2022 ten-recipe MAIN batch Contract Gate.**

Issue: `#144`.

Branch:

`docs/r3a-school2022-main-batch-gate`.

Accepted base:

`da6d1e05fd44ecc2733e1a6f472eae3e54b60604`.

Status:

`GATE_EVIDENCE_REVIEW_ACTIVE`.

Canonical contract under review:

`docs/family-food/r3a-school2022-main-batch-gate.md`.

## Goal

Freeze one reviewable DC3 batch of exactly 10 School2022 MAIN RecipeVersions,
using one source family and the existing
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1` seam.

No runtime publication is authorized until this gate is independently reviewed
and merged.

## Batch boundary

Selected cards are frozen in:

`data/curation/r3a-school2022-main-batch/candidate-selection.json`.

The batch:

- contains exactly 10 unique MAIN cards;
- creates exactly 5 identity-only FoodIngredients;
- reuses existing accepted identities for all remaining rows;
- publishes only ENERGY_KCAL in future runtime; other 53 nutrient codes remain UNKNOWN;
- requires no migration/schema/Planner/new-authority change.

Fail-closed source review removed School2022 `54-5м` and `54-12м` because
their ingredient tables name sunflower oil while process text names butter for
the corresponding operation. `54-15м` remains deferred because process water
and bay leaf are not quantified in the ingredient table.

## Source boundary

Reuse accepted School2022 evidence only:

- PDF SHA-256:
  `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`;
- durable archive:
  `private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`;
- archive SHA-256:
  `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- latest accepted independent archive verification remains 2026-10-01.

This gate does not claim a new archive readback. Public PDF recheck is
corroboration only.

## Scope boundaries

Do not:

- publish/activate R3-A runtime data;
- add migration 0043 or schema changes;
- change Planner mapping/scoring/repetition;
- add a new Nutrition authority;
- add Nutrition/Composition to the five new identities;
- resolve source contradictions by inference;
- start DC4/Gate1-CLOSE/PR9;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.

After the gate is review-ready, stop for independent review.
