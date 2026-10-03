# R2-F sandwich resilience-closure contract evidence

Issue: #139.

Accepted main: `561c13aad6ce978de399dfd807071232af06b71c` (merged PR #138).

R2-F is one **two-recipe** Contract Gate, not another single-recipe micro-step.

Selected future runtime candidates:

- `SAD28_SANDWICH_BUTTER_25_5` — Бутерброд со сливочным маслом — 30 g / 66.3 kcal;
- `SAD28_SANDWICH_CHEESE_20_10` — Бутерброд с сыром — 30 g / 83 kcal.

Both are `sandwich` RecipeVersions and therefore use the already accepted Planner
compatibility for BREAKFAST/LUNCH/SNACK. No Planner mapping change is proposed.

New identity-only FoodIngredients:

- `WHEAT_BREAD_PLAIN`;
- `BUTTER_CREAM_UNSPECIFIED`;
- `CHEESE_UNSPECIFIED`.

No Nutrition or Composition authority is granted to those identities.

Source authority is deliberately bounded to the two reviewed institution-published
cards through `BOUNDED_INSTITUTION_PUBLISHED_TECH_CARD_REVIEW_V1`. Runtime must pin the reviewed derivative in
`source-cards.json`; it must not depend on live web access or treat the whole PDF
as auto-approved production truth.

Projected exact-`MILK_2_5` resilience after future runtime publication:

- current unaffected BREAKFAST-compatible pool: 2 / capacity 6;
- projected unaffected pool: 4 / capacity 12;
- required seven BREAKFAST opportunities: feasible with unchanged repetition=3.

This is not a dairy-allergy claim: the selected recipes contain butter/cheese.

See `docs/family-food/r2f-sandwich-resilience-gate.md`.

## Public source verification

`public-source-verification.json` records the 2026-10-03 independent public
recheck of the official institution nutrition page and the indexed
technological-card PDF text for both selected cards.

R2-F does not claim retained raw PDF bytes. Runtime source truth is the committed
reviewed derivative `source-cards.json`; live web access is provenance/audit
corroboration only and cannot override the derivative.
