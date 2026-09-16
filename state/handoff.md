# Handoff

Updated: `2026-09-16`.

Accepted `main` after merged PR #45 is
`e87583b440e7121623622331c0fa136953bdc122`.

## Latest user-approved decision

On 2026-09-16 the user corrected the product/data direction:

- the current technical ingredient/recipe/nutrition datasets and seed corpora are external replaceable bootstrap/evidence artifacts; FamilyFoodOS is not architected around them;
- deterministic Recipe Constructor / Recipe Assembly remains valuable;
- mandatory personal cooking/kitchen execution is not a publication or Planning Core prerequisite;
- constructed recipes are validated through deterministic checks plus web corroboration against relevant external recipes;
- web evidence compares normalized recipe identity, ingredient sets/ratios, yield/servings where available and key method/process, without copying external prose;
- default corroboration requires at least two independent relevant sources unless an explicitly reviewed high-trust single-source policy applies;
- `KITCHEN_TESTED` is optional extra evidence; future real-household use may produce `USER_VALIDATED` evidence.

Canonical durable decision is being recorded in:

`docs/family-food/master-roadmap-addendum-2026-09-16.md`

## Effect on previous Assembly work

PR #31–#45 remain accepted historical research/evidence. Their earlier
`HUMAN_EVIDENCE_BLOCKED__2_OF_3` result accurately records the old mandatory-kitchen policy, but that policy no longer blocks the service roadmap after the new user decision.

Do not delete or rewrite those evidence packages to pretend the old decision never existed.

## Active sequence after governance merge

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE
→ PR7 MealPlan / Serving
→ PR8 Planner v0
→ GATE 1 — Planning Core
```

Recipe Constructor / Assembly becomes a separately scoped capability and may be implemented later/in parallel only when separately authorized. It must not force PR7/PR8 to wait for physical kitchen evidence.

## Current branch boundary

The current operation is docs/governance synchronization only:

- record dataset independence;
- record deterministic + web-corroborated Recipe Constructor validation;
- supersede mandatory kitchen verification as a roadmap gate;
- point agents/state to the corrected software critical path.

No runtime/schema/data-promotion changes belong in this PR.

After review/merge, the next authorized software operation is
`PR7-SUPPORT-MEAL-PATTERN-CATALOGUE`.

Do not start Retail, AI Gateway, Auth/shared deployment or unrelated catalogue expansion automatically.
