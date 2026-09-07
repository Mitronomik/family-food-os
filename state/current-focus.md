# Current focus

Updated: `2026-09-07`

## Accepted implementation and supporting operations

- **PR6 engine — ACCEPTED / MERGED**, PR #18 at
  `7c449672c039c66b8d475064462eba2a9f6d38e6`.
- **PR6-DATA-A — ACCEPTED / MERGED**, PR #19 at
  `60908eb8270ef356eff8552855b4cc5d2aa9ee44`.
- **PR6-DATA-B1 — established**, PR #20 merged at
  `2ce9917f51ac3161d4cb2839f6003e7a24bc96bd` (exact PR6-INFRA base).
- **PR6-INFRA — SQLite runner supports explicit FK table-rebuild mode by this
  changeset**. Authorization covers this infrastructure capability only; no
  production migration or schema/data change. No separate INFRA-CLOSE is needed.
- **PR6 milestone — NOT COMPLETE**. PR5 remains COMPLETE.
- **PR6-DATA-B2-A — next separately authorized product/data operation**; it must
  start from accepted `main` containing this runner capability. Its migration,
  source review, RecipeVersion corrections and assessments are outside PR6-INFRA.
- **PR6-DATA-B2-B — NOT AUTHORIZED**. PR7+ remain UNAUTHORIZED.

Migration head remains `0026_nutrition_measure_evidence`. The 30 v1 recipes /
189 ingredient rows and B1 57 evidence / 189 assessments / 123 issues are
unchanged. All 43 estimates remain non-executable.

Runner lifecycle and resumability:
[architecture §13.1](../docs/family-food/architecture.md#131-sqlite-foreign-key-table-rebuild-capability-pr6-infra).
Verification: [progress](progress.md#pr6-infra-verification).
Nutrition decisions remain in
[nutrition data readiness](../docs/family-food/nutrition-data-readiness.md) and
[Nutrition Core](../docs/family-food/nutrition-core.md).
