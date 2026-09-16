# Current focus

Updated: `2026-09-16`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- PR #31–#45 = MERGED as accepted research/governance history.
- Exact accepted `main` after PR #45: `e87583b440e7121623622331c0fa136953bdc122`.
- Current accepted SQLite migration head: `0030_recipe_source_corpus`.
- Future RecipeTemplate schema reservation remains `0031_recipe_template_catalogue` unless a later implementation decision changes the migration plan.
- R1 / R2 / R3 / R4 and later Assembly-A recovery packages remain accepted historical research.
- The earlier `HUMAN_EVIDENCE_BLOCKED__2_OF_3` state describes the old mandatory-kitchen-validation policy and no longer blocks Planning Core under the 2026-09-16 user-approved decision.

## Current authorized governance decision

The user explicitly approved two corrections on 2026-09-16:

1. technical ingredient/recipe/nutrition datasets and seed corpora are replaceable external bootstrap/evidence artifacts; FamilyFoodOS must not be designed around their schemas, counts or source-specific identities;
2. deterministic Recipe Constructor / Recipe Assembly remains desirable, but mandatory personal kitchen execution is replaced by deterministic validation plus web corroboration for constructed-recipe publication.

Canonical decision draft:

`docs/family-food/master-roadmap-addendum-2026-09-16.md`

The decision preserves provenance, rights, mass/form, Nutrition uncertainty, Russian display and `AI_ENABLED=false` rules. Web sources provide validation evidence; they are not Planner runtime dependencies and are not permission to copy external recipe prose.

## Recipe Constructor validation direction

Constructed candidates use:

```text
constructor/template rules
→ deterministic structural/data validation
→ external recipe discovery
→ normalized ingredient/ratio/yield/method comparison
→ WEB_CORROBORATED / REVIEW_REQUIRED / REJECTED
```

Default corroboration requires at least two independent relevant external recipes. A single-source exception requires an explicit reviewed high-trust policy.

`KITCHEN_TESTED` becomes optional additional evidence, not a roadmap prerequisite. Future `USER_VALIDATED` evidence may accumulate from real household use.

## Roadmap correction

Recipe Assembly research PR #31–#45 remains immutable historical evidence but is removed as a blocking prerequisite for Planning Core.

After review/merge of the current governance/docs PR, the next software operation is:

`PR7-SUPPORT-MEAL-PATTERN-CATALOGUE`

Then:

```text
PR7-SUPPORT-MEAL-PATTERN-CATALOGUE
→ PR7 MealPlan / Serving
→ PR8 Planner v0
→ GATE 1 — Planning Core
```

Recipe Constructor / Assembly may proceed later or in separately authorized bounded PRs without forcing PR7/PR8 to wait for physical kitchen evidence.

## Current authorization boundary

This branch is docs/governance only. Do not implement runtime/schema/data promotion as part of this PR.

Do not start Retail, AI Gateway, Auth/shared deployment, bulk catalogue expansion or unrelated milestones automatically.

After this decision PR is reviewed and merged, `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` is the next authorized software operation; PR7 itself starts only after that support operation is accepted according to the roadmap/addenda.
