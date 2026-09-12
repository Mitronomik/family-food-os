"""B2-A preservation, runner failure recovery, and immutable current/history truth."""

from copy import deepcopy
from dataclasses import fields, replace
from decimal import Decimal
from importlib import import_module
import importlib.util
from pathlib import Path
import sqlite3
import subprocess

import pytest
from sqlalchemy import UniqueConstraint, inspect
from sqlalchemy.schema import CreateIndex

from app.db import migrations, connection as connections
from app.db.config import DatabaseConfig
from app.db.connection import session
from app.domain.nutrition import NutritionWarningCode as W
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_tables import (
    food_recipe_versions_table,
)
from app.persistence.sqlalchemy_core.food_recipe_uow import (
    SqlAlchemyRecipeCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.nutrition_evidence_repositories import (
    SqlAlchemyNutritionEvidenceRepository,
)
from app.seed.food_recipes import seed_food_recipes
from app.seed.nutrition_measure_evidence import (
    NutritionEvidenceSeedError,
    seed_nutrition_measure_evidence,
)
from app.seed import recipe_corrections as b2
from app.tests.test_migration_runner_rebuild import ObservedConnection

HEAD = "0027_recipe_same_source_revisions"
OLD_HEAD = "0026_nutrition_measure_evidence"
ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "audit_pr6_data_b2a", ROOT / "scripts/audit_pr6_data_b2a.py"
)
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)


@pytest.fixture
def observed(monkeypatch):
    opened = []

    def connect(config):
        db = sqlite3.connect(config.path, factory=ObservedConnection)
        db.events = []
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        opened.append(db)
        return db

    monkeypatch.setattr(connections, "connect", connect)
    return opened


def snapshot(config):
    with sqlite3.connect(config.path) as db:
        return {
            table: sorted(db.execute(f'SELECT * FROM "{table}"').fetchall(), key=repr)
            for (table,) in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_migrations'"
            )
        }


def schema(config):
    with sqlite3.connect(config.path) as db:
        return {
            r[0]: r[1:]
            for r in db.execute("SELECT name, type, tbl_name, sql FROM sqlite_master")
        }


def dump(config):
    with sqlite3.connect(config.path) as db:
        return tuple(db.iterdump())


