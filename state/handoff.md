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
- structural source-Variant split: 31 one / 37 multiple;
- publication-safety split: 26 simple / 42 review-required.

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
- 42 candidate families needing variant/choice/optional/boundary review;
- assortment gaps in the preserved 68-family funnel.

## Verification evidence

Recovered package verification:

- package SHA-256 manifest: PASS;
- `python -m py_compile` for generator + validator: PASS;
- package validator: PASS with
  `68 / 991 / 96 / 33 / 63 / 31-37 / 26-42`;
- two independent builds from the same inputs were byte-identical before the
  runtime restart;
- fail-closed mutation checks rejected candidate/relationship loss, ID mismatch,
  duplicate relationships, zero substitution, summary drift, batch omission,
  batch overlap and false simple/exact classification.

Exact GitHub blob SHAs for regenerated package/tool files were checked against
the preserved local snapshots during delivery.

Final GitHub Docs verification must be GREEN on the exact PR head before merge.

## Scope boundary

No production FoodIngredient/Nutrition/Composition/RecipeVersion publication,
schema, migration, Planner, API or UI change belongs to this PR.

## Stop condition

After DC1 review/merge, stop.

Do not automatically start DC2, DC3, DC4, Gate1-CLOSE or PR9.
