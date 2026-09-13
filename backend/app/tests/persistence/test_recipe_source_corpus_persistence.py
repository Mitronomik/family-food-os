import json
from pathlib import Path

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations, current_migrations
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.recipe_source_corpus_repository import (
    SqlAlchemyRecipeSourceCorpusRepository,
)
from app.services.recipe_source_corpus_import import validate_bundle

ROOT = Path(__file__).resolve().parents[4]


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
