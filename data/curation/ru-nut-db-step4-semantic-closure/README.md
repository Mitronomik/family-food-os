# RU-NUT-DB Step 4 — source-semantic mapping closure

**Status:** mapping frozen; runtime publication blocked pending schema decision
**Accepted base:** `f7ac885dde055900b3a6397aa64a15fe698abe5b` (merged PR #80)
**Source:** licensed FIC `RU-NUT-DB` snapshot captured 2026-09-20
**Batch:** SUGAR, CARROT_RED_RAW, CABBAGE_GREEN, BEET, RICE_GROATS

## Goal

Close the source-field semantics required before the first Step 4 publication.
This package publishes no production nutrient values, profiles, seals or ATOMIC rows.

## Frozen mapping

Eighteen source fields are approved for **positive values only**:
`kcal, prot, fat, satur, starch, mdsug, diet_fibre, water, b1, b2, c,
ret_equiv, na, k, ca, p, fe, mg`.

Every mapped positive value uses `method_code=published_method_unspecified`.
Across the five records this yields **74** candidate V2 numeric values:
SUGAR 7; CARROT_RED_RAW 17; CABBAGE_GREEN 17; BEET 17; RICE_GROATS 16.

Eight fields stay deferred/source-only:
`carbh, a_vit, pp, carot, cholest, ethanol, sugar_ad, salt_ad`.

All **43** source zeros remain nonnumeric evidence. No zero is promoted to exact
canonical zero.

## Runtime blocker

The mapping itself is closed, but the exact five-food batch is not representable
by the current legacy-profile observation enum.

SUGAR publishes literal zero for `prot` and `fat`. The source state is neither
missing, established below-detection, nor method-incompatible, and zero authority
is unresolved. Current persisted states are only:
`value | missing | below_detection | method_incompatible`.

Therefore runtime Step 4 requires an explicit architecture decision:

1. preserve the five-food batch by adding a persisted state such as
   `published_zero_unresolved` through a separately approved migration/domain
   contract amendment; or
2. keep the current schema and defer SUGAR, changing the accepted first-batch scope.

Do not mislabel or numerically coerce the source zero to avoid this decision.

## Evidence files

- `field-mapping.json` — 26 exact mapping/defer decisions;
- `batch-source-state.json` — five source records and field states, no source numeric values;
- `source-evidence.json` — pinned source/interface hashes and live-form conflict receipt;
- `verification-summary.json` — exact counts and runtime blocker;
- `checksums.sha256` — package integrity.

## Non-goals

No migration, runtime publication, current-profile switch, Book2002 numeric
substitution, Planner/API/UI work or Step 5 work is included.
