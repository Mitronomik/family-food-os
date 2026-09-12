# Российский нормативный корпус рецептур

## Решение

Нормативные и базовые рецептурные карты, явно разрешённые пользователем проекта,
могут сохраняться и публиковаться как фактические рецептурные данные без отдельного
rights-gate для каждой карты. Это решение не распространяется автоматически на
фотографии, издательскую вёрстку, логотипы или сторонние авторские комментарии.
Для каждой записи всё равно сохраняются источник, версия, URL, дата получения и
контрольные суммы доступного source snapshot.

## Почему это отдельный corpus

Массовая загрузка не создаёт `SOURCE_VERIFIED RecipeVersion` автоматически.
Сначала сохраняется source truth:

`SourceDocument → SourceCard → SourceVariant → source ingredients / declared nutrients`.

Позже Ingredient Resolver и Recipe Assembly связывают строки с `FoodIngredient`,
Composition, exact mass и transformation truth. Только прошедший review результат
может стать RecipeTemplate/RecipeVersion.

Такой контур позволяет загрузить тысячи нормативных карт без выдумывания
FoodIngredient identity и без ослабления production gates.

## Что сохраняется

Для документа: authority, source/version, URL, retrieval time, format и SHA-256.
Для карты: код, русское название, источник рецептуры, технология, полный raw text
и SHA-256. Для варианта: возрастная/порционная ветка, выход, ingredient rows с
брутто/нетто и source-declared nutrient values.

Source-declared КБЖУ, витамины и минералы — **reference evidence**. Nutrition
FamilyFoodOS продолжает считать значения детерминированно из canonical
FoodIngredient/NutrientVector/Composition. Расхождение с картой становится review
signal, а не поводом подменить расчёт исходным итогом.

## Миграции

`0030_recipe_source_corpus` принадлежит source-corpus ingestion и не является
RecipeTemplate schema. Планировавшийся `0030_recipe_template_catalogue` сдвигается
на `0031_recipe_template_catalogue` после завершения evidence gates Assembly A.

## Массовый импорт

Команда:

```bash
AI_ENABLED=false PYTHONPATH=backend:. backend/.venv/bin/python \
  scripts/import_ru_normative_recipe_corpus.py \
  --database /path/to/family-food.sqlite \
  --source /path/to/source.txt \
  --source-code RU_MR_2_4_0162_19 \
  --title "МР 2.4.0162-19 — технологические карты" \
  --authority "Роспотребнадзор / Главный государственный санитарный врач РФ" \
  --source-version 2019-12-30
```

PDF поддерживается через `pdftotext -layout`. Импорт lossless: каждая найденная
`Технологическая карта N ...` сначала сохраняется raw-блоком и хешем даже если
структурный parser ещё не умеет разобрать конкретную таблицу. Повтор того же
source snapshot идемпотентен; новая редакция добавляется отдельной revision.

`data/seed/ru_normative_recipe_corpus/bootstrap.json` содержит шесть
структурированных карт, фактически предоставленных пользователем в исходной
постановке задачи. Это bootstrap для проверки схемы и импортера, **не заявление,
что внешний нормативный документ уже целиком скачан этой сессией**.

## Source acquisition

Полное наполнение требует доступного полного source snapshot. Если сетевой fetch
недоступен в окружении разработки, допустимо сохранить PDF/HTML отдельно и
запустить тот же importer с `--source`. Запрещено заполнять пропущенные карты или
значения по догадке.
