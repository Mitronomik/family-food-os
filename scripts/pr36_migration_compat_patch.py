from pathlib import Path


def one(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected 1 anchor, got {count}: {old!r}")
    target.write_text(text.replace(old, new, 1))


def alln(path: str, old: str, new: str, expected: int) -> None:
    target = Path(path)
    text = target.read_text()
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} anchors, got {count}: {old!r}")
    target.write_text(text.replace(old, new))


one(
    "backend/app/db/migration_lineage.py",
    '''    "0029_food_composition_core": frozenset(
        {
            "food_yield_models",
            "food_retention_profiles",
            "food_retention_values",
            "food_transformations",
            "food_composition_versions",
            "food_composition_nodes",
            "food_composition_steps",
        }
    ),
}
''',
    '''    "0029_food_composition_core": frozenset(
        {
            "food_yield_models",
            "food_retention_profiles",
            "food_retention_values",
            "food_transformations",
            "food_composition_versions",
            "food_composition_nodes",
            "food_composition_steps",
        }
    ),
    "0030_recipe_source_corpus": frozenset(
        {
            "recipe_source_documents",
            "recipe_source_cards",
            "recipe_source_card_variants",
            "recipe_source_card_ingredients",
            "recipe_source_declared_nutrients",
        }
    ),
}
''',
)
one(
    "backend/app/tests/table_guards.py",
    '''    "food_composition_steps",
    "sqlite_sequence",
''',
    '''    "food_composition_steps",
    "recipe_source_documents",
    "recipe_source_cards",
    "recipe_source_card_variants",
    "recipe_source_card_ingredients",
    "recipe_source_declared_nutrients",
    "sqlite_sequence",
''',
)
one(
    "backend/app/tests/persistence/test_nutrition_read_scope.py",
    '''        assert (
            database.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid DESC LIMIT 1"
            ).fetchone()[0]
            == "0029_food_composition_core"
        )
    assert expected_migration_ids()[-1] == "0029_food_composition_core"
    assert len(expected_migration_ids()) == 29
''',
    '''        assert (
            database.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid DESC LIMIT 1"
            ).fetchone()[0]
            == expected_migration_ids()[-1]
        )
''',
)
one(
    "backend/app/tests/test_family_food_identity_migration.py",
    '''        "0028_normalized_nutrient_vector",
        "0029_food_composition_core",
    ]
''',
    '''        "0028_normalized_nutrient_vector",
        "0029_food_composition_core",
        "0030_recipe_source_corpus",
    ]
''',
)
p = "backend/app/tests/test_food_composition_migration.py"
one(
    p,
    'MIGRATION = import_module("app.migrations.versions.0029_food_composition_core")\n',
    'MIGRATION = import_module("app.migrations.versions.0029_food_composition_core")\nSOURCE_CORPUS_MIGRATION_ID = "0030_recipe_source_corpus"\n',
)
one(p, '    assert report["migration_head_after"] == MIGRATION.MIGRATION_ID\n', '    assert report["migration_head_after"] == SOURCE_CORPUS_MIGRATION_ID\n')
one(
    p,
    '    assert migrations.expected_migration_ids()[-1] == MIGRATION.MIGRATION_ID\n',
    '''    assert migrations.expected_migration_ids()[-2:] == [
        MIGRATION.MIGRATION_ID,
        SOURCE_CORPUS_MIGRATION_ID,
    ]
''',
)
one(
    p,
    '    assert migrations.pending_migration_ids(config) == [MIGRATION.MIGRATION_ID]\n    assert migrations.apply_migrations(config) == [MIGRATION.MIGRATION_ID]\n',
    '''    assert migrations.pending_migration_ids(config) == [
        MIGRATION.MIGRATION_ID,
        SOURCE_CORPUS_MIGRATION_ID,
    ]
    assert migrations.apply_migrations(config) == [
        MIGRATION.MIGRATION_ID,
        SOURCE_CORPUS_MIGRATION_ID,
    ]
''',
)
one(
    "backend/app/tests/test_household_migration.py",
    '''        "0028_normalized_nutrient_vector",
        "0029_food_composition_core",
    ]
''',
    '''        "0028_normalized_nutrient_vector",
        "0029_food_composition_core",
        "0030_recipe_source_corpus",
    ]
''',
)
one("backend/app/tests/test_migration_runner_rebuild.py", 'HEAD = "0029_food_composition_core"\n', 'HEAD = "0030_recipe_source_corpus"\n')
one(
    "backend/app/tests/test_migration_runner_rebuild.py",
    "    assert len(accepted) == 29 and accepted[-1] == HEAD\n",
    "    assert accepted[-1] == HEAD and len(accepted) == len(set(accepted))\n",
)
p = "backend/app/tests/test_nutrient_vector.py"
one(
    p,
    '''    assert migrations.expected_migration_ids()[-2:] == [
        MIGRATION.MIGRATION_ID,
        "0029_food_composition_core",
    ]
''',
    '''    assert migrations.expected_migration_ids()[-3:] == [
        MIGRATION.MIGRATION_ID,
        "0029_food_composition_core",
        "0030_recipe_source_corpus",
    ]
''',
)
alln(
    p,
    '''        MIGRATION.MIGRATION_ID,
        "0029_food_composition_core",
    ]
''',
    '''        MIGRATION.MIGRATION_ID,
        "0029_food_composition_core",
        "0030_recipe_source_corpus",
    ]
''',
    2,
)
one(
    "backend/app/tests/test_nutrition_architecture.py",
    '''def test_b1_and_b2a_add_only_authorized_schema_and_no_api():
    assert expected_migration_ids()[-4:] == [
        "0026_nutrition_measure_evidence",
        "0027_recipe_same_source_revisions",
        "0028_normalized_nutrient_vector",
        "0029_food_composition_core",
    ]
    assert len(expected_migration_ids()) == 29
''',
    '''def test_b1_and_b2a_add_only_authorized_schema_and_no_api():
    migration_ids = expected_migration_ids()
    start = migration_ids.index("0026_nutrition_measure_evidence")
    assert migration_ids[start : start + 4] == [
        "0026_nutrition_measure_evidence",
        "0027_recipe_same_source_revisions",
        "0028_normalized_nutrient_vector",
        "0029_food_composition_core",
    ]
''',
)
one(
    "scripts/audit_pr6_data_b2b2.py",
    "from app.db.config import DatabaseConfig  # noqa: E402\n",
    "from app.db.config import DatabaseConfig  # noqa: E402\nfrom app.db.migrations import expected_migration_ids  # noqa: E402\n",
)
one(
    "scripts/audit_pr6_data_b2b2.py",
    '    assert head(config) == "0029_food_composition_core"\n',
    "    assert head(config) == expected_migration_ids()[-1]\n",
)
p = "scripts/audit_pr6_ru_food_data.py"
one(
    p,
    'BASE = "d5b5ce3fdc4ec79de5454b3ed23b1d527772c0bc"\n',
    'BASE = "d5b5ce3fdc4ec79de5454b3ed23b1d527772c0bc"\nACCEPTED_HEAD = "4180297d47d68a0e0d9efbe7a7a27f3900c4f388"\n',
)
one(
    p,
    '["git", "diff", "--name-only", BASE], cwd=ROOT, text=True',
    '["git", "diff", "--name-only", BASE, ACCEPTED_HEAD], cwd=ROOT, text=True',
)
one(
    "backend/app/tests/test_ru_food_data.py",
    '''    assert (
        result["migration_head_before"]
        == result["migration_head_after"]
        == "0029_food_composition_core"
    )
''',
    '''    assert (
        result["migration_head_before"]
        == result["migration_head_after"]
        == result["registered_migration_head"]
    )
''',
)
p = "backend/app/tests/test_database_foundation.py"
one(
    p,
    '''    try:
        MIGRATION_MODULES[:] = original[:-1]
        apply_migrations(DatabaseConfig(path=database_path))
''',
    '''    try:
        cutoff = next(
            index
            for index, module_name in enumerate(original)
            if module_name.endswith("0028_normalized_nutrient_vector")
        )
        MIGRATION_MODULES[:] = original[: cutoff + 1]
        apply_migrations(DatabaseConfig(path=database_path))
''',
)
one(p, "    # The backup remains at 0028; only the live DB gains Composition Core.\n", "    # The backup remains at 0028; the live DB gains 0029 and later migrations.\n")
one(p, "    assert result.applied_migrations == [expected_migration_ids()[-1]]\n", "    assert result.applied_migrations == expected_migration_ids()[-2:]\n")
p = "backend/app/tests/test_artifact_audit_operations_migration.py"
one(p, 'HEAD_MIGRATION_ID = "0029_food_composition_core"\n', 'COMPOSITION_MIGRATION_ID = "0029_food_composition_core"\nHEAD_MIGRATION_ID = "0030_recipe_source_corpus"\n')
alln(
    p,
    '''        VECTOR_MIGRATION_ID,
        HEAD_MIGRATION_ID,
''',
    '''        VECTOR_MIGRATION_ID,
        COMPOSITION_MIGRATION_ID,
        HEAD_MIGRATION_ID,
''',
    3,
)
one(
    p,
    '''        "food_composition_steps",
    }
''',
    '''        "food_composition_steps",
        "recipe_source_documents",
        "recipe_source_cards",
        "recipe_source_card_variants",
        "recipe_source_card_ingredients",
        "recipe_source_declared_nutrients",
    }
''',
)
