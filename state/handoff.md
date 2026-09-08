# Handoff

Updated: `2026-09-08`

PR6 engine and DATA-A are ACCEPTED / MERGED. B1 and PR6-INFRA are established.
B2-A starts exactly at accepted main `74bc80eb3ef0e34e17751856638ac58bbccb840e`
on `data/pr6-b2a-source-quantity-corrections`. The branch was fast-forwarded;
the unrelated local `.DS_Store` modification was preserved and excluded.

This changeset establishes same-source immutable RecipeVersion revisions and all
six reviewed quantity corrections. Five recipes have v1→v2 parent chains with
identical external provenance. Migration 0027 rebuilds only RecipeVersion under
the PR6-INFRA runner. Original PR4/B1 payloads and all historical rows survive;
their loaders explicitly find historical matching v1 after publication.

Separate B2-A correction and assessment loaders add five versions, 32 ingredient
rows and 32 explicit assessments; no runtime authority inherits from v1. Audit v3
covers 30 current recipes / 189 rows, all INCOMPLETE. All six quantity findings are
resolved; independent form/profile and conversion blockers remain.

Source interpretation (including primary 1 1/2 apples versus permitted variation),
assessment decisions and import/replay commands:
[B2-A decision](../docs/family-food/nutrition-data-readiness.md#decision--pr6-data-b2-a-same-source-quantity-corrections).
Executed verification: [progress](progress.md#pr6-data-b2-a-verification).

PR6 remains NOT COMPLETE. B2-B remains NOT AUTHORIZED; PR7+ remain UNAUTHORIZED.
No estimated conversion is accepted, no form/profile repair starts, and no
separate B2-A-CLOSE operation is required. No later work is authorized here.
