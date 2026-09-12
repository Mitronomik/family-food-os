# Handoff

Updated: `2026-09-12`

VECTOR-A / VECTOR-B are merged (PR #25 / #26). PR6-COMPOSITION-CORE is separately
authorized and implemented on `codex/pr6-composition-core`; verification is
complete and [PR #27](https://github.com/Mitronomik/family-food-os/pull/27) is open, ready for review (not merged).
Implementation commit: `657c692ce5ab8e49719ed9a164cda224cdfb296d`. Actual fetched base:
`b39d9f5786796dc689bdee8ae52a90cbcc4ebdfe`. Local `main` was stale; the feature
branch was created directly from verified `origin/main`. Migration 0028 → 0029.

## Approved mass authority and implemented contract

The user resolved the preflight ambiguity explicitly: persist exact positive
finite Decimal `input_mass_g` per component, derive total input mass by exact
summation, persist no normalized fractions and never approximate `1/3` as an
authoritative fraction. The earlier fraction proposal was never implemented.
The [canonical contract](../docs/family-food/food-composition-and-assembly.md#pr6-composition-core--concrete-runtime-contract)
records this decision and all implemented result/persistence semantics.

FoodIngredient remains the sole food identity. Atomic versions pin an existing
profile/sealed vector; composites pin immutable child versions, node IDs/order,
masses/states and ordered transformation steps. Build-time and SQL DAG checks
reject cycles; iterative runtime traversal also catches corrupted cycles and
allows shared-child reuse. Unknowns never become zero. Yield and sparse retention
are independent reviewed evidence with pinned immutable identities and provenance.

The reusable `CompositionCalculator` takes an explicit immutable root and a
nonempty requested nutrient-code set. It returns frozen domain results with
COMPLETE/PARTIAL/INCOMPLETE, per-nutrient availability, mass/basis, stable issues
and deterministic replay evidence. Structural corruption/missing dependencies
fail closed. Known input/retained amounts remain diagnostic when output yield is
unknown. Calculation creates no random IDs/timestamps and excludes mutable
current-profile flags. Decimal mass sums/products are exact; divisions use a
private 80-digit context, root nutrient output rounds once to six places.

Migration 0029 creates seven empty tables. Repositories share the existing Core
UoW connection and never commit independently. Snapshot-last writes, deferred FKs,
row counts and deterministic digests protect completeness; triggers protect
UPDATE/DELETE/REPLACE and late append. Migrations are forward-only; operational
rollback uses the existing pre-upgrade backup. No production backfill occurs.

## Evidence and delivery

[Audit](../data/curation/pr6-composition-core/README.md) uses temporary accepted
seed databases through real 0028. Every prior table/row and full readiness report
is unchanged by 0029; foreign keys are clean and all 183 vector seals read validly.
Current readiness is 30 recipes / 189 rows / 30 INCOMPLETE; classifications
66/21/37/65, all 43 estimates non-executable. Production counts for every new
composition table are zero; synthetic tests are not reported as production data.
Use `backend/.venv/bin/python`; `ruff` and `mypy` are available on PATH.
Executed checks and results: [progress](progress.md#pr6-composition-core-verification).

Final checks: 3758 backend/launcher tests passed, zero skips; 59 focused tests
passed; lint/format on 21 Python files and mypy on 9 runtime files passed.
Next action: review PR #27.
No autonomous merge. No automatic RU Food Data start. No RecipeVersion binding,
Recipe Assembly, API/UI, RU enrichment, B2 policy redesign, Serving, Planner,
Shopping, Pantry, AI or PR7+ work is included or newly authorized.
PR6 remains NOT COMPLETE. Unrelated `.DS_Store` remains excluded from delivery.
