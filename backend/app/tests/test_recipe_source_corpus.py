import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from app.domain.recipe_source_corpus import CorpusCaptureStatus, SourceCardInput
from app.services.recipe_source_corpus_import import (
    extract_single_normative_card,
    extract_sudact_card_links,
    split_normative_cards,
    validate_bundle,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19_manifest.json"
BOOTSTRAP = ROOT / "data/seed/ru_normative_recipe_corpus/bootstrap.json"


def test_split_normative_cards_preserves_raw_blocks_and_appendix_context():
    text = """Приложение 5
ТЕХНОЛОГИЧЕСКАЯ КАРТА № 8.1
Наименование кулинарного изделия (блюда): Помидоры свежие
Источник рецептуры: Нормативный источник
Технология приготовления: Вымыть, нарезать на порции.
Сведения о пищевой ценности
Приложение 6
ТЕХНОЛОГИЧЕСКАЯ N 1.1б
Наименование блюда: Борщ с капустой и картофелем на курином бульоне
Источник рецептуры: Нормативный источник
"""
    cards = split_normative_cards(text)
    assert [row["source_card_code"] for row in cards] == ["8.1", "1.1б"]
    assert [row["source_section_code"] for row in cards] == [
        "APPENDIX_5",
        "APPENDIX_6",
    ]
    assert cards[0]["name_ru"] == "Помидоры свежие"
    assert cards[0]["technology_text_ru"] == "Вымыть, нарезать на порции."
    for card in cards:
        assert (
            card["raw_card_sha256"]
            == sha256(card["raw_card_text"].encode()).hexdigest()
        )


def test_single_sudact_card_trims_navigation_and_page_chrome():
    text = """ТЕХНОЛОГИЧЕСКАЯ КАРТА N 8.1
Наименование блюда: Помидоры свежие
Источник рецептуры: Нормативный источник
Технология приготовления: Вымыть, нарезать на порции.
Сведения о пищевой и энергетической ценности 1 порции
50
0,5
← Технологическая карта N 8.0
Библиографические ссылки →
Все права защищены © 2012-2026
window.yaContextCb.push(() => {});
"""
    card = extract_single_normative_card(
        text,
        expected_code="8.1",
        source_section_code="APPENDIX_5",
        source_page_url="https://example.test/card/8.1",
        category_ru="Холодные блюда",
    )
    assert card["raw_card_text"].endswith("0,5")
    assert "←" not in card["raw_card_text"]
    assert "Все права защищены" not in card["raw_card_text"]
    assert (
        card["raw_card_sha256"]
        == sha256(card["raw_card_text"].encode("utf-8")).hexdigest()
    )


def test_single_sudact_card_fails_closed_without_page_boundary():
    text = """ТЕХНОЛОГИЧЕСКАЯ КАРТА N 8.1
Наименование блюда: Помидоры свежие
Технология приготовления: Вымыть.
"""
    with pytest.raises(ValueError, match="page boundary"):
        extract_single_normative_card(
            text,
            expected_code="8.1",
            source_section_code="APPENDIX_5",
            source_page_url="https://example.test/card/8.1",
            category_ru="Холодные блюда",
        )


def test_sudact_link_parser_accepts_karta_and_omitted_karta_slugs():
    html = """
    <a href="/law/x/prilozhenie-6/supy/tekhnologicheskaia-karta-n-1.2a/">
      Технологическая карта N 1.2а
    </a>
    <a href="/law/x/prilozhenie-6/supy/tekhnologicheskaia-n-1.1b/">
      Технологическая N 1.1б
    </a>
    <a href="/law/x/prilozhenie-7/supy/tekhnologicheskaia-n-1.1b/">
      Технологическая N 1.1б
    </a>
    """
    links = extract_sudact_card_links(
        html,
        "https://sudact.ru/law/x/prilozhenie-6/",
    )
    assert links == {
        "1.1б": "https://sudact.ru/law/x/prilozhenie-6/supy/tekhnologicheskaia-n-1.1b/",
        "1.2а": "https://sudact.ru/law/x/prilozhenie-6/supy/tekhnologicheskaia-karta-n-1.2a/",
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
    assert lookup[("APPENDIX_6", "1.1б")] == "Супы"
    assert lookup[("APPENDIX_8", "2.24")] == "Мясные блюда"


def test_bundle_rejects_duplicate_section_card_identity_even_when_raw_differs():
    bundle = json.loads(BOOTSTRAP.read_text())
    duplicate = deepcopy(bundle["cards"][0])
    duplicate["raw_card_text"] += "\nдругая фиксация той же карты"
    duplicate["raw_card_sha256"] = sha256(
        duplicate["raw_card_text"].encode("utf-8")
    ).hexdigest()
    bundle["cards"].append(duplicate)
    with pytest.raises(ValueError, match="Duplicate card identity"):
        validate_bundle(bundle)


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


def test_bundle_rejects_mutated_raw_text_with_stale_declared_hash():
    bundle = json.loads(BOOTSTRAP.read_text())
    validate_bundle(bundle)
    bundle["cards"][0]["raw_card_text"] += "\nподменённый текст"
    with pytest.raises(
        ValueError, match="raw_card_sha256 does not match raw_card_text"
    ):
        validate_bundle(bundle)


def test_bundle_requires_declared_card_hash():
    bundle = json.loads(BOOTSTRAP.read_text())
    del bundle["cards"][0]["raw_card_sha256"]
    with pytest.raises(ValueError, match="raw_card_sha256 is required"):
        validate_bundle(bundle)
