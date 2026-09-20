# Корпус v0.3 — согласование с DC1

Статус: **evidence/curation; публикация production не выполнена**.

Пакет связывает существующую работу с планом реализации, не заменяя canonical
[data-corpus-v1](../../../docs/family-food/data-corpus-v1.md).
[План продолжения](../../../docs/family-food/corpus-v03-integration-plan.md) и
`implementation-backlog.json` содержат 20 задач с критериями и откатом.

## Текущий статус и исторические pins

PR70 принят в main как `b9768984392982bd05d28fc0f7793453fe8378b5`.
`input-lock.json`, `git-inputs.json` и `summary.json` сохраняют исходную
сверку до merge. Поле `pr70_merged=false` относится только к тому снимку.
Финальный head PR70 `514c6b1` имеет тот же tree, что pin `c23227b`;
никакие численные данные или mappings от принятия PR не изменились.
Актуальный статус проекта хранится в `state/`, а не в generated receipts.

## Scope и фактический результат

Учтены 68 исторических семейств PR70, 96 его ingredient identities, 479 карт
v0.3, 1473 полных route IDs и 2693 исходных food occurrences. Это не 2693
канонических продукта. 184 группы одинаковых текстовых названий нужны только
для организации review. Совпадение имени/alias не доказывает форму, жирность,
состояние или одинаковый химсостав.

PR70@c23227b использует USSR82; v0.3 — другие издания. Точный cross-edition join
не установлен ни для одной карты. Это не утверждение, что блюда не похожи.
Прежние 33 accepted/alias mappings сохраняются только внутри namespace PR70;
их проверка формы и профиля остаётся необходимой. В accepted CSV seed 183
food/profile rows; это число строк seed, не число runtime entities после upgrades.

1113 книжных записей имеют metadata index. 52 визуальных и 382 машинных
reference profiles дают 412 уникальных source codes; пересечение 22 не удваивается.
Их значения здесь не объединяются и не публикуются. Привязка к source code
не является canonical FoodIngredient binding.

## Файлы и чтение

- `input-lock.json`: версия и SHA каждого внешнего входа; SHA исходного manifest.
- `generated/git-inputs.json`: фиксированные commits и хеши пяти Git CSV inputs.
- `generated/recipe-crosswalk.jsonl`: обе коллекции карт, отдельные издания.
- `generated/pr70-food-crosswalk.jsonl`: исходные accepted mapping dispositions;
  label hints в новом корпусе остаются непроверенными.
- `generated/food-demand.jsonl`: все вхождения, locator, process context hash,
  links на routes и bindings, ограничения nutrition и статус rights.
- `generated/route-index.jsonl`: выбранные ветви и полный список food dependencies;
  карты, selection и process routes не схлопываются в один рецепт.
- `generated/book-reference-index.jsonl`: исходные коды, страницы, review layers;
  без таблиц пищевой ценности и текста книг.
- `generated/food-review-groups.jsonl`: поиск по точному нормализованному имени;
  canonical codes и book IDs только подсказки, значения UUID не присваиваются.
- `generated/review-batches.json`: 8 food-review queues и 38 recipe-review queues.
- `generated/summary.json`: фактические количества и незакрытые условия.
- `generated/checksums.sha256`: целостность всех generated outputs.

Food queues идут по числу затрагиваемых материально разрешённых неклинических
карт, затем по стабильному ID; максимум 25 lexical groups на очередь. Это **не**
обещание опубликовать 25 foods. Recipe queues учитывают все 377 material-ready
неклинических routes по 10; сначала меньше зависимостей, затем ID. 376 имеют
procurement readiness. Остальные routes остаются в полном индексе с blockers.
Меню и разнообразие не приняты этим техническим порядком: до первой DC3
publication партии нужно выбрать полезный ассортимент и конкретные ветви.

Ни одна очередь пока не является пригодным к записи publication manifest.
Неизвестные формы, права, углеводы, source zero policy, sealed vectors,
process nutrition и allergen applicability остаются явными review gates.
Хранение и российская методика потребностей не предоставляются совпадением имён.

## Воспроизведение

Требуется Python 3.10+, Git; runtime, backend DB, AI и сеть при сборке не нужны,
если Git objects и source package уже доступны. Получить в локальный object store
commits из `input-lock.json`: main base и head PR70. При отсутствии commit
`git show` завершится ошибкой, а не подставит текущий main.

Оператор предоставляет неизменённый corpus v0.3 из сохранённого выпуска:
`FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`. ZIP SHA указан в lock; после распаковки
его root называется `corpus-work/`. Укажите каталог, где лежит `manifest.json`.
Это внешний operator-managed artifact; публичная доступность и права
распространения не предполагаются. Репозиторий содержит только metadata,
ссылки и review dispositions, без книг, полных технологий или таблиц нутриентов.

```sh
python3 scripts/build_corpus_v03_reconciliation.py --corpus "$CORPUS_PATH" --output "$OUTPUT_PATH"
python3 scripts/validate_corpus_v03_reconciliation.py "$OUTPUT_PATH"
python3 scripts/test_corpus_v03_reconciliation.py
```

Builder проверяет исходный manifest и все используемые файлы по хешам.
Изменённый/отсутствующий файл блокирует сборку. Полная реконструкция требует
внешнего пакета; обычная CI проверяет committed metadata без исходных книг.
Хранилище исходников и право их использования должны быть приняты отдельно до
production publication. Один временный CI artifact не является таким хранилищем.

## Acceptance и ограничения задачи

Goal: preserve prior evidence, account for source identities, prepare exact-ID
review queues and roadmap handoff. Data model/API/UI/migrations/runtime: N/A.
Non-goals: publish foods/recipes, settle new nutrient authority, merge PR70,
change Planner, Retail/prices/availability or create a generalized importer.

Проверки: bounded curation + docs tier; два byte-identical rebuild, hash rejection,
referential integrity, queue partitions, historical separation, failed promotion,
clinical exclusion, deterministic generation, Ruff, whitespace and link checks.
Полный backend regression не требуется: runtime и accepted data не изменяются.

Риск: очередь проверки может ошибочно восприниматься как разрешение импорта.
Все строки явно `publication_ready=false`, все новые canonical food IDs null.
Следующий результат — не ещё одна очередь, а reviewed mapping/authority decisions
по конкретным строкам первой DC2 партии, затем отдельный publication PR.

Откат: revert только файлов этого metadata/doc/tool пакета; исходники,
accepted runtime, PR70 и исторические рецепты остаются неизменными.
