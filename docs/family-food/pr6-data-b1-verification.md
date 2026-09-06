# PR6-DATA-B1 verification and delivery scope

Date: 2026-09-07. Exact starting main:
`60908eb8270ef356eff8552855b4cc5d2aa9ee44` (accepted DATA-A, PR #19).
Branch: `feature/pr6-data-b1-measure-evidence`.

B1 establishes the exact evidence/binding foundation. It does not claim its own
merge or acceptance. PR6 engine and DATA-A are ACCEPTED / MERGED. PR6 milestone
remains NOT COMPLETE; DATA-B2 is NOT AUTHORIZED; PR7+ remain UNAUTHORIZED.
No separate DATA-B1-CLOSE is required.

## Persistence and calculation authority

Only new migration and current head: `0026_nutrition_measure_evidence`.
The custom SQLite chain remains the sole schema authority. New tables:

- `nutrition_measure_evidence`;
- `recipe_ingredient_nutrition_assessments`;
- `recipe_ingredient_nutrition_assessment_issues`.

Driver-independent immutable domain types: `MeasureMassEvidence`,
`RecipeIngredientNutritionAssessment`; controlled `NutritionAssessmentIssue`,
`AssessmentStatus`, `SemanticCompatibility` and `ConversionDecision` enums.
Evidence and assessments are platform-owned, without Household/user ownership.

`NutritionEvidenceReader` / repository contracts add current row assessment and
evidence lookup; `NutritionProfileReader` gains exact profile-ID lookup. Concrete
Core repositories share the project UoW. New assessment versions atomically
retire the previous current marker; a partial unique index prevents two current
reviews, and immutable facts/history cannot be overwritten or deleted.
NutritionReadScope reads the complete recipe/current-profile/pinned-profile/
assessment/evidence/issues snapshot. Results expose exact provenance.

## Production seed and audit

57 evidence records (56 selected DATA-A sources, with separate exact/estimate
cheddar facts), 189 current assessments, 123 issue rows. First seed inserts
57 evidence / 189 assessments; identical second seed inserts 0 / 0, retains all
123 issues and an identical complete database dump. Every accepted row joins
exactly one current assessment, proven by grouped-current and missing-join SQL.
All 189 stable descriptors resolve to distinct local rows.

| Assessment status | Rows |
| --- | ---: |
| APPROVED_EXACT | 66 |
| APPROVED_NO_CONVERSION | 20 |
| BLOCKED | 66 |
| REVIEW_REQUIRED_ESTIMATE | 37 |

All 43 estimate candidates remain non-authoritative: 37 review-required and six
additionally blocked by profile representativeness. Eleven gram rows are blocked.
66 exact ml/pcs rows use the retained Decimal numerator/denominator without
intermediate quantization. No canonical density fallback is used for recipes.

Recipe results: 0 COMPLETE, 0 COMPLETE_WITH_WARNINGS, 0 CONDITIONAL,
30 INCOMPLETE, covering 30 RecipeVersions / 189 rows.

| Runtime warning | Row occurrences |
| --- | ---: |
| CONVERSION_ESTIMATE_NOT_ACCEPTED | 43 |
| ESTIMATED_SOURCE | 0 |
| ESTIMATION_STATUS_UNKNOWN | 189 |
| MISSING_DENSITY | 0 |
| MISSING_FOOD_INGREDIENT | 0 |
| MISSING_MEASURE_EVIDENCE | 0 |
| MISSING_NUTRITION_ASSESSMENT | 0 |
| MISSING_NUTRITION_PROFILE | 0 |
| NUTRITION_ASSESSMENT_BLOCKED | 66 |
| NUTRITION_ASSESSMENT_PROFILE_STALE | 0 |
| OPTIONAL_INGREDIENT | 4 |
| UNKNOWN_FIBER | 30 |
| UNSUPPORTED_PIECE_MASS | 0 |

| Structured assessment issue | Occurrences |
| --- | ---: |
| CONVERSION_ESTIMATE_NOT_ACCEPTED | 43 |
| FOOD_FORM_MISMATCH | 17 |
| IDENTITY_MISMATCH | 1 |
| MEASURE_OR_SIZE_AMBIGUOUS | 36 |
| NO_ACCEPTABLE_SOURCE | 1 |
| PROFILE_REPRESENTATIVENESS_REVIEW | 19 |
| SOURCE_ALTERNATIVE_WEIGHT_MISAPPLIED | 1 |
| SOURCE_QUANTITY_AMBIGUOUS | 1 |
| SOURCE_QUANTITY_MISMATCH | 4 |

Counts overlap. Nutrient-source estimation is independent of measure-conversion
estimation; `ESTIMATED_SOURCE` is never reused for conversion uncertainty.

## Pinned accepted DATA-A hashes

The production manifest pins operation `PR6-DATA-A`, accepted merged main above,
all three source SHA-256 hashes below, both production input hashes and both
promotion payload hashes. Offline regeneration is byte-identical; accepted-main
Git blobs and loader hash checks independently verify the source lineage.

| DATA-A file | SHA-256 |
| --- | --- |
| `conversion-gap-audit.json` | `7e6d87782fef1e2afadf0f37f0ed71367d70e87bfa4c186d301539f461a36711` |
| `source-manifest.json` | `3e315270c391c593e7d27c6027bc53204decae382d6779364846ac3932fe1d52` |
| `summary.json` | `bda18cbdab74defeecd524d2650eb59438334cf6fff408e8979218f8314440f1` |

## Executed verification

All pytest commands used `AI_ENABLED=false`; local interpreter:
`backend/.venv/bin/python` (Python 3.12 / SQLAlchemy 2.0.52).

```sh
AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests/test_nutrition*.py backend/app/tests/persistence/test_nutrition*.py backend/app/tests/test_pr6_data_a_research.py
# 212 passed in 25.40s.

AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests/test_food_ingredient*.py backend/app/tests/test_food_recipe*.py backend/app/tests/test_household*.py backend/app/tests/test_pantry*.py backend/app/tests/test_migration_lineage.py backend/app/tests/persistence/test_food_ingredient_repository.py backend/app/tests/persistence/test_food_recipe_repository.py backend/app/tests/persistence/test_household_repository.py backend/app/tests/persistence/test_unit_of_work.py
# 472 passed in 28.31s.

AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests launcher/tests
# Final run with required local loopback access: 3467 passed in 501.50s (0:08:21).

python3 scripts/promote_pr6_data_b1.py
AI_ENABLED=false backend/.venv/bin/python scripts/audit_pr6_data_b1.py
# PASS: byte-identical promotion and complete production audit v2.
```

The preliminary sandbox full run recorded 3158 passed, 186 failed, 121 errors in
256.02s. It exposed 23 backend tests with outdated schema/config/audit expectations
and launcher local-loopback denials. Backend expectations were corrected to the
explicitly authorized schema/policy; tests were not removed or weakened. The
full rerun above verifies the corrected branch with local test-server access.

Specific passing evidence:

- fresh migration and populated 0025→0026 upgrade preserve every prior table
  definition and every existing row value; new tables begin empty;
- injected migration failure rolls back all B1 DDL and its marker;
- duplicate key/version/current review, dangling evidence/profile/row/issue,
  invalid unit/status, zero/negative/NaN measures and immutable history failures;
- late seed reference failure rolls back evidence and earlier assessments;
- changed profile values under unchanged provenance, stale profiles, altered
  research hashes, invalid payload/schema and duplicate stable identities fail;
- stale profile A→B invalidates review; explicit review v2 restores exact mass,
  retaining historical profile A and review v1 with exactly one current marker;
- concurrent profile/review replacement cannot mix an already-open snapshot;
- new RecipeVersion rows receive no inherited authority; original rows remain
  intact, and B1 importer refuses the changed current recipe;
- read-only calculation preserves the complete database dump;
- existing nutrient totals, optional rows, unknown fiber, profile uncertainty,
  direct FoodIngredient density semantics and Household target checks pass;
- architecture tests retain driver-free domain/services, Core-only adapters and
  no new API, frontend, AI or future-context dependency.

Ruff check and format check: PASS for 34 changed Python files.
`git diff --check`, `git diff --cached --check`, staged scope audit and changed
Markdown file-link validation: PASS. No production RecipeVersion/ingredient,
FoodNutritionProfile/source seed, FoodIngredient density or DATA-A research file
was changed. `.DS_Store` is unrelated and excluded.

## Exact changed files

45 intended files, grouped by their repository paths:

```text
backend/app/db/migration_lineage.py
backend/app/db/migrations.py
backend/app/domain/nutrition.py
backend/app/domain/nutrition_config.py
backend/app/domain/nutrition_evidence.py
backend/app/migrations/versions/0026_nutrition_measure_evidence.py
backend/app/persistence/sqlalchemy_core/food_ingredient_repositories.py
backend/app/persistence/sqlalchemy_core/nutrition_evidence_repositories.py
backend/app/persistence/sqlalchemy_core/nutrition_evidence_tables.py
backend/app/persistence/sqlalchemy_core/nutrition_evidence_uow.py
backend/app/persistence/sqlalchemy_core/nutrition_read_scope.py
backend/app/seed/nutrition_measure_evidence.py
backend/app/services/nutrition.py
backend/app/services/nutrition_contracts.py
backend/app/services/nutrition_evidence_contracts.py
backend/app/tests/nutrition_evidence_fixtures.py
backend/app/tests/persistence/test_nutrition_evidence.py
backend/app/tests/persistence/test_nutrition_read_scope.py
backend/app/tests/table_guards.py
backend/app/tests/test_artifact_audit_operations_migration.py
backend/app/tests/test_database_foundation.py
backend/app/tests/test_family_food_identity_migration.py
backend/app/tests/test_household_migration.py
backend/app/tests/test_nutrition_application.py
backend/app/tests/test_nutrition_architecture.py
backend/app/tests/test_nutrition_catalogue.py
backend/app/tests/test_nutrition_domain.py
backend/app/tests/test_nutrition_evidence_domain.py
backend/app/tests/test_nutrition_targets.py
backend/app/tests/test_pantry_migration.py
backend/app/tests/test_pr6_data_a_research.py
data/seed/nutrition_measure_evidence/assessments.json
data/seed/nutrition_measure_evidence/evidence.json
data/seed/nutrition_measure_evidence/manifest.json
data/seed/nutrition_measure_evidence/production-audit-v2.json
docs/family-food/master-roadmap.md
docs/family-food/nutrition-core.md
docs/family-food/nutrition-data-readiness.md
docs/family-food/pr6-data-b1-verification.md
scripts/audit_pr6_data_b1.py
scripts/promote_pr6_data_b1.py
scripts/validate_pr6_data_a.py
state/current-focus.md
state/handoff.md
state/progress.md
```
