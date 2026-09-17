# Handoff

Updated: `2026-09-17`.

## Accepted base and governance

PR #51 is MERGED and Issue #47 is CLOSED / COMPLETED.

Accepted `main`:

`0648d9483bd9261451194668c274b3c08ad716b3`

Accepted SQLite migration head:

`0031_meal_pattern_catalogue`

The 2026-09-16 addendum remains canonical for external-dataset independence and Recipe Constructor web-corroboration policy. The later post-PR51 sequencing/migration decision is:

`docs/family-food/master-roadmap-addendum-2026-09-17-post-pr51.md`

PR #31–#45 remain historical evidence and must not be rewritten to hide the old policy.

## Completed supporting operation

`PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` / Issue #47 is COMPLETE through merged PR #51.

It established:

- platform-owned immutable/versioned `MealPatternProgram` catalogue truth;
- deterministic publication validation and lifecycle behavior;
- Russian display/explanation requirements;
- structured age/eligibility and safety behavior;
- ordered semantic meal opportunities with repeatable roles by position;
- provenance/evidence and review metadata;
- synchronous SQLAlchemy Core repository/UoW persistence;
- migration `0031_meal_pattern_catalogue`;
- small reviewed adult-only (19+) wellness/schedule seed;
- explicit unsupported behavior for children without separately approved age-specific program evidence.

The initial catalogue size is evidence scope, not an architecture invariant.

## Current operation

`POST-PR51-STATE-SYNC` is docs/state only.

Branch: `docs/post-pr51-state-sync`.

No runtime, schema, seed, API, frontend or behavior change belongs in this operation.

The sync records the approved migration reservation:

```text
0030_recipe_source_corpus
→ 0031_meal_pattern_catalogue
→ 0032 <reserved for PR7 MealPlan / Serving>
→ 0033_recipe_template_catalogue <future reservation only>
```

No existing migration history is rewritten. The exact `0032` migration suffix will be chosen only inside the future authorized PR7 implementation task.

## Next functional milestone

`PR7 — MealPlan / Serving` is **NEXT / NOT STARTED** and requires separate explicit user authorization after this state-sync PR is merged.

Before PR7 implementation, read in repository order:

1. `AGENTS.md`;
2. `state/current-focus.md`;
3. `docs/family-food/master-roadmap.md`;
4. `docs/family-food/master-roadmap-addendum-2026-09-13.md`;
5. `docs/family-food/master-roadmap-addendum-2026-09-16.md`;
6. `docs/family-food/master-roadmap-addendum-2026-09-17-post-pr51.md`;
7. `docs/family-food/meal-pattern-programs.md`;
8. `docs/family-food/architecture-addendum-2026-09-13.md`;
9. relevant scoped `AGENTS.md`, implementation patterns and tests.

PR7 boundaries already fixed by canonical contracts:

- `MealPatternProgram` is platform-owned; `MemberMealPatternSelection` is Household-owned;
- exact published program version or `CUSTOM` must be representable;
- heterogeneous member schedules are required;
- one to six opportunities must be representable without a permanent database-law maximum of six;
- `MealRole != RecipeVersion.meal_type_code`;
- shared household events may have individualized Servings;
- Nutrition Engine owns nutrient truth;
- PR8 owns Planner ranking/recommendation/reconciliation automation;
- deterministic core works with `AI_ENABLED=false`.

## Stop conditions

Do not begin PR7 merely because this sync is review-ready or merged. Wait for explicit user authorization.

Do not pull forward Planner ranking, Shopping, Prep, Retail, AI Gateway, Auth/shared deployment, frontend/onboarding or Recipe Constructor/Assembly implementation.