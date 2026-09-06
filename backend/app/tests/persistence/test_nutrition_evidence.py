import hashlib
import importlib.util
import json
import shutil
import sqlite3
from dataclasses import asdict, replace
from decimal import Decimal, localcontext
from uuid import uuid4

import pytest
from sqlalchemy import insert, update
from sqlalchemy.exc import IntegrityError

from app.db.config import DatabaseConfig
from app.db.migrations import (
    MIGRATION_MODULES,
    apply_migrations,
    expected_migration_ids,
)
from app.db.migration_lineage import REQUIRED_TABLES_BY_MIGRATION
from app.domain.nutrition import NutritionWarningCode as W
from app.domain.nutrition_config import calculation_context
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.nutrition_evidence_tables import (
    nutrition_measure_evidence_table as ET,
    recipe_ingredient_nutrition_assessments_table as AT,
    recipe_ingredient_nutrition_assessment_issues_table as IT,
)
from app.persistence.sqlalchemy_core.nutrition_evidence_uow import (
    SqlAlchemyNutritionEvidenceUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_read_scope import (
    SqlAlchemyNutritionReadScope,
)
from app.seed.food_recipes import seed_food_recipes
from app.seed.nutrition_measure_evidence import (
    DEFAULT_SEED_DIRECTORY,
    ROOT,
    NutritionEvidenceSeedError,
    load_seed_entries,
    seed_nutrition_measure_evidence,
)
from app.services.nutrition_evidence_contracts import NutritionEvidenceConflictError
from app.tests.persistence.test_nutrition_read_scope import recipe_detail

TABLES = {ET.name, AT.name, IT.name}
HEAD = "0026_nutrition_measure_evidence"


def dump(config):
    with sqlite3.connect(config.path) as db:
        return list(db.iterdump())


@pytest.fixture
def corpus(tmp_path):
    config = DatabaseConfig(path=tmp_path / "b1.sqlite")
    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    try:
        yield config, engine
    finally:
        engine.dispose()


@pytest.fixture
def seeded(corpus):
    config, engine = corpus
    seed_nutrition_measure_evidence(config)
    return config, engine


@pytest.mark.parametrize("upgrade", [False, True])
def test_fresh_and_0025_upgrade_preserve_every_existing_value(tmp_path, upgrade):
    config = DatabaseConfig(path=tmp_path / "migration.sqlite")
    old_rows, old_schema = {}, {}
    if upgrade:
        modules = MIGRATION_MODULES[:]
        MIGRATION_MODULES[:] = modules[:25]
        try:
            seed_food_recipes(config)
        finally:
            MIGRATION_MODULES[:] = modules
        with sqlite3.connect(config.path) as db:
            assert (
                db.execute("SELECT COUNT(*) FROM food_recipe_ingredients").fetchone()[0]
                == 189
            )
            old_schema = {
                r[0]: r[1:]
                for r in db.execute("SELECT name,type,tbl_name,sql FROM sqlite_master")
            }
            for (table,) in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ):
                old_rows[table] = db.execute(f'SELECT * FROM "{table}"').fetchall()
    assert apply_migrations(config) == ([HEAD] if upgrade else expected_migration_ids())
    assert apply_migrations(config) == []
    assert (
        expected_migration_ids()[-1] == HEAD
        and expected_migration_ids().count(HEAD) == 1
    )
    assert REQUIRED_TABLES_BY_MIGRATION[HEAD] == frozenset(TABLES)
    with sqlite3.connect(config.path) as db:
        schema = {
            r[0]: r[1:]
            for r in db.execute("SELECT name,type,tbl_name,sql FROM sqlite_master")
        }
        assert old_schema.items() <= schema.items()
        for table, rows in old_rows.items():
            actual = db.execute(f'SELECT * FROM "{table}"').fetchall()
            assert (actual[:-1] if table == "schema_migrations" else actual) == rows
        for table in TABLES:
            assert db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 0
            assert not {"household_id", "owner_id", "user_id"} & {
                r[1] for r in db.execute(f'PRAGMA table_info("{table}")')
            }
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    if not upgrade:
        seed_food_recipes(config)
    assert seed_nutrition_measure_evidence(config)["resolved_current_rows"] == 189


