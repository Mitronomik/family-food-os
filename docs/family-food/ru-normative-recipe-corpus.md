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

Такой контур позволяет загрузить сотни и тысячи нормативных карт без выдумывания
FoodIngredient identity и без ослабления production gates.

## Что сохраняется

Для документа: authority, source/version, URL, retrieval time, format и SHA-256.
Для карты: section/appendix identity, код, URL конкретной страницы, русское
название, источник рецептуры, технология, полный raw text и SHA-256. Для варианта:
возрастная/порционная ветка, выход, ingredient rows с брутто/нетто и
source-declared nutrient values.

`source_section_code` — часть identity карты. Это обязательно, потому что номера
вроде `8.1`, `1.2` или `2.1` повторяются в разных приложениях одного нормативного
документа и означают разные diet/context publications. Номер карты сам по себе не
является глобальным ключом.

Source-declared КБЖУ, витамины и минералы — **reference evidence**. Nutrition
FamilyFoodOS продолжает считать значения детерминированно из canonical
FoodIngredient/NutrientVector/Composition. Расхождение с картой становится review
signal, а не поводом подменить расчёт исходным итогом.

## МР 2.4.0162-19 — полный manifest

Для приложений 5–8 зафиксирован fail-closed manifest:

- `APPENDIX_5` — 76 технологических карт;
- `APPENDIX_6` — 45;
- `APPENDIX_7` — 33;
- `APPENDIX_8` — 58;
- всего — **212 section-scoped карт**.

Manifest находится в
`data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19_manifest.json` и содержит
ожидаемый код каждой карты и её категорию. Bulk crawler обязан получить ровно этот
набор: пропуск, лишняя карточка, дублирование или изменение appendix index приводят
к fail-closed ошибке, а не к частичному «успешному» импорту.

## Миграции

`0030_recipe_source_corpus` принадлежит source-corpus ingestion и не является
RecipeTemplate schema. Планировавшийся `0030_recipe_template_catalogue` сдвигается
на `0031_recipe_template_catalogue` после завершения evidence gates Assembly A.

## Массовый импорт из полного документа

Прямой PDF/text snapshot поддерживается:

```bash
AI_ENABLED=false PYTHONPATH=backend:. backend/.venv/bin/python \
  scripts/import_ru_normative_recipe_corpus.py \
  --database /path/to/family-food.sqlite \
  --source /path/to/mr-2.4.0162-19.pdf \
  --source-code RU_MR_2_4_0162_19 \
  --title "МР 2.4.0162-19 — технологические карты" \
  --authority "Роспотребнадзор / Главный государственный санитарный врач РФ" \
  --source-version 2019-12-30
```

PDF преобразуется через `pdftotext -layout`. Parser распознаёт и `N`, и `№`, а
для полного документа автоматически связывает карту с ближайшим заголовком
`Приложение 5`…`Приложение 8`, поэтому одинаковые номера между приложениями не
сливаются.

## Массовый импорт через постраничное HTML-зеркало

Когда единый PDF недоступен среде исполнения, importer умеет собрать тот же
корпус по appendix indexes и отдельным страницам Sudact. По умолчанию используется
проверяемый manifest:

```bash
AI_ENABLED=false PYTHONPATH=backend:. backend/.venv/bin/python \
  scripts/import_ru_normative_recipe_corpus.py \
  --database /path/to/family-food.sqlite \
  --sudact-manifest data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19_manifest.json \
  --export-bundle /path/to/mr-2.4.0162-19.bundle.json
```

Crawler сначала сверяет каждый appendix index с manifest, затем получает каждую
из 212 страниц, сохраняет `source_page_url`, raw-card text и SHA-256 и только
после полного прохода импортирует документ. Если хотя бы одна ожидаемая карта
недоступна, операция завершается ошибкой до записи неполного corpus snapshot.

Повтор того же source snapshot идемпотентен; новая редакция/изменившийся snapshot
создаёт новую document revision.

## Bootstrap

`data/seed/ru_normative_recipe_corpus/bootstrap.json` содержит шесть
структурированных карт, фактически предоставленных пользователем в исходной
постановке задачи. Это regression/bootstrap fixture для проверки схемы и
структурированных полей. Он не заменяет полный manifest из 212 карт.

## Граница публикации

Наличие карты в source corpus означает только, что нормативный источник сохранён
и доступен для последующей обработки. Это не разрешение автоматически:

- сопоставлять неоднозначную строку с `FoodIngredient`;
- придумывать отсутствующую массу или food form;
- принимать source-declared nutrition за Nutrition truth;
- публиковать RecipeVersion/RecipeTemplate без deterministic review.

Массовое сохранение источника и production publication — две разные операции.
