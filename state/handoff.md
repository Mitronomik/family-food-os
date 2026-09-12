# Handoff

Updated: `2026-09-12`

PR #27 is MERGED, not review-pending. Exact fetched starting main and merge commit:
`d5b5ce3fdc4ec79de5454b3ed23b1d527772c0bc`. GitHub merged state verified through the
GitHub connector. Branch: `codex/pr6-ru-food-data`. Migration remains
`0029_food_composition_core`; no schema change.

PR6-RU-FOOD-DATA is the current explicitly authorized operation. Its
[version 1 evidence package](../data/curation/pr6-ru-food-data/README.md) is bounded
to 81 existing food codes and seven form candidates. 60 food-data records are
RU_READY, 28 NOT_READY. RU_AVAILABLE does not independently permit default use;
only three records pass the separate food/market default gate. Sparse nutrients,
preparation, kitchen and later recipe gates remain independently required.

Promoted: CAULIFLOWER_FROZEN (SR 170398) and
STRAWBERRY_FROZEN_UNSWEETENED (SR 168173), both April 2018 release. Each adds one
profile and seal with 33 exact positive mapped source values. Fresh official Lenta
food-form evidence plus official SPB/LO presence supports RU_AVAILABLE.
Deferred: APPLE_PEELED and PASTA_COOKED (no exact purchase form or reviewed
preparation/output path); SPINACH_BABY (primary market form proof unestablished);
LEMON_JUICE / ORANGE_JUICE (unapproved FNDDS generic/default/blend and mappings).
Five SR/Foundation source extracts were revalidated against redownloaded official
archive hashes. FNDDS proposals remain research. PR4 reused evidence keeps its date.

Seed/import: `app.seed.ru_food_data` is a separate explicit operation after the
accepted food/recipe/B1/B2-A chain. Fixed package hashes, protected source hashes,
deterministic gates and exact profile provenance resolve local IDs. One project
UoW publishes profiles, sparse vectors and 60 ATOMIC versions. Seals/snapshots are
append-only. Repeat import inserts zero and leaves database contents identical.
Historical v1 backfill policy is unchanged; no current-profile selector is used
for composition replay. Rollback of a failed run is transactional; successful
operational recovery restores a pre-seed backup rather than deleting history.

Existing 183 foods/profiles/seals, all recipe versions/rows and B1/B2-A bindings
are unchanged. Complete readiness reports match, including all 43 non-executable
estimates. No new COMPOSITE/transformation/yield/retention rows, API/UI, Retail
runtime or AI dependency. Synthetic tests are excluded from production counts.

All required verification is green: full backend + launcher 3799 passed with
AI_ENABLED=false, focused 41, affected 311, migration/backup 154; source replay,
audits, Ruff/format and affected-runtime mypy pass. Exact commands/results are in
[progress](progress.md). Status: REVIEW-READY. Next action: review the bounded PR
against main, including the two promotions and five deferrals; merge requires
explicit post-review authorization. CLI HTTPS/SSH authentication is unavailable;
delivery uses the authenticated GitHub connector with verified Git blob/tree hashes.
Unrelated local `.DS_Store` remains excluded.

**PR6 remains NOT COMPLETE.** No autonomous merge. After reviewed merge, the next
roadmap candidate is PR6-DATA-B2-B2-REDESIGNED, requiring separate authorization.
Do not start it, Recipe Assembly or PR7+ automatically.