def test_failed_migration_rolls_back_all_new_tables_and_marker(tmp_path, monkeypatch):
    from importlib import import_module

    config = DatabaseConfig(path=tmp_path / "failure.sqlite")
    modules = MIGRATION_MODULES[:]
    MIGRATION_MODULES[:] = modules[:25]
    try:
        seed_food_recipes(config)
    finally:
        MIGRATION_MODULES[:] = modules
    before = dump(config)
    migration = import_module(MIGRATION_MODULES[-1])
    monkeypatch.setattr(
        migration, "STATEMENTS", migration.STATEMENTS[:2] + ("INVALID SQL",)
    )
    with pytest.raises(sqlite3.OperationalError):
        apply_migrations(config)
    assert dump(config) == before


def test_seed_idempotence_full_row_coverage_and_exact_candidate_arithmetic(corpus):
    config, engine = corpus
    before = dump(config)
    first = seed_nutrition_measure_evidence(config)
    after = dump(config)
    assert seed_nutrition_measure_evidence(config) == first | {
        "inserted_evidence": 0,
        "inserted_assessments": 0,
    }
    assert dump(config) == after
    # Every old INSERT (including recipe/profile values and global densities) survives verbatim.
    assert set(line for line in before if line.startswith("INSERT INTO")) <= set(after)
    with sqlite3.connect(config.path) as db:
        assert db.execute(f"SELECT count(*) FROM {ET.name}").fetchone()[0] == 57
        assert db.execute(f"SELECT count(*) FROM {IT.name}").fetchone()[0] == 123
        assert (
            db.execute(
                f"SELECT recipe_ingredient_id FROM {AT.name} GROUP BY recipe_ingredient_id HAVING SUM(is_current)!=1"
            ).fetchall()
            == []
        )
        assert (
            db.execute(
                f"SELECT COUNT(*) FROM food_recipe_ingredients r LEFT JOIN {AT.name} a ON a.recipe_ingredient_id=r.id AND a.is_current=1 WHERE a.id IS NULL"
            ).fetchone()[0]
            == 0
        )
    from app.persistence.sqlalchemy_core.food_recipe_composition import (
        create_food_recipe_catalogue_service,
    )

    recipes = create_food_recipe_catalogue_service(engine)
    exact = estimates = blocked_g = 0
    for recipe in recipes.list_active():
        detail = recipes.get_current_verified(recipe.id)
        result = create_nutrition_service(engine).recipe_version(detail.version.id)
        for item in result.required_contributions + result.optional_contributions:
            assert item.assessment.assessment_version == 1
            if item.assessment.status_code == "APPROVED_EXACT":
                exact += 1
                e = item.measure_evidence
                with localcontext(calculation_context()):
                    assert (
                        item.nutrition.mass_g
                        == item.row.quantity
                        * e.gram_weight
                        / e.normalized_input_quantity
                    )
                assert not e.estimated
            if "CONVERSION_ESTIMATE_NOT_ACCEPTED" in item.assessment.issues:
                estimates += 1
                assert item.measure_evidence.estimated
                assert (
                    item.nutrition.mass_g is None and item.nutrition.values.kcal is None
                )
            if item.row.unit == "g" and item.assessment.status_code == "BLOCKED":
                blocked_g += 1
                assert item.nutrition.mass_g is None
    assert (exact, estimates, blocked_g) == (66, 43, 11)
    assert dump(config) == after  # Calculation is read-only.


