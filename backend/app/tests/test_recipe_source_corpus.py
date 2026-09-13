import json
from hashlib import sha256
from pathlib import Path

import pytest

from app.domain.recipe_source_corpus import CorpusCaptureStatus, SourceCardInput
from app.services.recipe_source_corpus_import import (
    extract_sudact_card_links,
    split_normative_cards,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19_manifest.json"


def test_split_normative_cards_preserves_raw_blocks_and_appendix_context():
    text = """Приложение 5
ТЕХНОЛОГИЧЕСКАЯ КАРТА № 8.1
Наименование кулинарного изделия (блюда): Помидоры свежие
Источник рецептуры: Нормативный источник
Технология приготовления: Вымыть, нарезать на порции.
Сведения о пищевой ценности
Приложение 6
ТЕХНОЛОГИЧЕСКАЯ КАРТА N 8.1
Наименование блюда: Помидоры свежие
Источник рецептуры: Нормативный источник
"""
    cards = split_normative_cards(text)
    assert [row["source_card_code"] for row in cards] == ["8.1", "8.1"]
    assert [row["source_section_code"] for row in cards] == [
        "APPENDIX_5",
        "APPENDIX_6",
    ]
    assert cards[0]["name_ru"] == "Помидоры свежие"
    assert cards[0]["technology_text_ru"] == "Вымыть, нарезать на порции."
    for card in cards:
        assert card["raw_card_sha256"] == sha256(
            card["raw_card_text"].encode()
        ).hexdigest()


def test_sudact_link_parser_is_appendix_scoped_and_normalizes_suffixes():
    html = """
    <a href="/law/x/prilozhenie-5/supy/tekhnologicheskaia-karta-n-1.2a/">
      Технологическая карта N 1.2а
    </a>
    <a href="/law/x/prilozhenie-6/supy/tekhnologicheskaia-karta-n-1.2a/">
      Технологическая карта N 1.2а
    </a>
    """
    links = extract_sudact_card_links(
        html,
        "https://sudact.ru/law/x/prilozhenie-5/",
    )
    assert links == {
        "1.2а": "https://sudact.ru/law/x/prilozhenie-5/supy/tekhnologicheskaia-karta-n-1.2a/"
    }


def test_mr_manifest_has_all_214_section_scoped_cards():
    manifest = json.loads(MANIFEST.read_text())
    lookup = validate_manifest(manifest)
    assert manifest["expected_total_cards"] == 214
    assert {row["expected_card_count"] for row in manifest["appendices"]} == {
        33,
        45,
        60,
        76,
    }
    assert len(lookup) == 214
    assert lookup[("APPENDIX_5", "8.1")] == "Холодные блюда"
    assert lookup[("APPENDIX_6", "8.1")] == "Холодные блюда"
    assert lookup[("APPENDIX_8", "2.24")] == "Мясные блюда"


def test_domain_rejects_fabricated_hash():
    with pytest.raises(ValueError, match="raw_card_sha256"):
        SourceCardInput(
            source_section_code="APPENDIX_5",
            source_card_code="1.1",
            source_page_url="https://example.test/card/1.1",
            name_ru="Борщ",
            category_ru=None,
            source_recipe_basis=None,
            technology_text_ru=None,
            raw_card_text="источник",
            raw_card_sha256="0" * 64,
            capture_status=CorpusCaptureStatus.RAW_CAPTURED,
            variants=(),
        )
