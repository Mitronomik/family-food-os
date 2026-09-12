# PR6-NUTRIENT-VECTOR-B — implementation evidence

Base main: `e35d87a24d5d8afb59509e566aa1ff4b7a58a11a` (PR #25 merged).
No later main changes were present when starting implementation.

[Measured upgrade evidence](implementation-evidence.json) is generated on a
fresh disposable database seeded through actual migration 0027, including B1
and B2-A recipe corrections/reviews. The audit compares **every pre-existing
table and row**, all profile UUIDs/values/current flags, all B1 relationships,
and the full runtime production audit before/after migration 0028. It never
opens a developer or real-user database.

```sh
AI_ENABLED=false backend/.venv/bin/python scripts/audit_pr6_nutrient_vector_b.py
backend/.venv/bin/python scripts/validate_pr6_nutrient_vector_a.py --content-only
AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests/test_nutrient_vector.py
```

Measured: 51 definitions, 183 profiles examined/backfilled, 806 normalized
values. All 64 unresolved zero observations remain in immutable evidence and
legacy v1 projections; zero normalized values originate from them. All 45
VALUE_ABSENT observations remain unknown. No mismatch, ambiguous mapping or
source-ID-unavailable case exists in this corpus; synthetic tests exercise
those required disposition paths without adding production authority.

The actual B2-A current metrics are **66 APPROVED_EXACT, 21
APPROVED_NO_CONVERSION, 37 REVIEW_REQUIRED_ESTIMATE, 65 BLOCKED**. The earlier
20/66 figures describe B1 before B2-A, not the current seed. Before/after are
identical: 30 current versions, 189 rows, all 30 INCOMPLETE; 43 estimate
candidates remain non-executable. Numbers are audit context, not runtime rules.

VECTOR-A/B2-B1 research-only diff guards still run against their respective
accepted Git trees in tests. Current artifact content/provenance checks are
not redirected; `--content-only` separates those checks from the old per-PR
prohibition on implementing a new migration. No accepted JSON is edited.

Mechanism, unavailable-profile behavior and recovery:
[Nutrition Core](../../../docs/family-food/nutrition-core.md#pr6-nutrient-vector-b--normalized-immutable-snapshots).
Executed checks: [progress](../../../state/progress.md#pr6-nutrient-vector-b-verification).
PR6 is not complete; Composition Core requires separate authorization.