def test_stale_profile_reassessment_and_snapshot_coherence(seeded):
    config, engine = seeded
    with sqlite3.connect(config.path, isolation_level=None) as db:
        db.execute("PRAGMA journal_mode=WAL")
    detail = recipe_detail(engine)
    row = detail.ingredients[0]
    with SqlAlchemyNutritionReadScope(engine) as read:
        assert read.versions.get_detail(detail.version.id) == detail
        old_review = read.evidence.get_current_assessment(row.id)
        old_evidence = read.evidence.get_evidence(old_review.measure_evidence_id)
        old_profile = read.nutrition_profiles.get_current(row.food_ingredient_id)
        replacement = replace(
            old_profile, id=uuid4(), source_version="synthetic-v2", kcal=Decimal(999)
        )
        with SqlAlchemyFoodCatalogueUnitOfWork(engine) as write:
            write.nutrition_profiles.clear_current(row.food_ingredient_id)
            write.nutrition_profiles.add(replacement)
            write.commit()
        service = create_nutrition_service(engine)
        stale = service.recipe_version(detail.version.id).required_contributions[0]
        assert stale.nutrition.mass_g is None
        assert W.NUTRITION_ASSESSMENT_PROFILE_STALE in [
            w.code for w in stale.nutrition.warnings
        ]
        assert stale.assessment_profile == replace(old_profile, is_current=False)
        new_review = replace(
            old_review,
            id=uuid4(),
            nutrition_profile_id=replacement.id,
            assessment_version=2,
            review_note="Synthetic explicit reassessment",
        )
        with SqlAlchemyNutritionEvidenceUnitOfWork(engine) as write:
            write.evidence.add_assessment(new_review)
            write.commit()
        # The open scope retains the complete pre-replacement view, including current markers.
        assert read.evidence.get_current_assessment(row.id) == old_review
        assert (
            read.evidence.get_evidence(old_review.measure_evidence_id) == old_evidence
        )
        assert (
            read.nutrition_profiles.get_nutrition_profile_by_id(old_profile.id)
            == old_profile
        )
        assert (
            read.nutrition_profiles.get_current(row.food_ingredient_id) == old_profile
        )
        from app.domain.nutrition import calculate_recipe_nutrition

        snapshot = calculate_recipe_nutrition(
            replace(detail, ingredients=(row,)),
            {row.food_ingredient_id: read.ingredients.get(row.food_ingredient_id)},
            {row.food_ingredient_id: old_profile},
            {row.id: old_review},
            {old_evidence.id: old_evidence},
        )
        assert snapshot.required_contributions[0].nutrition.mass_g == Decimal("4.5")
    current = service.recipe_version(detail.version.id).required_contributions[0]
    assert current.assessment == new_review and current.nutrition.mass_g == Decimal(
        "4.5"
    )
    assert current.nutrition.profile == replacement
    with sqlite3.connect(config.path) as db:
        assert db.execute(
            f"SELECT assessment_version,is_current FROM {AT.name} WHERE recipe_ingredient_id=? ORDER BY assessment_version",
            (row.id.hex,),
        ).fetchall() == [(1, 0), (2, 1)]


@pytest.mark.parametrize(
    "failure", ["evidence_fk", "duplicate_version", "profile_fk", "row_fk"]
)
def test_failed_reassessment_preserves_current_review(seeded, failure):
    _, engine = seeded
    row = recipe_detail(engine).ingredients[0]
    with SqlAlchemyNutritionEvidenceUnitOfWork(engine) as write:
        old = write.evidence.get_current_assessment(row.id)
        changes = {"id": uuid4(), "assessment_version": 2}
        changes.update(
            {
                "evidence_fk": {"measure_evidence_id": uuid4()},
                "profile_fk": {"nutrition_profile_id": uuid4()},
                "row_fk": {"recipe_ingredient_id": uuid4(), "assessment_version": 1},
                "duplicate_version": {"assessment_version": 1},
            }[failure]
        )
        with pytest.raises(NutritionEvidenceConflictError):
            write.evidence.add_assessment(replace(old, **changes))
        assert write.evidence.get_current_assessment(row.id) == old
        write.commit()


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_input_unit", "g"),
        ("normalized_input_quantity", Decimal(0)),
        ("normalized_input_quantity", Decimal(-1)),
        ("gram_weight", Decimal(0)),
        ("gram_weight", Decimal(-1)),
        ("normalized_input_quantity", Decimal("NaN")),
    ],
)
def test_evidence_sql_constraints(corpus, field, value):
    _, engine = corpus
    _, entries, _ = load_seed_entries()
    values = asdict(entries[0])
    values[field] = value
    with engine.begin() as db:
        with pytest.raises(IntegrityError):
            db.execute(insert(ET).values(**values))


