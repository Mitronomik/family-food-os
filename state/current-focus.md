# Current focus

Updated: `2026-09-12`

- **PR6-NUTRIENT-VECTOR-A — MERGED**, PR #25, main
  `e35d87a24d5d8afb59509e566aa1ff4b7a58a11a`. Starting `origin/main` was fetched
  and matched this SHA; no later nutrition/schema changes were present.
- **PR6-NUTRIENT-VECTOR-B — implementation verified, ready for review**.
  [PR #26](https://github.com/Mitronomik/family-food-os/pull/26), branch `codex/pr6-nutrient-vector-b`; current scope is the normalized sparse
  nutrient vector owned by existing FoodNutritionProfile identities.
- Migration `0027_recipe_same_source_revisions` → `0028_normalized_nutrient_vector`.
  Measured upgrade: 51 definitions, 183 profiles, 806 values, 64 held zero
  observations. All existing table rows and v1 readiness are unchanged.
- Nutrition v1 / B1 history remain valid; production is 30 current recipes /
  189 rows / 30 INCOMPLETE. Current classifications are 66 exact, 21 no-conversion,
  37 review-required, 65 blocked; 43 estimates remain non-executable.
- Full backend/launcher regression: **3699 passed**, no skips, `AI_ENABLED=false`.
  Lint/format, affected-file mypy, migration/upgrade and provenance audits PASS.
- **PR6 — NOT COMPLETE.** Review/merge of VECTOR-B is pending.
  Composition Core is only the next roadmap candidate after acceptance/merge;
  it is not this PR and needs separate authorization. RU ingestion, B2 redesign,
  Recipe Assembly and PR7+ are outside the current scope.

Contract: [Nutrition Core](../docs/family-food/nutrition-core.md#pr6-nutrient-vector-b--normalized-immutable-snapshots).
Evidence: [VECTOR-B audit](../data/curation/pr6-nutrient-vector-b/implementation-evidence.json).
Verification: [progress](progress.md#pr6-nutrient-vector-b-verification).
Continuation: [handoff](handoff.md).
