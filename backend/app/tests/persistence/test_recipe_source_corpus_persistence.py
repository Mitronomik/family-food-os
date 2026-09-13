import json
import sqlite3
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations, current_migrations
from app.domain.recipe_source_corpus import CorpusImportConflictError
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.recipe_source_corpus_repository import (
    SqlAlchemyRecipeSourceCorpusRepository,
)
from app.services.recipe_source_corpus_import import validate_bundle

ROOT = Path(__file__).resolve().parents[4]
CORPUS = ROOT / "data/seed/ru_normative_recipe_corpus"


def test_bootstrap_import_is_idempotent_and_does_not_publish_recipe_versions(tmp_path):
    config = DatabaseConfig(path=tmp_path / "corpus.sqlite")
    apply_migrations(config)
    assert "0030_recipe_source_corpus" in current_migrations(config)
    bundle = json.loads(
        (ROOT / "data/seed/ru_normative_recipe_corpus/bootstrap.json").read_text()
    )
    document, cards = validate_bundle(bundle)
    engine = create_sqlite_engine(config)
    try:
        with engine.begin() as connection:
            production_before = connection.exec_driver_sql(
                "SELECT COUNT(*) FROM food_recipe_versions"
            ).scalar_one()
            repo = SqlAlchemyRecipeSourceCorpusRepository(connection)
            document_id, inserted = repo.import_document(document, cards)
            assert inserted == 6
            assert repo.card_count(document_id) == 6
            assert (
                connection.exec_driver_sql(
                    "SELECT COUNT(*) FROM food_recipe_versions"
                ).scalar_one()
                == production_before
            )
        with engine.begin() as connection:
            production_before_repeat = connection.exec_driver_sql(
                "SELECT COUNT(*) FROM food_recipe_versions"
            ).scalar_one()
            repo = SqlAlchemyRecipeSourceCorpusRepository(connection)
            same_document_id, inserted = repo.import_document(document, cards)
            assert same_document_id == document_id
            assert inserted == 0
            assert repo.card_count(document_id) == 6
            assert (
                connection.exec_driver_sql(
                    "SELECT COUNT(*) FROM food_recipe_versions"
                ).scalar_one()
                == production_before_repeat
            )
    finally:
        engine.dispose()


def _database_dump(config):
    with sqlite3.connect(config.path) as db:
        return tuple(db.iterdump())


@pytest.fixture
def imported_bootstrap(tmp_path):
    config = DatabaseConfig(path=tmp_path / "conflict.sqlite")
    apply_migrations(config)
    bundle = json.loads((CORPUS / "bootstrap.json").read_text())
    engine = create_sqlite_engine(config)
    try:
        with engine.begin() as connection:
            document_id, inserted = SqlAlchemyRecipeSourceCorpusRepository(
                connection
            ).import_document(*validate_bundle(bundle))
            assert inserted == 6
        yield config, engine, bundle, document_id
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "scope,field,value",
    [
        ("document", "raw_text_sha256", "0" * 64),
        ("document", "title_ru", "Другое название"),
        ("document", "authority_ru", "Другой источник"),
        ("document", "source_url", "https://example.test/changed"),
        ("document", "retrieved_at", "2026-09-13T00:00:00+00:00"),
        ("document", "raw_format", "TEXT"),
        ("card", "source_section_code", "OTHER_APPENDIX"),
        ("card", "source_card_code", "OTHER_CARD"),
        ("card", "source_page_url", "https://example.test/changed"),
        ("card", "name_ru", "Другое блюдо"),
        ("card", "category_ru", "Другая категория"),
        ("card", "source_recipe_basis", "Другой источник рецептуры"),
        ("card", "technology_text_ru", "Другая технология"),
        ("card", "capture_status", "PARTIAL"),
        ("card", "raw_card_text", "Другая фиксация карты"),
        ("card", "variants", []),
        ("variant", "variant_code", "OTHER_VARIANT"),
        ("variant", "label_ru", "Другая порция"),
        ("variant", "position", 2),
        ("variant", "output_g", "251"),
        ("variant", "output_text", "Другой выход"),
        ("variant", "ingredients", []),
        ("variant", "declared_nutrients", []),
        ("ingredient", "name_ru", "Другой продукт"),
        ("ingredient", "gross_g", "41"),
        ("ingredient", "net_g", "41"),
        ("ingredient", "quantity_text", "Другое количество"),
        ("ingredient", "source_form_note", "Другая форма"),
        ("ingredient", "optional", True),
        ("nutrient", "nutrient_code", "OTHER_NUTRIENT"),
        ("nutrient", "value", "2"),
        ("nutrient", "unit", "mg"),
        ("nutrient", "source_label", "Другая подпись"),
        ("bundle", "cards", []),
    ],
    ids=lambda value: str(value),
)
def test_conflicting_repeat_rejects_without_any_writes(
    imported_bootstrap, scope, field, value
):
    config, engine, bundle, document_id = imported_bootstrap
    before = _database_dump(config)
    changed = deepcopy(bundle)
    card = changed["cards"][0]
    variant = card["variants"][0]
    target = {
        "bundle": changed,
        "document": changed["document"],
        "card": card,
        "variant": variant,
        "ingredient": variant["ingredients"][0],
        "nutrient": variant["declared_nutrients"][0],
    }[scope]
    target[field] = value
    if field == "raw_card_text":
        card["raw_card_sha256"] = sha256(value.encode("utf-8")).hexdigest()
    # An empty card set is rejected by bundle validation already; exercise the
    # repository's own identity/cardinality comparison directly in that case.
    document, cards = validate_bundle(changed if scope != "bundle" else bundle)
    if scope == "bundle":
        cards = ()
    with engine.begin() as connection:
        repo = SqlAlchemyRecipeSourceCorpusRepository(connection)
        changes_before = connection.exec_driver_sql(
            "SELECT total_changes()"
        ).scalar_one()
        # Catch inside the caller's transaction and allow it to commit: safety
        # must not depend on the caller rolling back after a conflict.
        with pytest.raises(
            CorpusImportConflictError, match="Конфликт повторного импорта"
        ):
            repo.import_document(document, cards)
        assert (
            connection.exec_driver_sql("SELECT total_changes()").scalar_one()
            == changes_before
        )
        assert repo.import_document(*validate_bundle(bundle)) == (document_id, 0)
    assert _database_dump(config) == before