@pytest.mark.parametrize(
    "failure",
    [
        "duplicate_key",
        "second_current",
        "duplicate_version",
        "invalid_status",
        "dangling_issue",
        "duplicate_issue",
        "update_evidence",
        "delete_evidence",
        "update_review",
        "update_issue",
        "delete_review",
    ],
)
def test_database_constraints_and_immutable_history(seeded, failure):
    _, engine = seeded
    row = recipe_detail(engine).ingredients[0]
    with SqlAlchemyNutritionEvidenceUnitOfWork(engine) as write:
        review = write.evidence.get_current_assessment(row.id)
        evidence = write.evidence.get_evidence(review.measure_evidence_id)
    with engine.begin() as db:
        with pytest.raises(IntegrityError):
            if failure == "duplicate_key":
                db.execute(insert(ET).values(**asdict(replace(evidence, id=uuid4()))))
            elif failure in ("second_current", "duplicate_version", "invalid_status"):
                values = asdict(review)
                values.pop("issues")
                values["id"] = uuid4()
                if failure == "second_current":
                    values["assessment_version"] = 2
                elif failure == "duplicate_version":
                    values["is_current"] = False
                else:
                    values.update(
                        assessment_version=2, is_current=False, status_code="INVALID"
                    )
                db.execute(insert(AT).values(**values))
            elif failure == "dangling_issue":
                db.execute(
                    insert(IT).values(
                        assessment_id=uuid4(),
                        position=1,
                        issue_code="NO_ACCEPTABLE_SOURCE",
                    )
                )
            elif failure == "duplicate_issue":
                blocked = (
                    db.execute(AT.select().where(AT.c.status_code == "BLOCKED"))
                    .mappings()
                    .first()
                )
                issue = (
                    db.execute(IT.select().where(IT.c.assessment_id == blocked["id"]))
                    .mappings()
                    .first()
                )
                db.execute(
                    insert(IT).values(
                        assessment_id=blocked["id"],
                        position=99,
                        issue_code=issue["issue_code"],
                    )
                )
            elif failure == "update_evidence":
                db.execute(
                    update(ET)
                    .where(ET.c.id == evidence.id)
                    .values(gram_weight=Decimal(999))
                )
            elif failure == "delete_evidence":
                db.execute(ET.delete().where(ET.c.id == evidence.id))
            elif failure == "update_review":
                db.execute(
                    update(AT).where(AT.c.id == review.id).values(review_note="rewrite")
                )
            elif failure == "update_issue":
                db.execute(update(IT).values(issue_code="NO_ACCEPTABLE_SOURCE"))
            elif failure == "delete_review":
                db.execute(AT.delete().where(AT.c.id == review.id))


def test_late_seed_reference_failure_rolls_back_all_inserts(corpus):
    config, engine = corpus
    _, _, descriptors = load_seed_entries()
    last = descriptors[-1]
    with SqlAlchemyNutritionEvidenceUnitOfWork(engine) as write:
        food = write.ingredients.get_by_code(last["food_ingredient_code"])
        old = write.nutrition_profiles.get_current(food.id)
        write.nutrition_profiles.clear_current(food.id)
        write.nutrition_profiles.add(
            replace(old, id=uuid4(), source_version="changed-underlying-input")
        )
        write.commit()
    before = dump(config)
    with pytest.raises(NutritionEvidenceSeedError, match="absent/stale"):
        seed_nutrition_measure_evidence(config)
    assert dump(config) == before


