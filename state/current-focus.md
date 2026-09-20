# Current focus

Updated:2026-09-20. Accepted main base:
`a9472c2a0bb0534b70b41c541aa0ac9b4cb26ba0` (PR73).

The user explicitly approved Russian calculation/accounting methodologies and
adaptation of the rest of the nutrition chain. Current bounded implementation:
versioned Russian methodology domain and internal service operations.

Implemented: source-native available carbohydrates with method preservation;
strict/explicit published-zero-estimate policies; held/missing distinction;
MR2021 appendix3 energy component accounting; reviewed group-reference selector;
unit/definition-safe comparison; pinned ATOMIC/vector read integration and
household-scoped optional Russian reference service.

See [methodology contract](../docs/family-food/russian-nutrition-methodologies.md).
322 affected/new regression tests pass; real SQLite read path and AI=false tested.
Five locked Russian source profiles were evaluated under both policies locally;
no book numbers published in Git and no canonical profiles imported.

PR74 remains a separate open preparation PR; this branch starts directly from
accepted main. Do not assume PR74 merged or changes profile representation.

Remaining authorized dependencies: partial-profile persistence and new registry
version, publication/review of exact Russian reference rows and food profiles,
then explicit methodology selection in Planner/API/UI. These are not enabled by
this internal calculation-layer PR. Existing V1 defaults/history and schema0032
remain unchanged;0033 stays reserved. No clinical, Retail or live production
publication. Stop for PR review; no autonomous merge.
