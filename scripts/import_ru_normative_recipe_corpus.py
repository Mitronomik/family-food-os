"""Import Russian normative recipe source snapshots into the source corpus DB.

The command never publishes RecipeVersion/RecipeTemplate rows. It preserves raw
card text and optional structured source facts for later deterministic review.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
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
from app.services.recipe_source_corpus_import import (
    extract_single_normative_card,
    extract_sudact_card_links,
    html_to_text,
    split_normative_cards,
    validate_bundle,
    validate_manifest,
)

DEFAULT_MANIFEST = (
    ROOT / "data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19_manifest.json"
)


def _download_url(url: str, *, attempts: int = 3) -> bytes:
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; FamilyFoodOS recipe-source import)"
                    ),
                    "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8",
                },
            )
            with urlopen(request, timeout=60) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001 - preserve final acquisition failure
            error = exc
            if attempt + 1 < attempts:
                time.sleep(1 + attempt)
    raise RuntimeError(f"Не удалось получить нормативный источник: {url}") from error


def _read_source(path: Path | None, url: str | None) -> tuple[bytes, str, str]:
    if path is not None:
        raw = path.read_bytes()
        source_url = path.resolve().as_uri()
    elif url:
        raw = _download_url(url)
        source_url = url
    else:
        raise ValueError("--source or --url is required unless another mode is used")
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
                CorpusRawFormat.PDF_TEXT
                if raw.startswith(b"%PDF")
                else CorpusRawFormat.TEXT
            ).value,
            "raw_bytes_sha256": sha256(raw).hexdigest(),
            "raw_text_sha256": sha256(text.encode("utf-8")).hexdigest(),
            "publication_policy": (
                CorpusPublicationPolicy.NORMATIVE_BASE_RECIPE_APPROVED.value
            ),
        },
        "cards": cards,
    }


def _bundle_from_sudact_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text())
    lookup = validate_manifest(manifest)
    cards: list[dict] = []
    raw_snapshot = bytearray()
    text_snapshot: list[str] = []
    retrieved_at = datetime.now(timezone.utc).isoformat()

    for appendix in manifest["appendices"]:
        section = appendix["source_section_code"]
        appendix_url = appendix["url"]
        appendix_html_bytes = _download_url(appendix_url)
        appendix_html = appendix_html_bytes.decode("utf-8", errors="replace")
        discovered = extract_sudact_card_links(appendix_html, appendix_url)
        expected_codes = {
            code
            for (manifest_section, code), _category in lookup.items()
            if manifest_section == section
        }
        missing = sorted(expected_codes - set(discovered))
        unexpected = sorted(set(discovered) - expected_codes)
        if missing or unexpected:
            raise ValueError(
                f"Sudact index drift for {section}; missing={missing}, "
                f"unexpected={unexpected}"
            )
        if len(discovered) != appendix["expected_card_count"]:
            raise ValueError(
                f"Sudact count drift for {section}: "
                f"{len(discovered)} != {appendix['expected_card_count']}"
            )

        for category, values in appendix["categories"].items():
            for expected_code in values:
                canonical_code = _canonical_manifest_code(expected_code)
                card_url = discovered[canonical_code]
                page_bytes = _download_url(card_url)
                page_html = page_bytes.decode("utf-8", errors="replace")
                page_text = html_to_text(page_html)
                card = extract_single_normative_card(
                    page_text,
                    expected_code=canonical_code,
                    source_section_code=section,
                    source_page_url=card_url,
                    category_ru=category,
                )
                cards.append(card)
                raw_snapshot.extend(card_url.encode("utf-8"))
                raw_snapshot.extend(b"\0")
                raw_snapshot.extend(len(page_bytes).to_bytes(8, "big"))
                raw_snapshot.extend(page_bytes)
                text_snapshot.extend(
                    [section, canonical_code, card_url, card["raw_card_text"]]
                )

    if len(cards) != manifest["expected_total_cards"]:
        raise ValueError(
            f"Sudact corpus count drift: {len(cards)} != "
            f"{manifest['expected_total_cards']}"
        )
    root_url = manifest["appendices"][0]["url"].split("/prilozhenie-5/")[0] + "/"
    canonical_text = "\n\u241e\n".join(text_snapshot)
    return {
        "document": {
            "source_code": manifest["source_code"],
            "title_ru": manifest["title_ru"],
            "authority_ru": manifest["authority_ru"],
            "source_url": root_url,
            "source_version": manifest["source_version"],
            "retrieved_at": retrieved_at,
            "raw_format": CorpusRawFormat.HTML.value,
            "raw_bytes_sha256": sha256(bytes(raw_snapshot)).hexdigest(),
            "raw_text_sha256": sha256(canonical_text.encode("utf-8")).hexdigest(),
            "publication_policy": (
                CorpusPublicationPolicy.NORMATIVE_BASE_RECIPE_APPROVED.value
            ),
        },
        "cards": cards,
    }


def _canonical_manifest_code(value: str) -> str:
    return "".join(value.strip().lower().replace("a", "а").replace("b", "б").split())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--url")
    parser.add_argument("--sudact-manifest", type=Path)
    parser.add_argument("--source-code", default="RU_MR_2_4_0162_19")
    parser.add_argument("--title", default="МР 2.4.0162-19 — технологические карты")
    parser.add_argument(
        "--authority",
        default="Роспотребнадзор / Главный государственный санитарный врач РФ",
    )
    parser.add_argument("--source-version", default="2019-12-30")
    parser.add_argument("--export-bundle", type=Path)
    args = parser.parse_args()

    selected_modes = sum(
        bool(value)
        for value in (args.bundle, args.source, args.url, args.sudact_manifest)
    )
    if selected_modes == 0:
        args.sudact_manifest = DEFAULT_MANIFEST
    elif selected_modes != 1:
        parser.error("choose exactly one of --bundle, --source, --url, --sudact-manifest")

    if args.bundle:
        bundle = json.loads(args.bundle.read_text())
    elif args.sudact_manifest:
        bundle = _bundle_from_sudact_manifest(args.sudact_manifest)
    else:
        raw, text, source_url = _read_source(args.source, args.url)
        bundle = _bundle_from_source(raw, text, source_url, args)
    if args.export_bundle:
        args.export_bundle.parent.mkdir(parents=True, exist_ok=True)
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
                "source_code": document.source_code,
                "source_version": document.source_version,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