def test_seed_detects_modified_profile_values_with_same_provenance(corpus):
    config, engine = corpus
    from app.persistence.sqlalchemy_core.food_ingredient_tables import (
        food_nutrition_profiles_table,
    )

    with engine.begin() as db:
        db.execute(update(food_nutrition_profiles_table).values(kcal=Decimal(1)))
    before = dump(config)
    with pytest.raises(NutritionEvidenceSeedError, match="differs: kcal"):
        seed_nutrition_measure_evidence(config)
    assert dump(config) == before


@pytest.mark.parametrize(
    "failure", ["hash", "schema", "duplicate", "reference", "status"]
)
def test_invalid_seed_payload_is_rejected_before_mutation(corpus, tmp_path, failure):
    config, _ = corpus
    directory = tmp_path / "seed"
    shutil.copytree(DEFAULT_SEED_DIRECTORY, directory)
    path = directory / "assessments.json"
    data = json.loads(path.read_text())
    if failure == "hash":
        data["assessments"][0]["review_note"] = "unreviewed mutation"
    elif failure == "schema":
        data["unexpected"] = 1
    elif failure == "duplicate":
        data["assessments"][-1] = data["assessments"][0]
    elif failure == "reference":
        data["assessments"][0]["evidence_key"] = "missing"
    else:
        data["assessments"][0]["status_code"] = "INVALID"
    path.write_text(json.dumps(data))
    if failure != "hash":
        manifest_path = directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["payload_sha256"]["assessments.json"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
    before = dump(config)
    with pytest.raises(NutritionEvidenceSeedError):
        seed_nutrition_measure_evidence(config, seed_directory=directory)
    assert dump(config) == before


def test_production_promotion_matches_exact_accepted_data_a():
    spec = importlib.util.spec_from_file_location(
        "promote_b1", ROOT / "scripts/promote_pr6_data_b1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name, value in module.promote().items():
        assert (DEFAULT_SEED_DIRECTORY / name).read_bytes() == module.encoded(value)
    manifest, _, _ = load_seed_entries()
    import subprocess

    for path, digest in manifest["source_sha256"].items():
        assert (
            hashlib.sha256(
                subprocess.check_output(
                    ["git", "show", f"{manifest['source_merged_main']}:{path}"],
                    cwd=ROOT,
                )
            ).hexdigest()
            == digest
        )


def test_new_recipe_version_has_no_inherited_row_authority(seeded):
    config, engine = seeded
    from app.persistence.sqlalchemy_core.food_recipe_composition import (
        create_food_recipe_catalogue_service,
    )
    from app.seed.food_recipes import load_seed_entries as recipe_seeds

    recipes = create_food_recipe_catalogue_service(engine)
    existing = recipe_detail(engine)
    source = next(
        r for r in recipe_seeds() if r.canonical_code == "CACFP6_CORN_EDAMAME_BLEND"
    )
    new = recipes.append_trusted_version(
        existing.version.recipe_id,
        replace(
            source.version,
            source_version="synthetic-v2",
            change_note="Synthetic new version to test review boundary",
        ),
    )
    assert not {r.id for r in existing.ingredients} & {r.id for r in new.ingredients}
    result = create_nutrition_service(engine).recipe_version(new.version.id)
    assert sum(
        w.code == W.MISSING_NUTRITION_ASSESSMENT for w in result.warnings
    ) == len(new.ingredients)
    assert all(
        r.nutrition.mass_g is None
        for r in result.required_contributions + result.optional_contributions
    )
    assert recipes.get_version_detail(existing.version.id) == existing
    before = dump(config)
    with pytest.raises(NutritionEvidenceSeedError, match="no longer current"):
        seed_nutrition_measure_evidence(config)
    assert dump(config) == before


def test_source_hashes_fail_closed(tmp_path):
    manifest, _, _ = load_seed_entries()
    for path in manifest["source_sha256"] | manifest["production_input_sha256"]:
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, destination)
    source = tmp_path / next(iter(manifest["source_sha256"]))
    source.write_text(source.read_text() + " ")
    with pytest.raises(NutritionEvidenceSeedError, match="hash mismatch"):
        load_seed_entries(root=tmp_path)