def assert_fk(config):
    with session(config) as db:
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def pre_b2(config, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(
            migrations, "MIGRATION_MODULES", migrations.MIGRATION_MODULES[:26]
        )
        seed_food_recipes(config)
        seed_nutrition_measure_evidence(config)
        assert migrations.expected_migration_ids()[-1] == OLD_HEAD
    counts = snapshot(config)
    for table, count in {
        "food_recipe_versions": 30,
        "food_recipe_ingredients": 189,
        "nutrition_measure_evidence": 57,
        "recipe_ingredient_nutrition_assessments": 189,
        "recipe_ingredient_nutrition_assessment_issues": 123,
    }.items():
        assert len(counts[table]) == count


@pytest.mark.parametrize("populated", [False, True])
def test_real_0027_fresh_and_populated_preservation(
    tmp_path, monkeypatch, observed, populated
):
    config = DatabaseConfig(path=tmp_path / "upgrade.sqlite")
    before = old_schema = None
    if populated:
        pre_b2(config, monkeypatch)
        before, old_schema = snapshot(config), schema(config)
        assert (
            "uq_food_recipe_versions_provenance"
            in old_schema["food_recipe_versions"][2]
        )
    observed.clear()
    assert migrations.apply_migrations(config) == (
        [HEAD] if populated else migrations.expected_migration_ids()
    )
    assert migrations.expected_migration_ids()[-1] == HEAD
    module = import_module(migrations.MIGRATION_MODULES[-1])
    assert module.SQLITE_MIGRATION_MODE == "foreign_key_rebuild"
    events = observed[0].events
    create = next(
        i
        for i, (sql, _, _) in enumerate(events)
        if "CREATE TABLE food_recipe_versions_rebuild" in sql
    )
    assert events[create][1:] == (True, 0)
    marker = next(
        i
        for i, (sql, _, _) in enumerate(events[create:], create)
        if sql.startswith("INSERT INTO schema_migrations")
    )
    check = next(
        i
        for i, (sql, _, _) in enumerate(events[marker:], marker)
        if sql == "PRAGMA foreign_key_check"
    )
    commit = next(
        i for i, (sql, _, _) in enumerate(events[check:], check) if sql == "COMMIT"
    )
    restore = next(
        i
        for i, (sql, _, _) in enumerate(events[commit:], commit)
        if sql == "PRAGMA foreign_keys=ON"
    )
    assert create < marker < check < commit < restore
    assert observed[0].closed_fk == 1
    if populated:
        assert snapshot(config) == before  # Every table, UUID, timestamp and value.
        assert {
            k: v for k, v in schema(config).items() if v[1] != "food_recipe_versions"
        } == {
            k: v for k, v in old_schema.items() if v[1] != "food_recipe_versions"
        }  # No unrelated tables, indexes or triggers rebuilt.
    assert_fk(config)
    assert migrations.apply_migrations(config) == []
    engine = create_sqlite_engine(config)
    try:
        actual = inspect(engine).get_unique_constraints("food_recipe_versions")
        assert {tuple(r["column_names"]) for r in actual} == {
            ("recipe_id", "version_number")
        }
        assert {
            tuple(c.name for c in r.columns)
            for r in food_recipe_versions_table.constraints
            if isinstance(r, UniqueConstraint)
        } == {("recipe_id", "version_number")}
        assert {
            r["name"] for r in inspect(engine).get_indexes("food_recipe_versions")
        } == {r.name for r in food_recipe_versions_table.indexes}
        current_index = next(
            i
            for i in food_recipe_versions_table.indexes
            if i.name == "idx_food_recipe_versions_current_verified"
        )
        assert "version_number DESC" in str(CreateIndex(current_index).compile(engine))
        assert all(
            not r["unique"] for r in inspect(engine).get_indexes("food_recipe_versions")
        )
    finally:
        engine.dispose()
    if not populated:
        assert seed_food_recipes(config).versions_inserted == 30
        assert seed_nutrition_measure_evidence(config)["inserted_evidence"] == 57
    assert b2.seed_recipe_corrections(config)["inserted_versions"] == 5
    assert b2.seed_correction_assessments(config)["inserted_assessments"] == 32
    assert_fk(config)


def test_0027_real_rebuild_rollback_restores_schema_data_and_resumes(
    tmp_path, monkeypatch, observed
):
    config = DatabaseConfig(path=tmp_path / "failure.sqlite")
    pre_b2(config, monkeypatch)
    before = dump(config)
    module = import_module(migrations.MIGRATION_MODULES[-1])
    upgrade = module.upgrade

    def fail(db):
        upgrade(db)
        assert (
            "uq_food_recipe_versions_provenance"
            not in db.execute(
                "SELECT sql FROM sqlite_master WHERE name='food_recipe_versions'"
            ).fetchone()[0]
        )
        raise RuntimeError("injected after actual table rebuild")

    with monkeypatch.context() as patch:
        patch.setattr(module, "upgrade", fail)
        with pytest.raises(RuntimeError, match="injected"):
            migrations.apply_migrations(config)
    assert dump(config) == before
    assert HEAD not in migrations.current_migrations(config)
    assert observed[-2].closed_fk == 1
    assert_fk(config)
    assert migrations.apply_migrations(config) == [HEAD]
    assert_fk(config)


@pytest.fixture
def catalogue(tmp_path):
    config = DatabaseConfig(path=tmp_path / "catalogue.sqlite")
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
    engine = create_sqlite_engine(config)
    try:
        yield (
            config,
            engine,
            create_food_recipe_catalogue_service(engine),
            create_nutrition_service(engine),
        )
    finally:
        engine.dispose()


def test_historical_current_semantics_explicit_assessments_and_full_idempotence(
    catalogue,
):
    config, engine, recipes, nutrition = catalogue
    old_details = {
        r.canonical_code: recipes.get_current_verified(r.id)
        for r in recipes.list_active()
    }
    old_nutrition = {
        code: nutrition.recipe_version(d.version.id) for code, d in old_details.items()
    }
    before = snapshot(config)
    assert b2.seed_recipe_corrections(config)["inserted_versions"] == 5
    entries, promoted, _ = b2.load_entries()
    by_code = {e["recipe_canonical_code"]: e for e in entries}
    new_ids = set()
    for code, v1 in old_details.items():
        v2 = recipes.get_current_verified(v1.recipe.id)
        assert recipes.get_version_detail(v1.version.id) == v1
        assert nutrition.recipe_version(v1.version.id) == old_nutrition[code]
        if code not in by_code:
            assert v2 == v1
            continue
        assert v2.version.version_number == 2
        assert v2.version.created_from_version_id == v1.version.id
        for field in fields(v1.version):
            if field.name not in {
                "id",
                "version_number",
                "created_from_version_id",
                "created_at",
                "verified_at",
                "change_note",
            }:
                assert getattr(v2.version, field.name) == getattr(
                    v1.version, field.name
                )
        assert v2.recipe == v1.recipe
        with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as uow:
            args = (
                v1.recipe.id,
                v1.version.source_name,
                v1.version.source_recipe_id,
                v1.version.source_version,
            )
            assert [
                d.version.version_number for d in uow.versions.list_by_provenance(*args)
            ] == [1, 2]
            assert uow.versions.get_by_provenance(*args) == v2
        for old, new in zip(v1.ingredients, v2.ingredients):
            assert old.id != new.id
            new_ids.add(new.id)
            allowed = {"id", "recipe_version_id", "created_at"}
            if (code, old.position) in b2.FINDINGS:
                allowed |= {"quantity", "unit", "normalization_note"}
            assert all(
                getattr(old, f.name) == getattr(new, f.name)
                for f in fields(old)
                if f.name not in allowed
            )
            reviewed = by_code[code]["revision"]["version"]["ingredients"][
                old.position - 1
            ]
            assert (
                new.quantity == Decimal(reviewed["quantity"])
                and new.unit == reviewed["unit"]
            )
        assert [(r.position, r.instruction, r.stage_code) for r in v1.steps] == [
            (r.position, r.instruction, r.stage_code) for r in v2.steps
        ]
        assert [(r.position, r.equipment_code) for r in v1.equipment] == [
            (r.position, r.equipment_code) for r in v2.equipment
        ]
        unassessed = nutrition.recipe_version(v2.version.id)
        assert sum(
            w.code == W.MISSING_NUTRITION_ASSESSMENT for w in unassessed.warnings
        ) == len(v2.ingredients)
        assert all(
            r.nutrition.mass_g is None
            for r in unassessed.required_contributions
            + unassessed.optional_contributions
        )
    assert len(new_ids) == 32
    first = b2.seed_correction_assessments(config)
    assert first["inserted_assessments"] == 32
    assert first["status_counts"] == {
        "APPROVED_EXACT": 17,
        "APPROVED_NO_CONVERSION": 1,
        "BLOCKED": 10,
        "REVIEW_REQUIRED_ESTIMATE": 4,
    }
    for p in promoted:
        a = p["assessment"]
        detail = recipes.get_current_verified(
            old_details[a["recipe_canonical_code"]].recipe.id
        )
        result = nutrition.recipe_version(detail.version.id)
        row = next(
            r
            for r in result.required_contributions + result.optional_contributions
            if r.row.position == a["ingredient_position"]
        )
        assert row.assessment.source_audit_operation == b2.OPERATION
        assert row.assessment.recipe_ingredient_id in new_ids
        assert row.assessment.status_code == a["status_code"]
        if p["promotion_mode"] == "EXPLICIT_EQUAL_ROW_CARRY_FORWARD":
            assert p["compared_parent"] == p["compared_revision"]
        if row.assessment.status_code in ("BLOCKED", "REVIEW_REQUIRED_ESTIMATE"):
            assert row.nutrition.mass_g is None
        if (
            a["recipe_canonical_code"] == "SNAP6_SEARED_GREENS"
            and a["ingredient_position"] == 1
        ):
            assert row.nutrition.mass_g == Decimal("680.388555")
    for code, detail in old_details.items():
        assert nutrition.recipe_version(detail.version.id) == old_nutrition[code]
    after = snapshot(config)
    for table, values in before.items():
        assert set(values) <= set(after[table])
    final = dump(config)
    # Exact mandatory second complete pass: PR4 -> B1 -> corrections -> assessments.
    assert seed_food_recipes(config).versions_inserted == 0
    b1 = seed_nutrition_measure_evidence(config)
    assert b1["inserted_evidence"] == b1["inserted_assessments"] == 0
    assert b2.seed_recipe_corrections(config)["inserted_versions"] == 0
    assert b2.seed_correction_assessments(config)["inserted_assessments"] == 0
    assert dump(config) == final
    assert len(after["food_recipe_versions"]) == 35
    assert len(after["food_recipe_ingredients"]) == 221
    assert len(after["recipe_ingredient_nutrition_assessments"]) == 221
    assert len(after["nutrition_measure_evidence"]) == 57
    report = audit_module.audit_catalogue(engine)
    assert (
        report
        == audit_module.audit_catalogue(engine)
        == b2.read_json(audit_module.REPORT)
    )
    assert report["recipes"] == 30 and report["recipe_ingredient_rows"] == 189
    assert [r["outcome"] for r in report["source_quantity_findings"]] == [
        "RESOLVED"
    ] * 6
    assert report["warning_occurrences"]["MISSING_NUTRITION_ASSESSMENT"] == 0
    assert report["warning_occurrences"]["CONVERSION_ESTIMATE_NOT_ACCEPTED"] == 43
    assert_fk(config)


@pytest.mark.parametrize(
    "loader,repository,method",
    [
        (b2.seed_recipe_corrections, SqlAlchemyRecipeVersionRepository, "add_detail"),
        (
            b2.seed_correction_assessments,
            SqlAlchemyNutritionEvidenceRepository,
            "add_assessment",
        ),
    ],
)
def test_partial_loader_failure_is_atomic_and_resumable(
    catalogue, monkeypatch, loader, repository, method
):
    config, _, _, _ = catalogue
    if loader is b2.seed_correction_assessments:
        b2.seed_recipe_corrections(config)
    before = dump(config)
    original = getattr(repository, method)
    calls = []

    def fail(self, value):
        original(self, value)
        calls.append(value)
        if len(calls) == 2:
            raise RuntimeError("injected after second insert")

    with monkeypatch.context() as patch:
        patch.setattr(repository, method, fail)
        with pytest.raises(RuntimeError, match="injected"):
            loader(config)
    assert len(calls) == 2 and dump(config) == before
    loader(config)
    assert_fk(config)


def test_conflicting_v2_fails_without_repairing_latest(catalogue):
    config, engine, recipes, _ = catalogue
    entries, _, _ = b2.load_entries()
    entry = entries[1]  # One earlier recipe would otherwise insert before failure.
    parent = recipes.get_current_verified(
        recipes.get_by_code(entry["recipe_canonical_code"]).id
    )
    conflict = b2._revision(parent, entry)
    conflict = replace(
        conflict,
        version=replace(conflict.version, change_note="Conflicting reviewed v2"),
    )
    with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as uow:
        uow.versions.add_detail(conflict)
        uow.commit()
    before = dump(config)
    with pytest.raises(NutritionEvidenceSeedError, match="Conflicting existing v2"):
        b2.seed_recipe_corrections(config)
    assert dump(config) == before


def test_unresolved_recipe_gate_suppresses_both_rows_and_all_assessments(
    catalogue, monkeypatch
):
    config, _, recipes, _ = catalogue
    review = deepcopy(b2.read_json(ROOT / b2.CURATION))
    next(
        r
        for r in review["records"]
        if r["recipe_canonical_code"] == "SNAP6_SPINACH_APPLE_SALAD"
        and r["ingredient_position"] == 2
    ).update(
        resolution_status="UNRESOLVED_SOURCE_AMBIGUITY",
        corrected_quantity=None,
        corrected_unit=None,
    )
    _, _, b1_rows = b2.load_entries()
    corrections, assessments = b2.build_promotion(
        review, b2.read_json(ROOT / b2.PR4)["recipes"], b1_rows
    )
    assert len(corrections["corrections"]) == 4
    assert all(
        e["assessment"]["recipe_canonical_code"] != "SNAP6_SPINACH_APPLE_SALAD"
        for e in assessments["assessments"]
    )
    monkeypatch.setattr(
        b2,
        "load_entries",
        lambda _: (corrections["corrections"], assessments["assessments"], b1_rows),
    )
    assert b2.seed_recipe_corrections(config)["inserted_versions"] == 4
    assert (
        recipes.get_current_verified(
            recipes.get_by_code("SNAP6_SPINACH_APPLE_SALAD").id
        ).version.version_number
        == 1
    )


def test_protected_bytes_and_only_authorized_migration():
    for path in sorted(b2.INPUT_PATHS - {b2.CURATION}):
        assert (ROOT / path).read_bytes() == subprocess.check_output(
            ["git", "show", f"{b2.STARTING_MAIN}:{path}"], cwd=ROOT
        )
    assert migrations.expected_migration_ids()[-2:] == [OLD_HEAD, HEAD]
    assert len(migrations.expected_migration_ids()) == 27
    module = import_module(migrations.MIGRATION_MODULES[-1])
    source = Path(module.__file__).read_text()
    for forbidden in (
        ".commit(",
        ".rollback(",
        "executescript",
        "SAVEPOINT",
        "PRAGMA",
        "INSERT INTO schema_migrations",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity", Decimal("999")),
        ("unit", "pcs"),
        ("normalization_note", "unexpected"),
        ("prep_note", "unexpected"),
        ("optional", True),
        ("source_amount_text", "unexpected source"),
    ],
)
def test_complete_parent_mismatch_fails_before_append(
    catalogue, monkeypatch, field, value
):
    config, _, _, _ = catalogue
    get_detail = SqlAlchemyRecipeVersionRepository.get_detail

    def corrupted(self, version_id):
        detail = get_detail(self, version_id)
        if detail.recipe.canonical_code == "HARV6_FRESH_TOMATO_SALSA":
            return replace(
                detail,
                ingredients=(
                    replace(detail.ingredients[0], **{field: value}),
                    *detail.ingredients[1:],
                ),
            )
        return detail

    before = dump(config)
    monkeypatch.setattr(SqlAlchemyRecipeVersionRepository, "get_detail", corrupted)
    with pytest.raises(
        NutritionEvidenceSeedError, match="Complete reviewed parent differs"
    ):
        b2.seed_recipe_corrections(config)
    assert dump(config) == before


