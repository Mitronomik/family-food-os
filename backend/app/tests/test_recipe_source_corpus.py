from hashlib import sha256

import pytest

from app.domain.recipe_source_corpus import card_from_dict
from app.services.recipe_source_corpus_import import split_normative_cards


def test_split_normative_cards_preserves_each_raw_block():
    text = """Супы
Технологическая карта N 1.1
Наименование блюда: Борщ
Источник рецептуры: Нормативный источник
Технология приготовления: Варить до готовности.
Сведения о пищевой ценности
---
Технологическая карта N 6.4
Наименование блюда: Каша гречневая молочная
Источник рецептуры: Нормативный источник
"""
    cards = split_normative_cards(text)
    assert [row["source_card_code"] for row in cards] == ["1.1", "6.4"]
    assert cards[0]["name_ru"] == "Борщ"
    assert cards[0]["technology_text_ru"] == "Варить до готовности."
    for card in cards:
        assert card["raw_card_sha256"] == sha256(
            card["raw_card_text"].encode()
        ).hexdigest()


def test_card_validation_rejects_fabricated_hash():
    with pytest.raises(ValueError, match="raw_card_sha256"):
        card_from_dict(
            {
                "source_card_code": "1.1",
                "name_ru": "Борщ",
                "raw_card_text": "источник",
                "raw_card_sha256": "0" * 64,
                "capture_status": "RAW_CAPTURED",
                "variants": [],
            }
        )
