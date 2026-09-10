# Handoff

Updated: `2026-09-10`

PR6-NUTRIENT-VECTOR-A establishes registry/provenance research only from exact
main `307ba3475581087b079ebcf2fa643e19a00bf06d` (PR #24 merged).
Branch: `data/pr6-nutrient-vector-a-registry`. Next action is VECTOR-A final review.
Do not autonomously merge, start VECTOR-B or implement any schema/runtime.

The [complete report](../data/curation/pr6-nutrient-vector-a/README.md) contains
the 51-entry Russian registry, source manifests/hashes, 140 FDC mappings, all
915 legacy field observations and VECTOR-B recommendations. Key facts: 183
accepted profiles across history (0 historical-only), 870 confirmed values,
45 unknown fibres, 64 known zeros; no mismatches or ambiguous present values.
Current Foundation release verified April 2026; SR Legacy April 2018.
Source mapping gaps are explicit and must not be resolved by guessing.

Keep FoodNutritionProfile as the single profile/version/provenance container.
Absence of a value row means unknown only after complete atomic import/read;
zero remains explicit. Preserve nutrient-level source locators and legacy
projections; no second current-profile selector. Extra deployment profiles need
their own full historical inventory/audit before a future backfill.

Production runtime/schema/seeds, B1/B2-A/B2-B1 unchanged. Head migration is 0027;
Nutrition v1 current; 43 estimates non-executable; 30 current recipes / 189 rows
remain INCOMPLETE. PR6 / PR6-NUTRIENT-VECTOR NOT COMPLETE; VECTOR-B NOT AUTHORIZED;
COMPOSITION-CORE / PR7+ UNAUTHORIZED. Old B2-B2 remains superseded/pending redesign.

Verification commands/results are in [progress](progress.md#pr6-nutrient-vector-a-verification).
Use `backend/.venv/bin/python` for focused tests: root `.venv` lacks SQLAlchemy.
Unrelated tracked `.DS_Store` modification is preserved and excluded from PR.
Full external archives remain temporary, outside the repository; ordinary tests
are offline and depend only on committed selected evidence plus accepted Git history.
