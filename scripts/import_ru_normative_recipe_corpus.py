#!/usr/bin/env python3
"""Import a Russian normative recipe source snapshot into the source corpus DB.

The command never publishes RecipeVersion/RecipeTemplate rows. It preserves raw
card text and optional structured source facts for later deterministic review.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.recipe_source_corpus import CorpusPublicationPolicy, CorpusRawFormat
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.recipe_source_corpus_repository import (
    SqlAlchemyRecipeSourceCorpusRepository,
)
from app.services.recipe_source_corpus_import import split_normative_cards, validate_bundle


def _read_source(path: Path | None, url: str | None) -> tuple[bytes, str, str]:
    if path is not None:
        raw = path.read_bytes()
        source_url = path.resolve().as_uri()
    elif url:
        request = Request(
            url,
            headers={"User-Agent": "FamilyFoodOS/recipe-source-import"},
        )
        with urlopen(request, timeout=60) as response:  # noqa: S310 - curator URL
            raw = response.read()
        source_url = url
    else:
        raise ValueError("--source or --url is required unless --bundle is used")
    if raw.startswith(b"%PDF"):
        completed = subprocess.run(
            ["pdftotext", "-layout", "-", "-"],
            input=raw,
            capture_output=True,
            check=True,
        )
        return raw, completed.stdout.decode("utf-8"), source_url
    return raw, raw.decode("utf-8"), source_url


def _bundle_from_source(raw: bytes, text: str, source_url: str, args) -> dict:
    cards = split_normative_cards(text)
    return {
        "document": {
            "source_code": args.source_code,
            "title_ru": args.title,
            "authority_ru": args.authority,
            "source_url": source_url,
            "source_version": args.source_version,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "raw_format": (
                CorpusRawFormat.PDF_TEXT if raw.startswith(b"%PDF") else CorpusRawFormat.TEXT
            ).value,
            "raw_bytes_sha256": sha256(raw).hexdigest(),
            "raw_text_sha256": sha256(text.encode("utf-8")).hexdigest(),
            "publication_policy": (
                CorpusPublicationPolicy.NORMATIVE_BASE_RECIPE_APPROVED.value
            ),
        },
        "cards": cards,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--url")
    parser.add_argument("--source-code", default="RU_MR_2_4_0162_19")
    parser.add_argument("--title", default="МР 2.4.0162-19 — технологические карты")
    parser.add_argument(
        "--authority",
        default="Роспотребнадзор / Главный государственный санитарный врач РФ",
    )
    parser.add_argument("--source-version", default="2019-12-30")
    parser.add_argument("--export-bundle", type=Path)
    args = parser.parse_args()

    if args.bundle:
        bundle = json.loads(args.bundle.read_text())
    else:
        raw, text, source_url = _read_source(args.source, args.url)
        bundle = _bundle_from_source(raw, text, source_url, args)
    if args.export_bundle:
        args.export_bundle.write_text(
            json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"
        )

    document, cards = validate_bundle(bundle)
    config = DatabaseConfig(path=args.database)
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        with engine.begin() as connection:
            repo = SqlAlchemyRecipeSourceCorpusRepository(connection)
            document_id, inserted = repo.import_document(document, cards)
            total = repo.card_count(document_id)
    finally:
        engine.dispose()
    print(
        json.dumps(
            {
                "document_id": str(document_id),
                "inserted_cards": inserted,
                "card_count": total,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
