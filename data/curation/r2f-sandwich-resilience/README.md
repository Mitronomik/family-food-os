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

## Durable runtime source

Runtime truth is not the live institutional PDF. The exact selected cheese card is
retained as:

`data/curation/r2f-sandwich-resilience/runtime-source.json`

Exact UTF-8 file SHA-256:

`26f239916b56429e78314369df961c8dd13cecd7d559d942655387e9851a5a97`

Exact byte size: 1855.

Immutable retained-source locator:

`https://raw.githubusercontent.com/Mitronomik/family-food-os/a35ef046538687bcaf2600d5027f87688e9224ca/data/curation/r2f-sandwich-resilience/runtime-source.json`

The upstream PDF remains provenance/corroboration only. R2-F does not claim raw PDF
bytes are retained, and future source-family expansion requires reacquisition and
a new review. Live web cannot override the retained source and is not a runtime
dependency.

## Product effect

Under hard exact `MILK_2_5` exclusion:

- current unaffected BREAKFAST-compatible pool: 2 / capacity 6;
- projected after cheese runtime: 3 / capacity 9;
- required BREAKFAST opportunities: 7.

The existing Planner mapping already permits `sandwich` for
BREAKFAST/LUNCH/SNACK, so no Planner change is required.

This is not a dairy-allergy claim: the selected cheese sandwich contains dairy.

See `docs/family-food/r2f-sandwich-resilience-gate.md`.
