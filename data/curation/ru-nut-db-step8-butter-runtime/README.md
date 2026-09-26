# RU-NUT-DB Step 8 butter runtime publication payload

**Status:** reviewed production payload for Step 8 recipe-dependency food publication
**Target recipe dependency:** School2022 `53-19з — Масло сливочное (порциями)`
**Source snapshot:** `RU-NUT-DB` / 2026-09-20 / raw HTML SHA-256 `155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d`
**Exact FIC record:** code `1417` / `/DB/533` / raw-object SHA-256 `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`
**Publication payload SHA-256:** `7a9c1ff26fe9accdb1ab22dcb8ee60e9310c8ca5e77a3e2b27dd79c4df98b5bd`

Данные о химическом составе продуктов предоставлены ФГБУН «ФИЦ питания и биотехнологии» (база «Химический состав пищевых продуктов, используемых в Российской Федерации»).

Источник: https://ion.ru/nauka/baza-dannykh-khimicheskogo-sostava/1-1-baza-dannykh/1.1_baza%20dannih.html

Пакет публикует ровно один новый `FoodIngredient`: `BUTTER_PEASANT_72_5_UNSALTED`.

Form binding: School2022 требует сливочное масло 72,5% и несолёную форму; exact FIC DB/533 публикует `salt_ad=0.0` (`Добавленная соль`). Это значение сохраняется как source-only evidence совместимости формы «без добавленной соли», не становится V2 nutrient и не означает нулевой sodium. Любой non-zero/null/missing `salt_ad` должен fail closed.

Из 26 frozen RU-NUT-DB source fields запись DB/533 содержит 25 numeric literals и `water=null`. Runtime сохраняет все 26 source observations, публикует 17 V2 values и оставляет WATER unknown. Восемь deferred/source-only concepts Step 4 остаются non-canonical.

Профиль non-current; ATOMIC composition = v1 / INPUT. Пакет не создаёт YieldModel, retention profile, FoodTransformation, TransformationApplicability, RecipeVersion или Planner state и не требует migration.
