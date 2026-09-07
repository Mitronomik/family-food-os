# Handoff

Updated: `2026-09-07`

PR6 engine (#18) and DATA-A (#19) are ACCEPTED / MERGED. B1 is established by
PR #20, merged at `2ce9917f51ac3161d4cb2839f6003e7a24bc96bd`.

PR6-INFRA starts from that exact base on `infra/sqlite-rebuild-migration-runner`.
This changeset establishes explicit SQLite `foreign_key_rebuild` migration mode.
The runner owns the FK toggle, transaction, marker, pre-commit whole-database
validation and FK restoration. Earlier completed migration work is committed
before the special migration; failures leave a valid, resumable prefix.

Canonical lifecycle, module restrictions and restoration-failure semantics:
[architecture §13.1](../docs/family-food/architecture.md#131-sqlite-foreign-key-table-rebuild-capability-pr6-infra).
Executed verification: [progress](progress.md#pr6-infra-verification).

Migration head stays `0026_nutrition_measure_evidence`. Historical migrations,
production schema and accepted catalogue/research/seed bytes are unchanged.
No production rebuild migration exists in this operation; tests use synthetic
modules only. B1 remains 57 evidence / 189 assessments / 123 issues across
30 v1 RecipeVersions / 189 ingredient rows; estimates remain non-executable.

PR6 remains NOT COMPLETE. B2-A is the next separately authorized product/data
operation and must start from accepted main containing this capability. B2-B
remains NOT AUTHORIZED; PR7+ remain UNAUTHORIZED. No INFRA-CLOSE is required.
