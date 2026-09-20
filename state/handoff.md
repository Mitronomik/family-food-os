# Handoff

Updated: `2026-09-20`.

## Accepted base and governance

Accepted current main:

`d8c76a64483e3d5814e702be33c12cbe2e144160`

Current bounded operation:

`DATA-CORPUS-V1 / DC1 — Source authority + coverage inventory` — ACTIVE under
Issue #67.

Recovered implementation is REVIEW-READY on:

`data/data-corpus-v1-dc1`

Accepted SQLite migration head remains:

`0032_meal_plan_serving`

Reserved future migration remains:

`0033_recipe_template_catalogue`

DC2, DC3, DC4, Gate1-CLOSE and PR9 are NOT STARTED.

## Recovery checkpoint

The inconsistent pre-rebuild GitHub package is preserved unchanged under:

`data/curation/data-corpus-v1-dc1/recovery/pre-rebuild-b7bc19e8881ddc90/`

Known pre-rebuild commit:

`b7bc19e8881ddc90b95bd8d13c75e72ee4623295`

Recovery checkpoint completion commit:

`0c311848341da397b837abf12fcca4b442de8acd`

The old package is historical evidence only.

## Root cause recovered

The interrupted package consumed a text-rendered spreadsheet view as if it were
the complete v22.5 relationship-row shards.

The raw source contract requires:

`1550 + 1550 + 1550 + 1529 = 6179` rows.

Direct raw-XLSX parsing recovers all 68 candidate families and 991 relevant
source relationship/calculation rows. Missing rendered rows had previously been
misinterpreted as zero ingredient demand.

## Rebuilt package

Evidence package:

`data/curation/data-corpus-v1-dc1/`

Generator and validator:

- `scripts/build_data_corpus_v1_dc1.py`;
- `scripts/validate_data_corpus_v1_dc1.py`.

Current reconciliation:

- 68 candidate families;
- 991 relationship/calculation rows;
- 96 external ingredient identities;
- 33 accepted existing/alias mappings;
- 63 identities requiring later DC2-level closure if pursued;
- full accepted PR39 input contract: 350 recipe rows / 363 ingredient identities;
- structural source-Variant split: 31 one / 37 multiple;
- safe publication-branch split: 5 simple / 63 review-required;
- 33 existing mappings have exact current USDA FDC profile provenance identified,
  but recipe-form suitability remains review-required;
- 28 non-existing identities have an official source-family candidate with exact
  record still unpinned;
- 35 identities are blocked on identity/form semantics before exact authority
  assignment.

The previous 95-demand result is not retained: it depended on unsafe
display-name deduplication. In particular `ING-0014` and `ING-0069` remain
separate identities; the v22.5/v22.13 label conflict is explicit evidence debt.

## Compatibility limits

For all 68 candidates:

- v22.5 calculation rows match v22.13 `CalcRows`;
- accepted PR #39 mapping aggregates are reproduced;
- v22.5 Variant counts match v22.13 `VariantBlocks`.

Full row-level relationship equivalence is not claimed because the exact
v22.13 row-nutrient shards were unavailable during recovery.

Recorded blockers include:

- 20 candidates with additional v22.13 non-calculation relationship rows;
- 20 used identities with v22.5/v22.13 label differences;
- 63 candidate families needing variant/choice/optional/boundary/compatibility/
  semantic review;
- all 33 existing profiles still need exact recipe-form suitability review;
- candidate source-family assignment is not exact-record authority closure;
- assortment gaps in the preserved 68-family funnel.

## Verification evidence

Current review-fix verification:

- exact GitHub package audit: PASS for 68 candidates / 991 relationships /
  96 demands / 33 existing mappings / 63 non-existing mappings;
- safe branch split: 5 simple / 63 review-required;
- full PR39 input metadata: 350 / 363;
- current production nutrition seed metadata: 183 rows and exact Git blob identity;
- DC2/DC3 batch partitions: exact coverage with no overlap;
- authority assignment state present for all 96 demands;
- package SHA-256 manifest: PASS for all 11 generated artifacts;
- committed adversarial harness:
  `scripts/test_data_corpus_v1_dc1.py`.

The current runtime cannot resolve `github.com`, so the updated generator,
validator and adversarial harness could not be executed from a fresh local
checkout after these review fixes. Do not reuse the earlier pre-fix py_compile /
double-build receipts as final-head execution evidence.

Final GitHub Docs verification must be GREEN on the exact PR head before merge.

## Scope boundary

No production FoodIngredient/Nutrition/Composition/RecipeVersion publication,
schema, migration, Planner, API or UI change belongs to this PR.

## Stop condition

After DC1 review/merge, stop.

Do not automatically start DC2, DC3, DC4, Gate1-CLOSE or PR9.
