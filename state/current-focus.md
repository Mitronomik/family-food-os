# Current focus

Updated: `2026-09-12`

- **PR6-NUTRIENT-VECTOR-A — MERGED**, PR #25.
- **PR6-NUTRIENT-VECTOR-B — MERGED**, PR #26, main
  `b39d9f5786796dc689bdee8ae52a90cbcc4ebdfe`.
- **PR6-COMPOSITION-CORE — AUTHORIZED / implementation verified, ready for review**.
  Branch `codex/pr6-composition-core` starts at the verified remote main above.
- Explicit user decision: exact positive finite Decimal component `input_mass_g`
  is authoritative; total input mass is its exact sum. No persisted fractions,
  fraction-sum invariant or approximated recurring ratios.
- Migration `0028_normalized_nutrient_vector` → `0029_food_composition_core`.
  Seven new infrastructure tables; production composition/yield/retention rows: 0.
- Deterministic calculator: pinned sealed atomic vectors, immutable child DAG,
  explicit mass states, separate reviewed yield and sparse nutrient retention,
  per-nutrient availability and immutable replay. Nutrition v1 consumers unchanged.
- Measured readiness unchanged: 30 recipes / 189 rows / 30 INCOMPLETE;
  66 exact / 21 no-conversion / 37 review-required / 65 blocked;
  all 43 estimates non-executable. All prior rows and 183 vector seals verified.
- Final backend/launcher regression: **3758 passed**, no skips, `AI_ENABLED=false`.
  Focused Composition Core: **59 passed**. Lint/format, mypy and audits PASS.
- **PR6 — NOT COMPLETE.** No autonomous merge or automatic RU Food Data,
  B2 redesign, Recipe Assembly, Serving or PR7+ work.

Contract: [Composition Core](../docs/family-food/food-composition-and-assembly.md#pr6-composition-core--concrete-runtime-contract).
Evidence: [audit](../data/curation/pr6-composition-core/implementation-evidence.json).
Verification: [progress](progress.md#pr6-composition-core-verification).
Continuation: [handoff](handoff.md).
