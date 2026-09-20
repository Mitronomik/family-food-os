# Current focus

Updated: `2026-09-20`.

## Accepted state

PR73 is merged at `a9472c2a0bb0534b70b41c541aa0ac9b4cb26ba0`.
PR74 contains the bounded five-profile preparation/evidence review. On
2026-09-20 the user explicitly authorized correction of all PR74 blockers and
completion of this bounded review. This does not authorize merge, source reuse,
the proposed profile/schema design, a migration or production publication.

SQLite head remains `0032_meal_plan_serving`; reserved
`0033_recipe_template_catalogue` remains unchanged.

## Current authorized boundary

The PR74 preparation/evidence package is complete/review-ready:

- five exact Book2002 source records are selected from accepted review metadata;
- repository-verifiable source states are 60 observations:
  45 `published_positive` and 15 `below_detection`;
- all five retain a source-native carbohydrate incompatible with the current
  mandatory legacy `FoodNutritionProfile.carbohydrates_g` projection;
- sugar additionally has below-detection protein and fat;
- canonical nutrient values imported: 0;
- production profiles imported: 0;
- source reuse remains `BLOCKED_PENDING_RIGHTS_REVIEW`;
- no outbound rights request was sent;
- no database write is claimed or performed by the compatibility probe;
- external numeric payload and A/B full-build hashes are not retained in the
  repository and are explicitly not merge acceptance evidence.

See [profile payload preparation](../data/curation/dc2-first-profile-payload/README.md),
[verification receipt](../data/curation/dc2-first-profile-payload/verification-receipt.json)
and [profile compatibility proposal](../data/curation/dc2-first-profile-payload/profile-compatibility-proposal.md).

The compatibility proposal remains **proposed / decision required**. Review or
merge of PR74 does not accept an unknown-macro profile contract or migration.

## Stop boundary

After PR74 review/merge, stop for an explicit architecture decision on the
profile/unknown-macro representation and migration strategy, plus a separate
source-reuse decision. Only after those decisions may a separately authorized
DC2 production publication implementation begin.

Do not start a migration, production publication, DC3, DC4, Gate1-CLOSE,
PR9/Shopping, Retail, AI, Auth/PostgreSQL or generalized ingestion automatically.
