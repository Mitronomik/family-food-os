# Current focus

Updated: `2026-09-20`.

## Accepted state

PR75 is merged at `33659866348bbc56d705bb764bb3c864c2cce0be`.

The user approved the ten-step Russian-data integration sequence:

`partial profile storage → registry/adapters → transactional publication → first
Russian food batch → Russian reference table → persisted methodology selection →
transformation applicability → recipe-dependency food batch → executable Russian
recipes → Planner integration`.

Current bounded work is step 1: partial nutrition-profile storage.

## Current authorized boundary

The partial-profile implementation:

- permits explicit unavailable legacy kcal/protein/fat/carbohydrate values;
- persists source-observation states without converting unknown to zero;
- distinguishes `value`, `missing`, `below_detection` and
  `method_incompatible`;
- preserves source literal, method reference and locator;
- keeps partial profiles non-current under the legacy selector;
- does not auto-create a V1 NutrientVector seal for a partial profile;
- preserves all accepted complete profile IDs/values, vector seals and ATOMIC
  references;
- uses the existing SQLite custom migration runner;
- implements migration `0034_partial_nutrition_profiles`;
- leaves reserved `0033_recipe_template_catalogue` unused.

Migration ordering is forward-only. If the reserved `0033` is implemented later,
its module must be appended after already accepted `0034` in
`MIGRATION_MODULES`; inserting it before `0034` would invalidate the exact
prefix history of upgraded databases.

No Russian production profile is published in this PR. Source-use status remains
unchanged.

## Acceptance

Review-ready requires:

- partial profile round-trip with SQL NULL, never invented numeric zero;
- immutable source observations;
- old current profile selector unchanged;
- old Nutrition/NutrientVector/Composition behavior unchanged;
- populated 0032 database upgrade preserving profile/vector identities;
- actual migration failure rollback;
- backup copy restore and successful re-upgrade;
- focused migration/vector tests;
- full backend regression;
- full launcher regression;
- `AI_ENABLED=false`.

## Stop boundary

After review/merge, stop before step 2: the new nutrient-registry/adapters version.

Do not start transactional profile publication, production Russian food
publication, target-table publication, Planner/API/UI methodology enablement,
DC3, DC4, Gate1-CLOSE or PR9 automatically.
