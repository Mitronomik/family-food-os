# RU-NUT-DB Step 4 — source-semantic mapping closure

**Status:** mapping frozen; runtime publication ready after evidence merge/review
**Accepted base:** `f7ac885dde055900b3a6397aa64a15fe698abe5b` (merged PR #80)
**Source:** licensed FIC `RU-NUT-DB` snapshot captured 2026-09-20
**Batch:** SUGAR, CARROT_RED_RAW, CABBAGE_GREEN, BEET, RICE_GROATS

## Frozen mapping

Eighteen source fields are approved for published numeric values, including
source-published `0`:

`kcal, prot, fat, satur, starch, mdsug, diet_fibre, water, b1, b2, c,
ret_equiv, na, k, ca, p, fe, mg`.

Across five records this yields **90 V2 numeric values — 18 per food**.

A source-published zero is stored as numeric `Decimal("0")`. This preserves what
FIC published; it does not claim independently established analytical absence.
The source literal and method provenance remain explicit.

Eight fields stay deferred/source-only:
`carbh, a_vit, pp, carot, cholest, ethanol, sugar_ad, salt_ad`.

## Why no zero migration is needed

`NutritionObservationState.VALUE` records that a source supplied a numeric value.
It is not a scientific-certainty label. Therefore SUGAR `prot=0` and `fat=0`
are represented as numeric zero plus VALUE observations preserving literal `"0"`.

No new observation state or migration is needed.

## Non-goals

No migration, runtime publication, current-profile switch, Book2002 numeric
substitution, Planner/API/UI work or Step 5 work is included.
