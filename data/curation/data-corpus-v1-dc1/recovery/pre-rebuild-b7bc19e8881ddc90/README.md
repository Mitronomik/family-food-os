# DATA-CORPUS-V1 / DC1 — source authority + coverage inventory

Status: evidence/curation package for Issue #67.  
Repository base: `d8c76a64483e3d5814e702be33c12cbe2e144160` (merged PR #69).  
Production publication: **NO**. Schema/migration/runtime/API/UI changes: **NO**.

## FACT — selection

DC1 reuses merged PR #39 instead of repeating identity mapping. The initial candidate universe is every
`DIRECT_EXISTING_MAP_LEAD` plus every `CATALOGUE_EXTENSION_LEAD`.

Result: **68 recipe families**, all already classified `READY_RAW` by the accepted v22.13 package.
`45` are strict-raw leads.

This is a curation funnel, not production approval and not the final consumer assortment.

## FACT — source variants

- **27** families have one exact/preselected retained source branch.
- **41** expose multiple source branches and remain variant-selection review items.

No branch is selected merely because it avoids new FoodIngredient work.

## FACT — food/form demand

The 68-family slice contains **55 external ingredient identities** and
**55 deduplicated food/form demands**.

- **23** reuse current accepted FamilyFoodOS identity/profile truth.
- **32** require DC2-level identity/form/authority closure.

External v22 nutrient values remain reference evidence only.

## FACT — exact/preselected funnel

Zero-new/form-split candidates: `USSR82-323`, `USSR82-442`, `USSR82-453`.

DC3 partition:
- `DC3-A_ZERO_NEW_PROFILE`: 3;
- `DC3-B_LOW_DEBT_EXACT_VARIANT`: 8;
- `DC3-C_EXACT_VARIANT_AFTER_DC2`: 16;
- `DC3-D_VARIANT_SELECTION_REVIEW`: 41.

## DECISION — proposed DC2 partition

- `REUSE_NO_DC2_WRITE`: 23 demands.
- `DC2-A_HIGH_IMPACT`: 15 demands used by >=4 candidate families or >=2 exact/preselected families.
- `DC2-B_COMMON_EXTENSION`: 7 lower-impact non-proxy demands.
- `DC2-C_IDENTITY_FORM_REVIEW`: 10 proxy/form-sensitive demands.

Batch membership is prioritization, **not publication approval**. Every row must close its recorded blocker first.

## Authority boundary

For existing exact/alias mappings, use current accepted repository profiles; do not re-promote workbook nutrients.

For missing demands:
- A-tier exact Russian references are recorded as Russian primary/official candidates and remain blocked by exact-row/rights review;
- form-split rows require exact FamilyFoodOS form selection first;
- proxy rows require identity closure before nutrition authority;
- B-tier/multi-source references require one compatible official source to be pinned.

Canonical authority and rights rules remain in `docs/family-food/data-corpus-v1.md`.

## Source lineage

Accepted mapping baseline: merged PR #39, checkpoint SHA-256
`a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`.

The older v22.5 row shards are used only for retained source relationship/variant inventory and aggregate demand counting.
Their nutrient values and reference URLs are not FamilyFoodOS production Nutrition authority.

## OPEN QUESTIONS

1. 37 candidate families still need exact source-branch selection.
2. 62 deduplicated food/form demands still need DC2 closure.
3. Russian primary composition rights remain a real gate where that source tier is required.
4. The low-debt funnel is skewed toward soups/vegetables/eggs; DC3 must preserve realistic weekly variety.

## Files

- `candidate-recipes.csv` — 68 recipe families, branch status and DC3 partition.
- `food-demand.csv` — 95 deduplicated food/form demands, impact and authority blocker.
- `batch-plan.json` — exact proposed DC2/DC3 membership.
- `source-artifacts.json` — source/evidence fingerprints and usage limits.
- `summary.json` — machine-readable reconciliation totals.

## Stop condition

DC1 is evidence only. After review/merge, stop. DC2/DC3 remain **NOT STARTED** and require separate reviewable production batches.
