# Current focus

Updated: `2026-09-08`

- **PR6 engine — ACCEPTED / MERGED**, PR #18.
- **DATA-A — ACCEPTED / MERGED**, PR #19; historical findings remain intact.
- **B1 — established**, PR #20: protected 57 evidence / 189 assessments / 123 issues.
- **PR6-INFRA — established**, PR #21 at
  `74bc80eb3ef0e34e17751856638ac58bbccb840e`, the exact B2-A starting base.
- **B2-A — same-source revision capability and all six reviewed source-quantity
  corrections established by this changeset**. Five recipes receive immutable
  v2 and 32 new explicit assessments; 25 recipes remain on v1.
- Migration head: `0027_recipe_same_source_revisions`, using the established
  `foreign_key_rebuild` runner mode. PR4 and B1 seed bytes remain unchanged and
  resolve their historical v1 rows after v2 publication.
- Audit v3: 30 current versions / 189 current rows; all 30 INCOMPLETE. All 43
  estimated candidates remain non-executable. No form/profile repair started.
- **PR6 — NOT COMPLETE; B2-B — NOT AUTHORIZED; PR7+ — UNAUTHORIZED.**
  No separate B2-A-CLOSE operation exists and this changeset grants no later scope.

Durable source decisions and exact counts:
[nutrition data readiness](../docs/family-food/nutrition-data-readiness.md#decision--pr6-data-b2-a-same-source-quantity-corrections).
Migration/repository contract:
[architecture §13.2](../docs/family-food/architecture.md#132-same-source-recipeversion-revisions-pr6-data-b2-a).
Executed verification: [progress](progress.md#pr6-data-b2-a-verification).
