# Handoff

## Current update — first DC2 batch review, 2026-09-20

PR71 merged at `9b1d5c73da4f1d779336a35e0e7e2c2d32363e85`.
The user authorized the next source/form review stage. See
[first-batch review](../data/curation/dc2-first-batch-review/README.md) and
[current focus](current-focus.md), which supersede older execution statuses below.
25 group decisions account for1532 occurrences and24 source-record candidates;
14 profiles have earlier visual evidence. No publication, accepted canonical
mapping or nutrient-policy change. The next exact blockers are documented in
publication-decisions.md; do not restart source discovery without reading them.


Updated: `2026-09-20`.

## Current handoff after PR70 merge

Accepted main is `b9768984392982bd05d28fc0f7793453fe8378b5` (merged PR #70).
PR #71 is being synchronized and verified for the user-authorized merge.
See [current focus](current-focus.md), [integration plan](../docs/family-food/corpus-v03-integration-plan.md)
and [reconciliation package](../data/curation/corpus-v03-reconciliation/README.md).

The PR70 recovery artifacts and source input hashes are preserved. Its final
head `514c6b1` has the same tree as the historical `c23227b` input pin used by
v0.3 reconciliation. Generated historical merge-status flags remain capture
metadata, not live project state. All current statuses are owned by this section
and current-focus; the receipt below is historical.

Reconciliation retains 547 crosswalk records, 2693 food occurrences and 46
review queues, all without production publication. Exact form/source/rights/
nutrient decisions are next proposed work, not automatically authorized.
After the authorized PR71 merge, stop. DC2/DC3/DC4, Gate1 and PR9 remain open.

## Preserved pre-merge PR70 handoff receipt — historical

The following text records the earlier delivery state. Its REVIEW-READY and
not-merged wording is superseded by the current handoff above.

### Original handoff

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

The inconsistent pre-rebuild GitHub package is preserved for recovery under:

`data/curation/data-corpus-v1-dc1/recovery/pre-rebuild-b7bc19e8881ddc90/`

The exact original pre-rebuild bytes remain available at commit
`b7bc19e8881ddc90b95bd8d13c75e72ee4623295`. The copied recovery README was
later whitespace-normalized only for repository Docs verification; its metrics/data
content was not changed.

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
- 28 non-existing identities have a preferred source-family search target;
  exact source presence, record identity and form compatibility remain unverified;
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
- preferred source-family search targets are not evidence that a compatible
  source record exists and are not exact-record authority closure;
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

Current heavy verification applies to the generator/generated-package bytes
finalized on branch head `78c81ff7f55c6878be9112b75f766c78fe73c639` before the following state-only
finalization commits:

- exact repository PR39 mapping inputs restored byte-for-byte: PASS;
- exact production nutrition seed restored byte-for-byte: PASS;
- raw XLSX generator source-hash enforcement: PASS;
- build A: PASS;
- build B: PASS;
- validator A/B: PASS;
- 15-case adversarial suite: PASS;
- build A == build B: PASS.

The generated package at `78c81ff...` is the output of the current generator.
Subsequent finalization commits are state-only and do not alter the generator or
generated package bytes covered by this evidence. Final-head automatic package
verification rechecks checksums, validator behavior and the formatted
15-case adversarial suite.

Raw source XLSX bytes are operator-managed external evidence. Exact required
filenames/hashes are recorded in `source-artifacts.json`. The ZIP/container
hash is diagnostic only; canonical source identity is the exact file set plus
per-file SHA-256. The raw source ZIP must not be uploaded as a GitHub Actions
artifact in this public repository. Automatic PR CI runs package verification;
full raw-source rebuild is manual `workflow_dispatch` against explicit
`target_ref`, using the temporary authenticated URL only through
`DC1_SOURCE_BUNDLE_URL`.

Final Docs verification and automatic package verification must be GREEN on the
review head before merge.

## Scope boundary

No production FoodIngredient/Nutrition/Composition/RecipeVersion publication,
schema, migration, Planner, API or UI change belongs to this PR.

## Stop condition

After DC1 review/merge, stop.

Do not automatically start DC2, DC3, DC4, Gate1-CLOSE or PR9.
