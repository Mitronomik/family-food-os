# Handoff

Updated: `2026-09-19`.

## Accepted base and governance

Accepted main before DATA-CORPUS-V1 governance:

`9a76a97790b676f36c4c982af825721c3ef2c67e`

Current bounded operation:

`DATA-CORPUS-V1 / DC0 — Contract and governance` — ACTIVE under Issue #67.

Accepted SQLite migration head:

`0032_meal_plan_serving`

Future RecipeTemplate reservation remains:

`0033_recipe_template_catalogue`

Gate1-CLOSE is NOT STARTED.

PR9 is NOT STARTED.

## User decision that changed sequencing

On 2026-09-19 the user explicitly chose to stop optimizing catalogue truth only
for Gate1.

New direction:

```text
build reusable authoritative corpus
→ publish normal production FoodIngredient/Nutrition/RecipeVersion truth
→ audit readiness
→ use ordinary corpus subsets for Gate1 and later gates
```

This supersedes the minimal-eight-recipe strategy in Issue #64 / current PR #66
to the extent they limited catalogue work only to Gate1 needs.

Canonical details:

- `docs/family-food/data-corpus-v1.md`;
- `docs/family-food/master-roadmap-addendum-2026-09-19-data-corpus.md`;
- Issue #67.

## Relationship to PR #66

PR #66 is not mergeable in its current form.

Its ten new profiles were selected to satisfy the old minimal Gate1 subset and
include authority/provenance choices that the new corpus program must re-evaluate.

Do not use #66 as production truth.

Reusable mechanics may later be recovered:

- immutable selected-source snapshot/hash validation;
- deterministic publication/idempotency structure;
- Planner fixture structure;
- persisted-week/Serving proof.

Underlying food/profile/recipe truth must come from accepted DATA-CORPUS-V1
batches.

## DATA-CORPUS-V1 phases

### DC0 — current

Docs/governance only:

- canonical corpus contract;
- roadmap addendum;
- current-focus/handoff sync;
- AGENTS routing;
- source authority policy.

### DC1 — next after reviewed merge

Evidence/curation:

- select initial `50–80+` useful recipe candidates;
- preserve exact source variants;
- build deduplicated canonical food/form demand;
- reuse current mappings/production profiles;
- assign authoritative sources;
- record rights/use state;
- identify exact blockers;
- propose small DC2/DC3 batches.

No invented values and no production publication in DC1 unless a separate
bounded production authorization is created.

### DC2 / DC3

Small reviewable production batches:

- DC2: authoritative FoodIngredient/Nutrition/NutrientVector/ATOMIC Composition;
- DC3: source-backed RecipeVersion resolution/publication.

No one giant import.

### DC4

Corpus readiness audit, then Gate1 fixture selection from ordinary production
catalogue truth.

## Authority notes

FIC/FGBUN 2024/reference database is a preferred Russian authority candidate,
but current public materials are not treated as an open bulk-data licence.
Record rights/use before bulk retention.

USDA FoodData Central is an accepted open official baseline candidate where exact
food/form semantics match.

Retail/mirror/secondary sources are corroboration by default.

The project still forbids:

- LLM numeric truth;
- unknown → zero;
- estimate → exact;
- arbitrary food/form substitution;
- hidden raw/cooked mass equivalence;
- arbitrary cross-source nutrient merging.

## Verification for DC0

Per `verification-policy.md`, DC0 is docs/state only.

Required before review-ready:

- stale-state/link audit;
- exact changed-file scope audit;
- diff whitespace checks;
- no runtime/schema/data claim.

No backend regression is required solely for DC0.

## Stop condition

After DC0 review/merge, stop.

Proceed only to DC1 under Issue #67.

Do not automatically start production data batches, Gate1-CLOSE or PR9.
