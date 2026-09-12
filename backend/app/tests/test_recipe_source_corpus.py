from hashlib import sha256

import pytest

from app.domain.recipe_source_corpus import CorpusCaptureStatus, SourceCardInput
from app.services.recipe_source_corpus_import import split_normative_cards


def test_split_normative_cards_preserves_raw_blocks_and_appendix_context():
    text = """Приложение 5
ТЕХНОЛОГИЧЕСКАЯ КАРТА № 8.1
Наименование кулинарного изделия (блюда): Помидоры свежие
Источник рецептуры: Нормативный источник
Технология приготовления: Вымыть, нарезать на порции.
Сведения о пищевой ценности
Приложение 6
ТЕХНОЛОГИЧЕСКАЯ КАРТА №8.1
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


def test_domain_rejects_fabricated_hash():
    with pytest.raises(ValueError, match="raw_card_sha256"):
        SourceCardInput(
            source_section_code="APPENDIX_5",
            source_card_code="1.1",
            name_ru="Борщ",
            category_ru=None,
            source_recipe_basis=None,
            technology_text_ru=None,
            raw_card_text="источник",
            raw_card_sha256="0" * 64,
            capture_status=CorpusCaptureStatus.RAW_CAPTURED,
            variants=(),
        )
