# Current focus

Updated: `2026-09-20`.

## Accepted state

PR72 is merged at `0322d0a74a0edf53802adc394446011a7d8acc06`.
PR73 contains the bounded `dc2-exact-input-v1` evidence review for exact
School2022 input forms and mass safeguards. On 2026-09-20 the user explicitly
authorized correction of all PR73 blockers and completion of this bounded review.
This does not authorize merge, production publication or the next milestone.

SQLite head remains `0032_meal_plan_serving`; reserved
`0033_recipe_template_catalogue` remains unchanged.

## Current authorized boundary

The PR73 exact-input review package is complete/review-ready:

- 211 source occurrences across sugar, carrot, cabbage, beet and polished rice;
- four execution routes remain held because two source rows are suspicious;
- canonical FoodIngredient IDs remain unassigned;
- nutrient equivalence and calculation readiness remain false;
- retained fraction remains unknown;
- source net mass remains normative accounting evidence, not certified physical
  pre-heat mass;
- School2022 §1.5 heat-loss semantics are recorded separately in
  `source-nutrition-policy.json` and grant no canonical retention authority.

See [exact mappings](../data/curation/dc2-exact-input-mappings/README.md).

Review/merge of this evidence package does not authorize a DC2 production
publication payload.

## Stop boundary

After PR73 review/merge, stop pending explicit scope for exact canonical
FoodIngredient/profile equivalence, nutrient-method decisions, source reuse
scope and an independently reviewed DC2 publication payload through existing
profile/vector/ATOMIC contracts.

Do not start DC3, DC4, Gate1-CLOSE, PR9/Shopping, Retail, AI,
Auth/PostgreSQL, schema migration or generalized ingestion automatically.