def test_repeat_compares_persisted_values_independent_of_bundle_order(
    imported_bootstrap,
):
    config, engine, bundle, document_id = imported_bootstrap
    before = _database_dump(config)
    bundle["cards"].reverse()
    bundle["document"]["retrieved_at"] = "2026-09-12T03:00:00+03:00"
    for card in bundle["cards"]:
        for variant in card["variants"]:
            variant["declared_nutrients"].reverse()
            variant["output_g"] += ",00"
    with engine.begin() as connection:
        assert SqlAlchemyRecipeSourceCorpusRepository(connection).import_document(
            *validate_bundle(bundle)
        ) == (document_id, 0)
    assert _database_dump(config) == before


def test_frozen_214_card_bundle_repeat_and_late_conflict_leave_database_unchanged(
    tmp_path,
):
    raw_bundle = (CORPUS / "mr_2_4_0162_19.bundle.json").read_bytes()
    assert sha256(raw_bundle).hexdigest() == (
        "ee0aad55080ba09294625af57800172862a53293518f7869e1b974ed7e9ab0b7"
    )
    bundle = json.loads(raw_bundle)
    document, cards = validate_bundle(bundle)
    assert len(cards) == 214
    config = DatabaseConfig(path=tmp_path / "frozen.sqlite")
    apply_migrations(config)
    assert max(current_migrations(config)) == "0030_recipe_source_corpus"
    engine = create_sqlite_engine(config)
    try:
        with engine.begin() as connection:
            production_before = connection.exec_driver_sql(
                "SELECT * FROM food_recipe_versions"
            ).all()
            document_id, inserted = SqlAlchemyRecipeSourceCorpusRepository(
                connection
            ).import_document(document, cards)
            assert inserted == 214
        before = _database_dump(config)
        with engine.begin() as connection:
            repo = SqlAlchemyRecipeSourceCorpusRepository(connection)
            changes_before = connection.exec_driver_sql(
                "SELECT total_changes()"
            ).scalar_one()
            assert repo.import_document(document, cards) == (document_id, 0)
            assert repo.card_count(document_id) == 214
            # Conflict is at the last persisted identity, after earlier cards
            # have matched. Rehashing makes the changed bundle valid in-domain.
            last = max(
                bundle["cards"],
                key=lambda c: (c["source_section_code"], c["source_card_code"]),
            )
            last["raw_card_text"] += "\nконфликтующая фиксация"
            last["raw_card_sha256"] = sha256(last["raw_card_text"].encode()).hexdigest()
            with pytest.raises(CorpusImportConflictError):
                repo.import_document(*validate_bundle(bundle))
            assert (
                connection.exec_driver_sql("SELECT total_changes()").scalar_one()
                == changes_before
            )
            assert (
                connection.exec_driver_sql("SELECT * FROM food_recipe_versions").all()
                == production_before
            )
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
            assert (
                connection.exec_driver_sql("PRAGMA integrity_check").scalar_one()
                == "ok"
            )
        assert _database_dump(config) == before
    finally:
        engine.dispose()