def test_assessment_seed_rejects_conflicting_v2_chain(catalogue):
    config, engine, recipes, _ = catalogue
    entries, _, _ = b2.load_entries()
    for entry in entries:
        parent = recipes.get_current_verified(
            recipes.get_by_code(entry["recipe_canonical_code"]).id
        )
        revision = b2._revision(parent, entry)
        if entry == entries[-1]:
            revision = replace(
                revision,
                version=replace(revision.version, created_from_version_id=None),
            )
        with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as uow:
            uow.versions.add_detail(revision)
            uow.commit()
    before = dump(config)
    with pytest.raises(NutritionEvidenceSeedError, match="Conflicting existing v2"):
        b2.seed_correction_assessments(config)
    assert dump(config) == before


def test_assessment_seed_rejects_different_existing_review(catalogue):
    config, engine, _, _ = catalogue
    b2.seed_recipe_corrections(config)
    b2.seed_correction_assessments(config)
    from app.persistence.sqlalchemy_core.nutrition_evidence_uow import (
        SqlAlchemyNutritionEvidenceUnitOfWork,
    )

    entries, promoted, _ = b2.load_entries()
    with SqlAlchemyNutritionEvidenceUnitOfWork(engine) as uow:
        recipe = uow.recipes.get_by_code(entries[0]["recipe_canonical_code"])
        row = uow.versions.get_current_verified(recipe.id).ingredients[0]
        review = uow.evidence.get_current_assessment(row.id)
        from uuid import uuid4

        uow.evidence.add_assessment(
            replace(
                review, id=uuid4(), assessment_version=2, review_note="Separate review"
            )
        )
        uow.commit()
    before = dump(config)
    with pytest.raises(NutritionEvidenceSeedError, match="Conflicting B2-A assessment"):
        b2.seed_correction_assessments(config)
    assert dump(config) == before


