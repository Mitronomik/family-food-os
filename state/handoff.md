# Handoff

Updated: `2026-09-19`.

## Accepted base and governance

DATA-CORPUS-V1 / DC0 is COMPLETE through merged PR #68.

Accepted post-PR68 main:

`b1ce3e02394bad847f0c4063fe9faf520e208622`

Current bounded operation:

`DATA-CORPUS-V1 / DC1 — Source authority + coverage inventory` — ACTIVE under
Issue #67.

Accepted SQLite migration head:

`0032_meal_plan_serving`

Future RecipeTemplate reservation remains:

`0033_recipe_template_catalogue`

Gate1-CLOSE is NOT STARTED.

PR9 is NOT STARTED.

## Closed superseded work

PR #66 — `feat: publish minimal Russian corpus for Gate1 planning` — was closed
without merge on 2026-09-19.

Reason:

- its minimal-eight Gate1-only strategy was superseded by the accepted
  DATA-CORPUS-V1 contract;
- its ten proposed profiles were selected to satisfy one fixture and require
  re-evaluation under the new authority/provenance policy;
- closing the PR accepts none of its production data.

Its branch remains available as historical implementation evidence.

Potentially reusable mechanics:

- source snapshot/hash fail-closed validation;
- idempotent publication structure;
- Gate1 Planner fixture structure;
- persisted complete-week/Serving assertions.

Do not reuse its proposed nutrition/profile facts as accepted truth.

## DATA-CORPUS-V1 canonical direction

```text
authoritative sources
→ FoodIngredient / Nutrition / Composition
→ source-backed recipe corpus
→ ingredient resolution
→ deterministic recipe nutrition
→ reusable production RecipeVersion catalogue
→ Gate1 and later gates
```

Canonical docs:

- `docs/family-food/data-corpus-v1.md`;
- `docs/family-food/master-roadmap-addendum-2026-09-19-data-corpus.md`;
- Issue #67.

## DC1 task

Build the coverage/authority matrix that determines what production data is
actually worth publishing.

Required matrix concept:

```text
recipe/source variant
→ source ingredient
→ accepted/existing mapping
→ canonical FoodIngredient/form
→ authoritative nutrition source/status
→ rights/use status
→ mass/form/process blockers
→ publication disposition
```

Required DC1 outputs:

1. initial `50–80+` useful recipe candidates;
2. exact selected source variants/branches;
3. deduplicated required FoodIngredient/form demand;
4. explicit reuse of current accepted FoodIngredient/profile truth;
5. authoritative source assignment/status for each missing demanded form;
6. rights/use classification;
7. exact unresolved blocker inventory;
8. proposed small DC2 food batches;
9. proposed small DC3 recipe batches.

## Evidence rules

- no LLM numeric truth;
- unknown != zero;
- estimate != exact;
- raw/input/cooked forms are not interchangeable;
- do not merge nutrients across unrelated sources into a false exact profile;
- do not select a recipe alternative only because it is easier to map;
- source-declared recipe totals are review evidence by default, not production
  Nutrition authority;
- FIC/FGBUN may be preferred for Russian exact forms only where identity,
  basis/version and retained-use scope are reviewable;
- FIC public materials are not automatically treated as an open bulk licence;
- USDA FoodData Central is an accepted open official candidate when exact form
  semantics match;
- manufacturer/retailer evidence does not establish a generic profile by default.

## Scope boundary

DC1 is evidence/curation only.

No broad production FoodIngredient/Nutrition/Composition/RecipeVersion publication
belongs in DC1.

No schema/migration change is expected.

DC2/DC3 production work starts only as separately reviewable batches after the
DC1 package identifies exact demand and authority.

## Verification expectation

DC1 should verify:

- source existence and exact source identity;
- source release/version/date;
- rights/use disposition;
- duplicate/mapping consistency;
- food/form semantics;
- quantity/mass-state coverage;
- recipe candidate coverage and variety;
- explicit unresolved inventory;
- reproducible batch-selection rationale.

Do not claim production/runtime regression for evidence-only changes unless the
implementation surface actually changes.

## Stop condition

After DC1 is review-ready/merged, stop.

Do not automatically start DC2, DC3, DC4, Gate1-CLOSE or PR9.
