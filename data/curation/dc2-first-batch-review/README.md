# DC2 — предметная проверка первой партии

**Статус:** первая очередь review рассмотрена; публикация DC2 не выполнена.
База: `9b1d5c73da4f1d779336a35e0e7e2c2d32363e85` (PR71 merged).

## Результат

25 групп `DC2-REVIEW-001` получили конкретные решения, кандидатов источников,
отклонённые подстановки и следующий проверяемый шаг. Охвачены 1532 вхождения;
это групповая проверка с сохранением исходного контекста, а не 1532 индивидуально
принятых FoodIngredient mapping. Найдены 24 точных record IDs книги 2002;
14 имеют ранее визуально проверенные профили. Кандидат источника не означает
пригодность к публикации.

Независимо пересчитаны 359 затронутых материально разрешённых неклинических
маршрутов. У 91 все food dependencies попали в область текущего review.
**Разблокированных для production рецептов: 0.** Это область работ, не процент
готовности и не доказательство достаточного разнообразия.

Конкретный прогресс относительно PR71:

- найдены исходные record IDs и страницы вместо одного совпадения названий;
- сохранены существующие source descriptions USDA, выявлены слишком узкие
  профили картофеля gold, жёлтого лука и линолевого подсолнечного масла;
- проверено несовпадение школьной сметаны 15% с existing full-fat profile;
- жирность школьных молочных ингредиентов привязана к §1.4, pdf page4;
- солёное/несолёное масло и пастеризованное/стерилизованное молоко не выбраны
  произвольно;
- вода не получила выдуманный российский профиль; сухой чай не заменён напитком;
- source field states сохранены без численного копирования или обнуления missing.

## Файлы

`decisions.json` — 25 review decisions с причинами и конкретным дальнейшим действием.
`input-lock.json` — хеши используемых внешних файлов неизменённого v0.3.
`generated/group-reviews.json` — source candidates и existing profile evidence.
`generated/profile-reviews.json` — страницы, review layer, basis и field states.
`generated/occurrence-reviews.json` — все1532 IDs с locator и process hash.
`generated/route-impact.json` — влияние на каждый из359 маршрутов.
`generated/input-receipt.json` и `checksums.sha256` — происхождение/целостность.
`publication-decisions.md` — точные нерешённые условия и варианты решения.

## Воспроизведение

Использовать внешний corpus v0.3 из выпуска, закреплённого в
[reconciliation package](../corpus-v03-reconciliation/README.md).
Без исходников обычная CI проверяет committed metadata и репозиторные inputs.

```sh
python3 scripts/build_dc2_first_batch_review.py --corpus "$CORPUS_PATH" --output "$OUTPUT_PATH"
python3 scripts/test_dc2_first_batch_review.py
ruff check scripts/build_dc2_first_batch_review.py scripts/test_dc2_first_batch_review.py
```

Два полных rebuild дали одинаковые bytes. 10 тестов проверяют ключевые
ограничения: salt/tea proxies, молочную форму, source provenance, неизвестные
значения, дубли и сохранение pending mapping. Независимый QA проверил source IDs,
полное покрытие очереди и route impact. Production runtime не меняется;
полный backend regression для этой evidence-only задачи не требуется.

## Task contract

Goal: exact-source/form review of the first existing DC2 queue.
Scope: curation decisions, immutable input references, reproducible review output,
policy proposal and task state. Non-goals: publication, accepted registry changes,
schema/API/UI/Planner changes, source contact, purchases, prices/availability.
Architecture: current FoodIngredient/Nutrition/Composition contracts unchanged;
source ID is not a platform UUID. Data/API/UI changes: runtime N/A.
Acceptance: queue coverage exact; evidence references valid; mismatches explicit;
no unknown→zero, source-method conflation or automatic authority adoption.
Rollback: revert this review package; existing sources/mappings/runtime remain.
Follow-up: resolve conditions in publication-decisions.md, then create a separately
reviewed publication payload; do not relabel this queue as production-ready.