def test_curation_exact_arithmetic_and_primary_apple_selection():
    from decimal import ROUND_HALF_UP, localcontext

    records = {
        (r["recipe_canonical_code"], r["ingredient_position"]): r
        for r in b2.read_json(ROOT / b2.CURATION)["records"]
    }
    with localcontext() as context:
        context.prec = 42
        expected = {
            ("HARV6_FRESH_TOMATO_SALSA", 1): (Decimal(240), "ml"),
            ("SNAP6_SPINACH_APPLE_SALAD", 1): (
                (Decimal(2) / 3 * 10 * Decimal("28.349523125")).quantize(
                    Decimal("0.000001"), rounding=ROUND_HALF_UP
                ),
                "g",
            ),
            ("SNAP6_SPINACH_APPLE_SALAD", 2): (Decimal("1.5"), "pcs"),
            ("SNAP6_SEARED_GREENS", 1): (Decimal("1.5") * Decimal("453.59237"), "g"),
            ("WIC1_OVERNIGHT_OATS_CINNAMON_APPLE", 5): (Decimal("0.5"), "pcs"),
            ("SNAP4_BROWN_RICE_PILAF", 1): (Decimal("1.5") * 240, "ml"),
        }
    assert set(records) == set(expected)
    for key, (quantity, unit) in expected.items():
        record = records[key]
        assert record["resolution_status"] == "CORRECTED"
        assert (
            Decimal(record["corrected_quantity"]) == quantity
            and record["corrected_unit"] == unit
        )
    apple = records["SNAP6_SPINACH_APPLE_SALAD", 2]
    assert apple["source_amount_text"] == "1 1/2 apples (chopped, can use 1-2 apples)"
    assert "no midpoint" in apple["review_note"]


@pytest.fixture(autouse=True)
def b2a_migration_boundary(monkeypatch):
    monkeypatch.setattr(
        migrations, "MIGRATION_MODULES", migrations.MIGRATION_MODULES[:27]
    )
