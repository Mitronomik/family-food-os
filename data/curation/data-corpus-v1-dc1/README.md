# DATA-CORPUS-V1 / DC1 — recovered source authority + coverage inventory

**Status:** evidence/curation only for Issue #67.  
**Repository base:** `d8c76a64483e3d5814e702be33c12cbe2e144160` (merged PR #69).  
**Production publication:** **NO**.  
**DC2 / DC3:** **NOT STARTED**.

## Recovery result

This package was rebuilt from raw XLSX bytes and accepted PR #39 mapping files after a completeness defect was found in the interrupted DC1 package.

The prior package used a text-rendered spreadsheet view as if it were the complete row shard. The raw v22.5 manifest requires four shards with **1550 / 1550 / 1550 / 1529 = 6179** rows. Raw XLSX parsing finds **991** candidate relationship/calculation rows for all **68** candidates. The corrupted package had silently treated missing rendered rows as zero ingredient demand.

The preserved pre-rebuild package is under `recovery/pre-rebuild-b7bc19e8881ddc90/`.

## FACT — candidate universe

The candidate universe is unchanged: all accepted PR #39 `DIRECT_EXISTING_MAP_LEAD` + `CATALOGUE_EXTENSION_LEAD` rows.

- recipe families: **68**;
- PR39 external status `READY_RAW`: **68**; this is **not** production readiness;
- strict raw triage YES: **45**;
- one source `Variant`: **31**;
- multiple source `Variant` values: **37**;
- structurally simple single-variant families after ChoiceGroup/optional/boundary review: **26**;
- families requiring variant/choice/optional/boundary review: **42**.

A single `Variant` value is not treated as an exact publication decision. Five one-variant families still require review because of explicit ChoiceGroup or garnish/sauce boundaries.

## FACT — source compatibility

For all 68 candidates:

- v22.5 candidate rows equal v22.13 `CalcRows`;
- v22.5 rows reproduce the accepted PR #39 mapping-state row aggregates;
- v22.5 variant count equals v22.13 `VariantBlocks`.

However **20** candidates have more v22.13 `RelationshipRows` than v22.5 calculation rows. Exact v22.13 row-shard files were not available to this recovery environment. Therefore full row-level relationship equivalence is **not** claimed.

`compatibility.csv` carries this blocker explicitly.

## FACT — food/form demand

This recovery preserves external identity boundaries instead of deduplicating by label:

- external ingredient IDs used: **96**;
- accepted existing/alias mappings: **33**;
- identities requiring DC2-level identity/form/source work: **63**.

The earlier journal number 95 came from collapsing two external IDs with the same displayed label. That is unsafe: `ING-0014` and `ING-0069` must remain separate, and v22.5 candidate rows use `ING-0069` with the label `Шпик` while v22.13/PR39 calls the identity `Жир кулинарный`. DC1 records this as a semantic review blocker rather than guessing equivalence.

Existing PR39 FoodIngredient mappings are reused as identity decisions only. DC1 does **not** claim that a current nutrition profile is automatically suitable for every recipe source form; profile/form suitability remains explicitly not revalidated here.

## DECISION — proposed DC2 triage

- `DC2-A_HIGH_IMPACT`: **6**
- `DC2-B_STANDARD_EXTENSION`: **22**
- `DC2-C_IDENTITY_FORM_REVIEW`: **35**
- `REUSE_NO_DC2_WRITE`: **33**

This is prioritization only. It does not authorize a production write or assert that authority/rights are closed.

## DECISION — proposed DC3 triage

- `DC3-A_SIMPLE_NO_DC2_WRITE`: **3**
- `DC3-B_SIMPLE_AFTER_DC2`: **23**
- `DC3-C_VARIANT_BOUNDARY_REVIEW`: **42**

No source branch is selected merely because it reduces data debt. All batch membership is evidence triage only.

## Assortment review — preserve, do not auto-expand

Category counts in the original 68-family funnel:

- Блюда из творога: **2**
- Блюда из яиц: **11**
- Картофель, овощи и грибы: **14**
- Крупы и каши: **4**
- Макаронные изделия: **2**
- Мучные изделия: **1**
- Мясные блюда: **2**
- Птица и кролик: **3**
- Супы: **23**
- Холодные блюда: **6**

The funnel is visibly skewed toward soups, vegetables/potatoes and egg dishes. Standalone meat/poultry breadth is limited. This is a DC3 variety blocker for a realistic family week, but DC1 does not expand the candidate universe automatically.

## Authority and rights boundary

- External v22.5/v22.13 nutrient values are not promoted to FamilyFoodOS production Nutrition.
- Existing PR39 mappings mean accepted identity mapping, not automatic nutrition-profile/form approval.
- New/form-split/proxy rows retain `NOT_VERIFIED_DC1`; `authority_search_strategy` is only the next verification strategy, not a verified source.
- Rights for future external authority rows remain `PENDING_SELECTED_SOURCE_REVIEW` until an exact source is selected and reviewed under the canonical DATA-CORPUS-V1 policy.

## Files

- `candidate-recipes.csv` — 68 candidates, full relationship counts, variant/choice/optional/boundary status and DC3 triage.
- `food-demand.csv` — one row per external ingredient identity; no unsafe name-based deduplication.
- `compatibility.csv` — v22.5 vs v22.13 count/semantic compatibility status.
- `source-relationships-part1.csv` … `part4.csv` — all 991 retained source relationship/calculation rows for the 68 candidates, sharded by original v22.5 row file and excluding nutrient values.
- `batch-plan.json` — exact non-overlapping DC2/DC3 triage partitions.
- `source-artifacts.json` — input hashes, source usage limits and missing v22.13 row-shard blocker.
- `summary.json` — machine-readable reconciliation totals.
- `checksums.sha256` — deterministic hashes of generated package files.

## Rebuild

The package is generated from raw XLSX bytes plus the accepted PR #39 mapping package. Example:

```bash
python scripts/build_data_corpus_v1_dc1.py   --row-shard /path/russian_normative_recipes_v22_5_row_nutrients_part1.xlsx   --row-shard /path/russian_normative_recipes_v22_5_row_nutrients_part2.xlsx   --row-shard /path/russian_normative_recipes_v22_5_row_nutrients_part3.xlsx   --row-shard /path/russian_normative_recipes_v22_5_row_nutrients_part4.xlsx   --v22-5-manifest /path/russian_normative_recipes_v22_5_manifest.xlsx   --v22-13-mass /path/russian_normative_recipes_v22_13_mass_nutrients.xlsx   --v22-13-audit /path/russian_normative_recipes_v22_13_integrity_audit.xlsx   --v22-13-manifest /path/russian_normative_recipes_v22_13_manifest.xlsx   --mapping-dir data/curation/v22-13-map-a   --output /tmp/data-corpus-v1-dc1

python scripts/validate_data_corpus_v1_dc1.py /tmp/data-corpus-v1-dc1
```

Source XLSX files are not committed by this package; exact required SHA-256 values are enforced by the generator and recorded in `source-artifacts.json`.

## Verification invariants

The generator fails closed on:

- row-shard truncation or candidate loss;
- missing mapping IDs or duplicate mapping identities;
- duplicate source relationship rows;
- blank/non-positive candidate ingredient amounts;
- v22.5/v22.13 calculation-row or variant-block mismatch;
- disagreement with accepted PR39 per-recipe mapping aggregates;
- summary/batch partition omission or overlap;
- assignment of a simple/exact DC3 triage status while ChoiceGroup, optional, multi-variant or garnish/sauce boundary remains unresolved.

A second build from the same inputs must be byte-identical for all generated package files.

## OPEN blockers

1. **42** candidate families still require variant/choice/optional/boundary review before exact publication-branch selection.
2. **63** external identities require DC2-level closure if their dependent recipes are pursued.
3. **20** candidates have additional v22.13 non-calc relationship rows; exact v22.13 row shards were not available here, so full row-level compatibility remains unproven.
4. **20** used identities have a v22.5/v22.13 label difference requiring review; `ING-0069` is the clearest explicit conflict example.
5. The original 68-family funnel has assortment gaps for a realistic family week; DC1 records the gap but does not widen scope automatically.

## Stop condition

After review/merge of this evidence package, stop. DC2 and DC3 remain **NOT STARTED** and require separate reviewable production operations.
