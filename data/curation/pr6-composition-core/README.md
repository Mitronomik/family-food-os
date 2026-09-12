# PR6-COMPOSITION-CORE — implementation evidence

Base `origin/main`: `b39d9f5786796dc689bdee8ae52a90cbcc4ebdfe` (PR #26 merged).
Migration `0028_normalized_nutrient_vector` → `0029_food_composition_core`.

The [measured audit](implementation-evidence.json) uses a disposable database
seeded through the real 0028 chain with all accepted recipe corrections and B1
reviews. It compares every existing table/row and full Nutrition v1 readiness
before/after 0029, checks foreign keys and reads all 183 immutable sealed vectors.
It never opens a developer or real-user database. All seven new composition
infrastructure tables have zero rows; synthetic tests are not production data.

```sh
AI_ENABLED=false backend/.venv/bin/python scripts/audit_pr6_composition_core.py
AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests/test_food_composition.py backend/app/tests/test_food_composition_migration.py
```

Measured readiness is unchanged: 30 current RecipeVersions, 189 ingredient
rows, 30 INCOMPLETE; 66 APPROVED_EXACT, 21 APPROVED_NO_CONVERSION,
37 REVIEW_REQUIRED_ESTIMATE, 65 BLOCKED. All 43 estimates remain non-executable.
No FoodIngredient, FoodNutritionProfile, nutrient registry/value/seal or B1
binding changes occur. Counts are audit evidence, not runtime business constants.

The explicitly approved mass-authoritative decision replaces the task's original
reference to undefined normalized fractions: persist exact positive finite
Decimal `input_mass_g` per component; derive total input mass by exact summation.
Do not persist fractions, approximate `1/3`, or enforce a fraction-sum invariant.

[Canonical runtime contract](../../../docs/family-food/food-composition-and-assembly.md#pr6-composition-core--concrete-runtime-contract)
covers scope, immutable DAG, mass states, yield/retention, sparse requested-set
completeness, Decimal precision/rounding, replay and transactional persistence.
[Progress](../../../state/progress.md) records actual executed checks.

No public API/UI, Recipe Assembly/RecipeVersion bridge, RU data ingestion,
estimate-policy change or PR7+ implementation. PR6 remains NOT COMPLETE.
No autonomous merge or automatic RU Food Data start.
