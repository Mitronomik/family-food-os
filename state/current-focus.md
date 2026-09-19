# Current focus

Updated: `2026-09-19`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- Issue #47 / `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` = COMPLETE through merged PR #51.
- PR7 / Issue #53 = COMPLETE through merged PR #54.
- PR8 / Issue #57 = COMPLETE through merged PR #59.
- Post-PR59 state synchronization = COMPLETE through merged PR #60.
- Gate1-A audit/evidence baseline = COMPLETE through merged PR #63.
- Post-PR65 accepted main / DATA-CORPUS-V1 base:
  `9a76a97790b676f36c4c982af825721c3ef2c67e`.
- Accepted SQLite migration head: `0032_meal_plan_serving`.
- Future RecipeTemplate reservation remains `0033_recipe_template_catalogue`.

## Latest user-approved sequencing decision

The 2026-09-19 user decision supersedes the Gate1-only minimal-data strategy.

FamilyFoodOS will establish a reusable authoritative food + recipe corpus needed
by the service itself, then use verified subsets of that ordinary production
corpus for Gate1 and later gates.

Canonical contracts:

- `docs/family-food/data-corpus-v1.md`;
- `docs/family-food/master-roadmap-addendum-2026-09-19-data-corpus.md`;
- Issue #67.

## Current authorized operation

`DATA-CORPUS-V1 / DC0 — Contract and governance` is **ACTIVE** under Issue #67.

Goal:

- canonicalize source hierarchy;
- canonicalize normalized publication requirements;
- change sequencing before Gate1-CLOSE;
- synchronize state and agent routing.

DC0 is **docs/state only**.

No runtime, schema, migration or production catalogue publication is authorized
inside DC0.

## Relationship to Gate1-A-RU / Issue #64 / PR #66

Issue #64 remains historical Gate1-A-RU context.

Its minimal-eight-recipe publication strategy is superseded by Issue #67.

PR #66 must not merge in its current form. It may retain reusable fixture/source
mechanics, but its production truth must be rebuilt from accepted DATA-CORPUS-V1
publication batches or replaced by a fresh Gate1 delivery PR after corpus
readiness.

Gate1-CLOSE remains NOT STARTED.

PR9 remains NOT STARTED.

## DATA-CORPUS-V1 target

Coverage-first baseline:

- `50–80+` verified usable RecipeVersions;
- `100%` required FoodIngredient resolution for the active recipe corpus;
- authoritative nutrition provenance for every required production profile;
- exact food/form semantics under current Composition/Nutrition contracts;
- realistic weekly variety;
- Russian display readiness;
- deliberate progress toward approximately `250–350` FoodIngredient.

The count target must not be met by weak or unused filler foods.

## Source authority direction

- FIC/FGBUN material is a preferred Russian exact-authority candidate where
  identity/basis/version and retained-use scope are reviewable.
- FIC 2024 / the official database is not treated as an automatically open
  bulk-copy dataset; bulk retention requires a rights/use decision.
- USDA FoodData Central is an accepted open official baseline candidate where
  exact semantics match; open licensing does not authorize food-form substitution.
- manufacturer labels may establish exact product truth, not generic category
  truth by default.
- retailer pages, mirrors, snippets and secondary tables are corroboration/
  discovery by default.
- no LLM numeric authority; unknown != zero; no arbitrary cross-source merge.

## Active sequence

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         COMPLETE
→ PR7 MealPlan / Serving                     COMPLETE
→ PR8 Planner v0                             COMPLETE
→ Gate1-A audit/readiness baseline           COMPLETE
→ DATA-CORPUS-V1 / DC0                       ACTIVE (#67)
→ DC1 source authority + coverage inventory  NOT STARTED
→ DC2 food publication batches               NOT STARTED
→ DC3 recipe publication batches             NOT STARTED
→ DC4 readiness audit + Gate1 consumption    NOT STARTED
→ GATE1-CLOSE — Planning Core                NOT STARTED
→ PR9 Shopping Engine                        NOT STARTED
```

## Stop condition

After DC0 is review-ready/merged, stop.

Next authorized operation is DC1 under Issue #67.

Do not start DC2 production publication, Gate1-CLOSE, PR9, Retail, AI,
Auth/PostgreSQL or the generalized Data Ingestion Platform automatically.
