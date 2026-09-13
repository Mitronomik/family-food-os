from pathlib import Path

path = Path("scripts/audit_pr6_data_b2b2.py")
text = path.read_text()

old_import = "from app.db.config import DatabaseConfig  # noqa: E402\nfrom app.db.migrations import expected_migration_ids  # noqa: E402\n"
new_import = "from app.db import migrations  # noqa: E402\nfrom app.db.config import DatabaseConfig  # noqa: E402\n"
if text.count(old_import) != 1:
    raise SystemExit("Expected patched audit import anchor exactly once")
text = text.replace(old_import, new_import, 1)

old_baseline = '''def baseline(config):
    seed_baseline(config)
    seed_ru_food_data(config)
'''
new_baseline = '''def baseline(config):
    # This is a frozen PR29 replay. Later migrations must not change the
    # historical implementation-evidence receipt being verified here.
    original = migrations.MIGRATION_MODULES
    cutoff = next(
        index
        for index, module_name in enumerate(original)
        if module_name.endswith("0029_food_composition_core")
    )
    try:
        migrations.MIGRATION_MODULES = original[: cutoff + 1]
        seed_baseline(config)
        seed_ru_food_data(config)
    finally:
        migrations.MIGRATION_MODULES = original
'''
if text.count(old_baseline) != 1:
    raise SystemExit("Expected baseline anchor exactly once")
text = text.replace(old_baseline, new_baseline, 1)

old_head = "    assert head(config) == expected_migration_ids()[-1]\n"
new_head = '    assert head(config) == "0029_food_composition_core"\n'
if text.count(old_head) != 1:
    raise SystemExit("Expected dynamic head assertion exactly once")
text = text.replace(old_head, new_head, 1)

path.write_text(text)
