# RU-NUT-DB Step 4 runtime publication payload

**Status:** reviewed production payload for the first five-food Russian batch
**Source snapshot:** `RU-NUT-DB` / 2026-09-20 / raw HTML SHA-256 `155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d`
**Mapping:** `data/curation/ru-nut-db-step4-semantic-closure/field-mapping.json`
**Publication payload SHA-256:** `ca27a1bcd69ac0020cd34616d91426f8f9f115ce853210b0e52a639cee96111f`

Данные о химическом составе продуктов предоставлены ФГБУН «ФИЦ питания и биотехнологии» (база «Химический состав пищевых продуктов, используемых в Российской Федерации»).

Источник: https://ion.ru/nauka/baza-dannykh-khimicheskogo-sostava/1-1-baza-dannykh/1.1_baza%20dannih.html

Пакет содержит только пять утверждённых записей Step 4 и все 26 исходных nutrient fields каждой записи. Runtime публикует только 18 полей, закреплённых Step 4B; остальные восемь сохраняются в source observations и не становятся canonical V2 truth.

Batch:
- `SUGAR` ← code 1150 / `/DB/252`;
- `CARROT_RED_RAW` ← code 1187 / `/DB/126`;
- `CABBAGE_GREEN` ← code 1184 / `/DB/69`;
- `BEET` ← code 1204 / `/DB/254`;
- `RICE_GROATS` ← code 66 / `/DB/103`.

Пакет не содержит полного исходного массива ФИЦ и не заменяет лицензионный authority receipt.
