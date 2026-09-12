# Handoff

Updated: `2026-09-12`

PR6-NUTRIENT-VECTOR-A is merged in PR #25 at
`e35d87a24d5d8afb59509e566aa1ff4b7a58a11a`. The user separately authorized
PR6-NUTRIENT-VECTOR-B. Branch: `codex/pr6-nutrient-vector-b`; implementation is verified and ready for review. Main was fetched and matches the task SHA.

The [concrete contract](../docs/family-food/nutrition-core.md#pr6-nutrient-vector-b--normalized-immutable-snapshots)
describes migration 0028, immutable registry evidence, sparse Decimal values,
deferred seal FK, triggers, complete reads and unaudited-profile handling.
Existing FoodNutritionProfile remains the single profile/version container.
Nutrition v1 consumers are unchanged; no API/UI or future-context work is included.

The [reproducible audit](../data/curation/pr6-nutrient-vector-b/README.md) measures
51 definitions / 183 profiles / 806 values. All 64 unresolved source zeros are
retained in evidence and v1 and omitted from exact normalized values. All 45
absent observations remain unknown. Every pre-existing table row, profile ID,
current flag and B1 binding remains unchanged. Readiness is 30 recipes / 189 rows /
30 INCOMPLETE; current statuses 66/21/37/65; 43 estimates remain non-executable.
The older 20/66 counts were B1-era context, superseded by accepted B2-A.

Use `backend/.venv/bin/python`; root Python lacks the project SQLAlchemy runtime.
VECTOR-A current content validation uses `--content-only`. Tests execute old
research-only scope guards in disposable clones at each accepted research SHA;
all content/provenance/zero-gate checks still run on current artifacts.
Full backend/launcher regression: **3699 passed in 593.83s**, no skips,
`AI_ENABLED=false`. Lint/format, mypy, upgrade/provenance/readiness audits PASS.
[PR #26](https://github.com/Mitronomik/family-food-os/pull/26) is open, ready for final review.
Implementation commit: `265aa247726d7520a7914d16ecabe6c607419f34`.
Next action: review this PR; do not merge without explicit post-review authorization.
Executed checks: [progress](progress.md#pr6-nutrient-vector-b-verification).

Unrelated tracked `.DS_Store` modification is preserved and excluded from delivery.
No real-user/developer database was opened or mutated; all evidence uses temporary
seeded SQLite databases. Migration fails atomically on extra unaudited existing
profiles; do not invent an audit or silently skip them. New unaudited v1 profiles
remain without a readable vector. Future enrichment is not authorized.

PR6 remains NOT COMPLETE. No autonomous merge. Composition Core requires its own
authorization after this PR is reviewed and merged; do not start it now.
