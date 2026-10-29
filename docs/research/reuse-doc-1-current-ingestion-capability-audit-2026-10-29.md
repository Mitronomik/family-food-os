# REUSE-DOC-1 — аудит существующих ingestion/reuse capabilities

**Дата:** 2026-10-29. **Issue:** [#250](https://github.com/Mitronomik/family-food-os/issues/250).

**Статус:** исследовательский отчёт для независимого review. Не ADR, не approval
интеграции, не новая архитектура и не разрешение на следующую задачу.

**Accepted baseline:** `main@59298e8cb2bb5abfd0a662a2e8191866d22416cf`.
Все ссылки на repository files и номера строк ниже относятся к этому SHA,
если явно не указано иное. Ветка доставки:
`docs/reuse-doc-1-capability-audit-2026-10-29`.

## FACT

### 1. Baseline, полномочия и метод

PR [#249](https://github.com/Mitronomik/family-food-os/pull/249) merged
2026-10-29 в указанный baseline. Его
[Research RFC](integration-reuse-2026-10-29.md) прочитан полностью;
исторический снимок `3c4645a…` и финальное обновление RFC `edba04d…` не являются
текущим baseline этого аудита. Merge исследования не утверждает его интеграции.

Прочитаны [root AGENTS](../../AGENTS.md),
[current-focus](../../state/current-focus.md), [docs AGENTS](../AGENTS.md),
scoped [backend](../../backend/AGENTS.md),
[app](../../backend/app/AGENTS.md),
[persistence](../../backend/app/persistence/AGENTS.md) и
[scripts](../../scripts/AGENTS.md) для соответствующего осмотра;
[Operating Manual](../family-food/project-operating-manual.md),
[Master Roadmap](../family-food/master-roadmap.md) и addenda
[09-13](../family-food/master-roadmap-addendum-2026-09-13.md),
[09-16](../family-food/master-roadmap-addendum-2026-09-16.md),
[post-PR51](../family-food/master-roadmap-addendum-2026-09-17-post-pr51.md),
[DATA-CORPUS](../family-food/master-roadmap-addendum-2026-09-19-data-corpus.md),
[Architecture](../family-food/architecture.md),
[Security](../family-food/security-architecture.md),
[DATA-CORPUS-V1](../family-food/data-corpus-v1.md),
[Data Ingestion](../family-food/data-ingestion.md),
[RU normative corpus](../family-food/ru-normative-recipe-corpus.md),
[Composition](../family-food/food-composition-and-assembly.md),
[transactional nutrition publication](../family-food/transactional-nutrition-publication-contract.md),
[Recipe V2 consumption](../family-food/recipe-v2-nutrition-planner-integration-contract.md)
и релевантные PR10 gates (§6).

Сверены исходники, тестовые сценарии, manifests и CI; код не исполнялся для
публикации данных. Наличие теста ниже означает проверенную спецификацию/реализацию
теста, **не новый успешный запуск**. Это аудит границ, не повторная сертификация
всего production-каталога или всех исторических evidence receipts.

Верхняя запись current-focus описывает доставку #248 и содержит историческое
ожидание review. GitHub подтверждает, что #248 уже merged; принимаются его
contract/evidence результаты, но не предполагается разрешение на runtime.
Issue #250 отдельно разрешает только этот параллельный docs-only аудит;
`state/*` не обновляется.

### 2. Source → publication: уже реализованные ступени

```text
Controlled PDF/text/HTML acquisition или проверенный offline bundle
→ SourceDocument / SourceCard / SourceVariant + raw/text hashes
→ source-specific curation / quantity normalization / reviewed mappings
→ canonical FoodIngredient + exact unit/form/mass + nutrition authority
→ trusted reviewed seed/publication request
→ immutable RecipeVersion / Nutrition versions
→ existing Planner / Serving / Shopping
```

Эти ступени нельзя объединять в «парсер импортирует готовый рецепт».
`split_normative_cards` захватывает raw cards и оставляет `variants=[]`;
source-corpus extraction само по себе не заполняет все структурированные факты.
`RecipeCandidate` из RFC — концептуальное имя, а не найденный food-runtime DTO.
Legacy `ImportDraft`/`ParsedRow` из cosmetic import не является его реализацией.

### 3. Реестр code/test/CI evidence

| ID / capability | Существующая реализация, точка входа | Проверенные тесты / evidence и предел вывода |
| --- | --- | --- |
| E1 Source capture | [recipe_source_corpus_import.py](../../backend/app/services/recipe_source_corpus_import.py):94–171 `html_to_text`, `extract_sudact_card_links`, `split_normative_cards`; :198–223 `extract_single_normative_card`; `validate_manifest`, `validate_bundle` | [test_recipe_source_corpus.py](../../backend/app/tests/test_recipe_source_corpus.py): raw blocks/appendix, page boundary rejection, duplicate identity, missing/stale/fabricated hashes. Это RU normative extraction, не универсальный schema.org extractor. |
| E2 Durable source staging | [recipe_source_corpus.py](../../backend/app/domain/recipe_source_corpus.py): `SourceDocumentInput`, `SourceCardInput`; [import_ru_normative_recipe_corpus.py](../../scripts/import_ru_normative_recipe_corpus.py) — PDF/text, manifest acquisition, offline bundle | [persistence tests](../../backend/app/tests/persistence/test_recipe_source_corpus_persistence.py); [manifest](../../data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19_manifest.json) и [bundle](../../data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19.bundle.json). 214 section-scoped cards — конкретный dataset, не domain invariant. Source capture не публикует RecipeVersion. |
| E3 Candidate curation/quantity | [build_pr4_recipe_seed.py](../../scripts/build_pr4_recipe_seed.py):95–179 `_normalize_quantity`, `_number`: дроби, lb/oz→g, source US volume→ml, pcs без выдуманной массы; [DC1 builder](../../scripts/build_data_corpus_v1_dc1.py) и [validator](../../scripts/validate_data_corpus_v1_dc1.py) | [test_food_recipe_seed.py](../../backend/app/tests/test_food_recipe_seed.py): exact accepted structure/provenance, mapping/step drift, atomic replay/conflict. [DC1 tests](../../scripts/test_data_corpus_v1_dc1.py). Нормализация source-specific; условная вода и volume conventions не универсальная политика для нового источника. |
| E4 Canonical identity | [food_ingredients.py](../../backend/app/domain/food_ingredients.py): `normalize_unicode_search_key`, canonical food/alias/unit validation; [food_recipes service](../../backend/app/services/food_recipes.py): `TrustedRecipeIngredientSeed`, `FoodIngredientResolutionError` | [food recipe application tests](../../backend/app/tests/test_food_recipe_application.py) и [seed tests](../../backend/app/tests/test_food_recipe_seed.py): неизвестный/inactive ingredient, rollback. Совпадение текста не устанавливает raw/cooked form, edible basis, grams или права. |
| E5 Trusted Recipe publication | [food_recipes.py](../../backend/app/services/food_recipes.py):47–85 `TrustedRecipeIngredientSeed`, `TrustedRecipeVersionSeed`; `FoodRecipeCatalogueService.create_trusted`, `append_trusted_version_in_scope`, `reconcile_seed`; [domain](../../backend/app/domain/food_recipes.py): `RecipeVersion`, rights/source status | [seed tests](../../backend/app/tests/test_food_recipe_seed.py), [repository tests](../../backend/app/tests/persistence/test_food_recipe_repository.py), [same-source revisions](../../backend/app/tests/test_recipe_same_source_revisions.py): immutable history, exact replay/conflict и source changes. DTO со словом Trusted — граница уже проверенного ввода, не результат внешнего парсера. |
| E6 FDC baseline | [seed/food_ingredients.py](../../backend/app/seed/food_ingredients.py):30–32 source allowlist; :39–158 `load_seed_entries`; :160–171 `seed_food_ingredients`; [nutrition.csv](../../data/seed/food_ingredients/nutrition.csv) | Уже принимает `USDA_FDC` Foundation/SR Legacy, source ID/version/type, basis, Decimal и trusted catalogue/UoW. Это реальная существующая загрузка, не missing integration. Legacy seed не равен всей текущей V2 authority. |
| E7 Nutrition publication/consumption | [nutrition_publication.py](../../backend/app/services/nutrition_publication.py), [recipe_nutrition_v2.py](../../backend/app/domain/recipe_nutrition_v2.py): reviewed publication, explicit versioned recipe nutrition | [test_transactional_nutrition_publication.py](../../backend/app/tests/test_transactional_nutrition_publication.py): fresh partial unknown, zero-write replay, current-profile preservation, rollback/commit failure; [test_recipe_nutrition_v2.py](../../backend/app/tests/test_recipe_nutrition_v2.py): canonical V2 path. Внешнее заявленное КБЖУ не заменяет этот расчёт. |
| E8 Pantry | [pantry.py](../../backend/app/services/pantry.py): `PantryService`, `add_stock`, подтверждённые movements | [test_pantry_application.py](../../backend/app/tests/test_pantry_application.py) и [repository tests](../../backend/app/tests/persistence/test_pantry_repository.py): Household/transaction guards и отрицательный запас. Grocy stock ledger был бы вторым владельцем тех же остатков; FEFO не доказывает food safety. |
| E9 Planner / Serving | [planner service](../../backend/app/services/planner.py): `PlannerService`; [meal_plans.py](../../backend/app/domain/meal_plans.py): `MealPlan`, `Serving`; [Planner domain](../../backend/app/domain/planner.py) | [test_planner_gate1_fixtures.py](../../backend/app/tests/test_planner_gate1_fixtures.py), [test_meal_plan_source_contract.py](../../backend/app/tests/test_meal_plan_source_contract.py). Уже есть deterministic planning, individual Decimal servings, mixed-source representation. Representable source не означает admitted/prepared supply. |
| E10 Shopping | [shopping_calculation.py](../../backend/app/domain/shopping_calculation.py): `ShoppingQuantity`, `ShoppingLotAllocation`, `ShoppingUnresolvedReason`, `shopping-v1a`; [shopping.py](../../backend/app/services/shopping.py) | [calculation tests](../../backend/app/tests/test_shopping_calculation.py), [persistence tests](../../backend/app/tests/persistence/test_shopping_persistence.py), [API tests](../../backend/app/tests/test_shopping_api.py) и [.github workflows](../../.github/workflows/pr9-a-shopping-calculation.yml), [persistence](../../.github/workflows/pr9-b-shopping-persistence.yml), [API](../../.github/workflows/pr9-c-shopping-api.yml). Decimal/FEFO, immutable source snapshots и idempotency уже реализованы; generation не расходует Pantry. |
| E11 FBG / AFRS evidence | [garlic-mass-review.json](../../data/curation/recipe-assembly-a-r2/garlic-mass-review.json), [source-manifest](../../data/curation/recipe-assembly-a-r2/source-manifest.json), [rice-rights-review](../../data/curation/recipe-assembly-a-r2/rice-rights-review.json) | FBG `FBG-A-2025-A5-GARLIC` уже использован: `REVIEWED_R2_EVIDENCE_ONLY`, `production_mass_row_created=false`, `universal_density_g_ml=null`. AFRS excerpts также уже представлены в repository evidence. Это не новая общая yield/portion authority и не лицензия на весь источник. |
| E12 CI / corpus scope | [Docs verification](../../.github/workflows/docs-verification.yml), [DC1](../../.github/workflows/dc1-verification.yml), [DC4](../../.github/workflows/dc4-corpus-readiness.yml), [source artifacts](../../data/curation/data-corpus-v1-dc1/source-artifacts.json), [reconciliation lock](../../data/curation/corpus-v03-reconciliation/input-lock.json) | Docs CI проверяет whitespace/staged paths/relative link existence. Corpus workflows не запускаются этим аудитом и не доказывают права на новый HTML. Operator-managed XLSX и pinned normalized inputs не равны representative web recipe corpus. |

Дополнительные точные seams, которые новый importer не должен дублировать:

- E2 persistence: [recipe_source_corpus_repository.py](../../backend/app/persistence/sqlalchemy_core/recipe_source_corpus_repository.py):28–139,
  `SqlAlchemyRecipeSourceCorpusRepository.import_document`, `_assert_exact_repeat`,
  `_matching_children`; тесты exact replay, conflicting repeat без записей,
  order independence и отсутствие RecipeVersion publication.
- E4 mass evidence: [nutrition_evidence.py](../../backend/app/domain/nutrition_evidence.py):
  `MeasureMassEvidence`; [nutrition.py](../../backend/app/domain/nutrition.py):315–362
  `_row_mass`; [tests](../../backend/app/tests/test_nutrition_evidence_domain.py)
  проверяют exact fraction, запрет density/grams fallback, estimate exclusion,
  semantic blockers и stale binding.
- E5 права и accepted seed: [seed/food_recipes.py](../../backend/app/seed/food_recipes.py):405–474
  `_validate_provenance` сверяет approved manifest/corpus, URL/version/hash,
  rights и исходные servings. [r1b_reviewed_recipes.py](../../backend/app/seed/r1b_reviewed_recipes.py)
  `load_r1b_recipe_seeds`, `seed_r1b_recipes` и
  [tests](../../backend/app/tests/test_r1b_reviewed_recipes.py) проверяют более поздние
  reviewed publication packages. Это не legal clearance произвольного входа.
- E6 дополнительно: [b2b2_vector_import.py](../../backend/app/domain/b2b2_vector_import.py)
  и [ru_food_vector_import.py](../../backend/app/domain/ru_food_vector_import.py),
  `prepare_reviewed_source`, уже проверяют exact FDC record/release/basis и
  nutrient mapping; [ru_food_data seed](../../backend/app/seed/ru_food_data.py)
  проверяет package hashes и approved food IDs. Тесты
  [test_pr6_data_b2b2.py](../../backend/app/tests/test_pr6_data_b2b2.py),
  [test_ru_food_data.py](../../backend/app/tests/test_ru_food_data.py),
  [test_food_ingredient_seed.py](../../backend/app/tests/test_food_ingredient_seed.py)
  покрывают changed packages и invalid source inputs. Это bounded imports,
  не generalized live FDC enrichment.

**Absence evidence и его границы.** Выполнены `git ls-tree -r --name-only`
и два завершённых поиска `git grep -n -I` (exit 1, stderr пуст):
`RecipeCandidate|RecipeParseCandidate|PortableRecipeDraft` в
`backend/app/{domain,services,schemas,models,seed}` и `scripts`; case-insensitive
`recipe[_-]scrapers|ingredient[_-]parser|schema[.]org|ld[+]json|JSON.?LD|cooklang`
в `backend/app/{domain,services,seed}` и `scripts`. Отдельно прочитаны
[backend dependencies](../../backend/pyproject.toml) и
[frontend dependencies](../../frontend/package.json); parser packages не объявлены.
`RecipeCandidate` присутствует в будущем design в Data Ingestion:888–904;
[legacy imports](../../backend/app/services/imports.py):19–46 имеют cosmetic targets. Generic food HTML/JSON-LD extractor,
Cooklang adapter и food DTO `RecipeCandidate` не найдены. В `data/` и
`backend/app/tests/` нет tracked `.html`, `.htm`, `.jsonld`, `.json-ld`, `.xml`
файлов; inline HTML в тестах E1 проверяет нормативные карты и ссылки.
JSON/text может содержать inline markup, а private archives не обследованы:
это **не доказательство отсутствия HTML вообще**. Ни E1, ни просмотренные
source manifests не устанавливают разрешённый репрезентативный schema.org
benchmark. Поиск не утверждает отсутствие любой эквивалентной функции под
любым названием.

### 4. Capability → implementation → gap → reuse matrix

Вердикты описывают аудит: `ALREADY_COVERED`, `REAL_GAP`, `DEFERRED_BY_GATE`,
`EVIDENCE_INSUFFICIENT`, `REJECTED_AS_DIRECT_INTEGRATION`. Ни один не является
разрешением. Для внешних условий см. первичные источники §5.

| Capability / owner | Existing code/test | Gap или overlap | Candidate / integration type | License / rights / security / language | Gate / verdict |
| --- | --- | --- | --- | --- | --- |
| Generic recipe HTML extraction / Data ingestion | E1–E3 | Multi-site schema.org/JSON-LD не найден; source staging уже есть | recipe-scrapers / будущая offline library adapter | MIT code; отдельные права на recipe text и upstream fixtures; untrusted HTML/resource limits; RU field extraction не RU semantic resolution | `REAL_GAP` в extractor; `EVIDENCE_INSUFFICIENT` для ROI; только отдельная будущая авторизация |
| Ingredient-string parsing / Data curation → Food catalogue | E3–E4 | Дроби/единицы/alias уже частично покрыты; generic RU NLP не подтверждён | ingredient-parser-nlp / EN-only library candidate | MIT; NLTK/Pint/NumPy и отдельная provenance training data; upstream English-only; RU требует обучения/данных | `EVIDENCE_INSUFFICIENT`; RU ready-made integration отклонить; не смешивать со spike extractor |
| Portable representation / Recipe catalogue boundary | E5 | Versioning/scaling есть; потребность interchange и lossless mapping не доказаны | Cooklang/CookCLI / optional format adapter | MIT CookCLI не даёт права на чужие recipes; Rust CLI и optional server/sync/import surface; Unicode не гарантирует Russian display readiness | `DEFERRED_BY_GATE`; неизвестная ценность, не canonical model |
| Nutrition source intake / Nutrition + Data curation | E6–E7 | FDC уже импортируется; только exact uncovered food/form enrichment может быть gap | USDA FDC / offline data, существующие adapters | CC0/public domain; release/hash, nutrient definitions, basis, raw/cooked и RU food match обязательны | `ALREADY_COVERED` для baseline; enrichment требует отдельного demand/source review |
| Yield / purchase basis / Composition evidence | E3, E11 | Бounded FBG fact уже использован; generic yield mapping не реализован | USDA FBG / reference + offline evidence | Официальный child/institutional procurement context; проверить конкретный ресурс/права; yield не individual Serving | `DEFERRED_BY_GATE`; новое значение не source-approved автоматически |
| Storage evidence / PR10 safety policy | E8, PR10 contracts | Confirmed pantry ledger есть; reviewed prepared-food storage policy не закрыта | USDA FoodKeeper / evidence only | data.gov CC0 distribution; quality/freshness не universal safety; exact state/temp/jurisdiction | `DEFERRED_BY_GATE`; нельзя создавать expiry/safe-until или PreparedBatch |
| Pantry/stock / Pantry + Shopping | E8, E10 | Прямое дублирование ledger/FEFO/transactions | Grocy / reference only | MIT; чужие identity/DB/ownership, dual-write и household mapping | `REJECTED_AS_DIRECT_INTEGRATION`; UX reference позднее |
| Recipe catalogue/plans / Recipe + Planning | E5, E9–E10 | Catalogue/planning/shopping уже существуют; extraction отдельно в первой строке | Mealie / reference only | AGPL-3.0; licensing/upgrade/API/auth obligations; AGPL сама по себе не запрет коммерции | `REJECTED_AS_DIRECT_INTEGRATION`; consumer UX позднее |
| Recipe scaling/import / Recipe | E3–E5, E10 | Повтор canonical model и publication | Tandoor / reference only | AGPL + Commons Clause; конкретный commercial-use scope требует отдельного review | `REJECTED_AS_DIRECT_INTEGRATION` |
| Weekly/leftover workflow / Planning, future consumer UX | E9, PR10 | Own deterministic Planner; user-value of SaaS patterns не измерен | Eat This Much / reference only | Публичные feature descriptions не reusable algorithm/license; никаких household uploads | `EVIDENCE_INSUFFICIENT` для value; UX deferred |
| Collaborative groceries / future consumer UX | E8, E10 | Shopping math/ownership уже есть | KitchenOwl / reference only | AGPL; Flutter/Flask stack не переносится; UI assets/code отдельно лицензируются | `DEFERRED_BY_GATE`; direct core integration rejected |
| Recipe import/export / Data boundary, future UX | E3, E5 | Import patterns полезны как reference; выгода interchange не доказана | RecipeSage / reference only | Upstream non-commercial AGPL wording, commercial arrangement отдельно | `REJECTED_AS_DIRECT_INTEGRATION` без отдельного решения о правах |
| Standardized process / Data curation | E11 | AFRS уже evidence input; не домашняя physical-scale validation | AFRS / source-specific reference | Права на конкретный artifact, large-batch applicability, source version; не копировать картинки/вёрстку | `ALREADY_COVERED` как evidence; новое использование требует review |
| Packaged labels/GTIN / future Retail | E4, E6 | Retail match не canonical food identity | Open Food Facts / deferred dataset adapter | ODbL database obligations, attribution; crowdsourced quality; exact packaged product only | `DEFERRED_BY_GATE`; не generic Nutrition authority |
| Natural-language tools / optional AI | Core deterministic path E4–E10 | Не требуются для текущего core; сторонний privileged tool broker не нужен | Grocy/Mealie MCP, Pantry Raider / reference only | Конкретный repository/version/license не установлен; tool privileges, injection, household access | `EVIDENCE_INSUFFICIENT` + `DEFERRED_BY_GATE`; прямое подключение отклонить |

### 5. Внешние источники и качественный shortlist

Проверка первичных источников — 2026-10-29. Это preliminary technical/rights
assessment, **не юридическое заключение**. Перед решением о reuse нужны свежие
version/license/terms receipts. Доступный URL не даёт разрешения на копирование.

| Rank | Candidate и доказательство | Build vs borrow / overlap / поверхность сопровождения | Что можно измерить и почему не запускать сейчас |
| --- | --- | --- | --- |
| 1 | [recipe-scrapers offline API](https://docs.recipe-scrapers.com/getting-started/examples/), [usage/rights](https://docs.recipe-scrapers.com/copyright-and-usage/), [source pin](https://github.com/hhursev/recipe-scrapers/tree/b49b0ff0f2f69970f9579d0c5d086892c335011c) | Узкий missing extractor; меньше overlap, чем платформа. Pin показывает 15.13.0, Python ≥3.11, beautifulsoup4/extruct/isodate; requests — online extra. FamilyFoodOS Python ≥3.12 удовлетворяет только declared floor, installation/resolve не проверены. Сайт-специфические parsers и transitive upgrades требуют сопровождения. | Field extraction + correction time. Нет подтверждённого representative rights-cleared HTML набора; синтетика докажет механику, не corpus ROI. Upstream [test_data notice](https://docs.recipe-scrapers.com/test-data-notice/) сохраняет чужой copyright; эти fixtures нельзя автоматически считать MIT recipes. |
| 2 | [FDC API guide](https://fdc.nal.usda.gov/api-guide/), [downloads](https://fdc.nal.usda.gov/download-datasets/) | Open official data, но E6/E7 уже есть: выгодны только demand-specific mappings и upkeep. Release/type/form compatibility дороже механического CSV import. | Missing exact mappings и review effort, не «подключить FDC впервые». Нет выбранного нового authorized batch. |
| 3 | [FBG tables](https://foodbuyingguide.fns.usda.gov/Appendix/DownLoadFBG), [Appendix A](https://foodbuyingguide.fns.usda.gov/Appendix/ResourceAppendixA) | Useful yield/measure evidence, частичный overlap E11. Высокая semantic review cost; rights/resource-specific. | Exact form/yield applicability, не household portion truth; текущую portion gate не закрывает. |
| 4 | [FoodKeeper dataset](https://catalog.data.gov/dataset/fsis-foodkeeper-data) | Machine-readable CC0 evidence; policy/jurisdiction/temperature review существенно сложнее загрузки JSON. | Coverage безопасно сопоставленных state/condition evidence; PR10 safety gate остаётся. |
| 5 | [CookCLI pinned manifest](https://github.com/cooklang/cookcli/blob/df83728e08c12630eada2fd1feefd1652545c02f/Cargo.toml), [Cooklang specification](https://cooklang.org/docs/spec/) | Optional portable format; own RecipeVersion уже есть. CLI default features включают server/sync/import/self-update/LSP, широкий surface для простой задачи. | Supported-subset roundtrip, missing provenance/identity report; потребность не подтверждена. |
| 6 | [ingredient-parser support](https://ingredient-parser.readthedocs.io/en/latest/how-to/extending.html), [training data](https://ingredient-parser.readthedocs.io/en/latest/explanation/data.html), [repository](https://github.com/strangetom/ingredient-parser) | MIT EN parser; overlap с E3. Для RU нужны preprocessing, labels, обучение и maintenance; Python floor не доказательство совместимости модели/dependencies. | EN field precision только на разрешённых строках; RU reuse benefit не доказан, отдельную модель не предлагаем. |
| Reference/defer | [Grocy](https://github.com/grocy/grocy), [Mealie](https://github.com/mealie-recipes/mealie), [Tandoor](https://github.com/TandoorRecipes/recipes), [KitchenOwl](https://github.com/TomBursch/kitchenowl), [RecipeSage](https://github.com/julianpoy/recipesage), [Eat This Much](https://www.eatthismuch.com/how-to/) | Высокий overlap, чужие service/identity/auth/storage contracts; продуктовые flows можно изучать без копирования code/assets. | Пользовательская ценность требует отдельного consumer UX исследования после его gate. Нет доказанного выигрыша от platform replacement. |
| Later data/reference | [Open Food Facts](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/), [AFRS catalogue](https://quartermaster.army.mil/jccoe/publications/food_links.html) | Retail отдельно; AFRS уже есть в evidence. Конкретные MCP implementations не идентифицированы достаточно для проверки. | AFRS live URL ранее недоступен; текущая независимая доступность и blanket reuse rights не заявляются. Используем существующий pinned E11 как факт наличия evidence, не новый grant. |

Ranking качественный: fit/effort-to-borrow, overlap, upgrade surface,
measurable coverage, source rights/safety, representative corpus,
maintainability и текущие gates. Это порядок возможного исследования при новой
авторизации, **не перестановка roadmap**. Calendar-week savings не оценивались.

### 6. Неизменяемые границы и PR10

Сохраняются `AI_ENABLED=false`, backend-owned deterministic calculations,
единственная FoodIngredient identity, raw/input/cooked distinction,
`unknown != zero`, immutable RecipeVersion и source/rights history.
Domain/services не получают сторонний parser или SQLAlchemy imports;
действуют SQLAlchemy Core/repositories/UoW и sole custom SQLite migration authority.
Любой будущий parser output — untrusted; права, exact units/forms, nutrition
и review проверяются до trusted publication. Household isolation и confirmed
Pantry commands сохраняются; derived Shopping revisions не обновляются молча.

Controlled acquisition E1/E2 не является защищённым arbitrary user URL import.
Security contract §9 требует отдельного SSRF/redirect/DNS/size/type/resource
контроля. Публичный HTML — потенциальный hostile input; offline extraction тоже
требует limits и запрета исполнять scripts/выполнять network side effects.

Прочитаны [PR10 implementation contract](../family-food/pr10-prep-freezer-implementation-contract.md),
[Finished-Dish-First](../family-food/pr10-finished-dish-first-amendment-2026-10-12.md),
[Option B gates](../family-food/pr10-option-b-staged-delivery-gates-2026-10-17.md),
[D3](../family-food/pr10-core-step-eligibility-d3-contract-2026-10-22.md),
[current fixture evidence](../family-food/pr10-core-two-step-current-fixture-evidence-2026-10-27.md)
и [accepted Option A contract](../family-food/pr10-core-option-a-stable-fixture-implementation-contract-2026-10-27.md).

PR #246 сохраняет отрицательное `0/21` совпадений recipe slots.
PR #248 сохранил полный исходный receipt и corrected process-content checksum;
не повторяем устаревший вывод «архива нет». Исторический PlannerRequest parity,
seed-ID seam и воспроизведение исходной недели настоящим Planner не доказаны.
`APPROVED_IMMEDIATE=0`, `NO_GO_TO_PR10_CORE_RUNTIME`,
`PR10-FD-META=BLOCKED/TIME_UNRESOLVED`, `SAFE_BATCH_READY=false`,
`PORTION_RELEASE_READY=NOT_PROVEN`. D3 rollback-resistant revocation и Gate2 с
двумя approved immediate tasks сохраняются. Парсер, FBG и FoodKeeper не заменяют
source/execution/safety review и не разрешают PR10 runtime.

## ASSUMPTION

1. recipe-scrapers может уменьшить ручное извлечение из разрешённого schema.org
   HTML. Это правдоподобно из API и найденного code gap, но не измерено на нашем
   спросе; текущие нормативные PDF/text/XLSX не превращаются в его use case.
2. Вне repository может существовать подходящий разрешённый HTML архив. Его
   locator, права, репрезентативность и независимое чтение не установлены.
3. Manual correction time, net maintenance cost и commercial license posture
   проекта не измерены/не определены этим аудитом. Нельзя утверждать экономию
   недель, качество RU parsing или готовность production dependency.

## DECISION PROPOSAL

**NO-SPIKE сейчас.** Для запуска benchmark недостаточно missing extractor:
нужны подтверждённый recurring extraction demand и разрешённые representative
fixtures. E1–E7 уже покрывают нынешнюю controlled curation/publication; текущие
PR10 blockers относятся к fixture/source/process/safety, а не schema.org.
Не предлагаем parallel arms для ingredient-parser или Cooklang.

Единственный оправданный следующий запрос к владельцу — отдельная
**docs-only проверка demand и fixture eligibility для recipe-scrapers**.
Этот отчёт её не запускает. Если подходящих источников нет, сохранить NO-SPIKE.
Если есть, только новый owner approval может разрешить один offline extraction
spike; production dependency потребует последующего отдельного решения и
применимого Implementation Contract Gate.

### Проект следующей Codex-задачи — НЕ АВТОРИЗОВАН

**Goal:** подтвердить или опровергнуть, что реальные разрешённые HTML-входы
создают непокрытый extraction bottleneck.

**Scope:** docs-only manifest уже законно доступных локальных fixtures и
спроса: source owner, exact artifact/version, hash/size, durable locator,
rights scope, RU/EN, markup family, missing/ambiguous fields, expected target
поля; review без копирования новых чужих текстов. Текущий approved corpus
сохраняет собственные форматы и не переписывается в JSON-LD ради benchmark.
Обозначить, какую работу E1–E3 делают на тех же входах и где возвращают unsupported.

**Non-goals / constraints:** no package install, parser execution, live fetch,
arbitrary URLs, recipe text/image copying, DB/publication, canonical entities,
dependencies, schema, API/UI, roadmap/state/PR10 changes. Data/API/UI/migration: N/A.

**Tests / acceptance:** каждый fixture доступен независимому reviewer и имеет
разрешение именно на нужное хранение/оценку; выборка отражает заявленный спрос,
разделена по language/source/markup, а не состоит только из удобных synthetic
examples. Нет подходящей выборки/спроса — NO-GO. Неизвестные права — исключение
fixture, а не предположение разрешения. Итог — независимо reviewable manifest
или документированный NO-GO; stop перед запуском benchmark.

**Если когда-либо отдельно одобрят benchmark**, его план до запуска должен
содержать один parser arm и следующие заранее согласованные измерения:

- Baseline: существующий importer, где формат поддержан; иначе честный
  unsupported + manual extraction по одному gold schema. Дополнительный
  самописный generic parser не создаётся незаметно как baseline.
- Fields: title, ordered raw ingredient lines, ordered steps, source yield
  text и source identity. Gold labels review отдельно. Precision = correct
  emitted / all emitted; recall = correct emitted / all expected; считать
  по каждому полю, RU/EN и источнику, сообщать denominators и micro/macro results.
  Пустой denominator — N/A; missing/unknown не true zero. Правила matching,
  Unicode/whitespace normalization и ordering фиксировать до оценки.
- Unsupported/unknown: confusion matrix по gold disposition; false acceptance
  = unsupported/ambiguous cases, ошибочно выданные как acceptable, / все gold
  unsupported/ambiguous cases. Критические fabricated quantity/form/rights,
  silent omission и любое trusted publication — NO-GO даже при хорошем average.
- Manual correction time: одинаковый итоговый quality bar, counterbalanced
  порядок двух arms, одинаковые reviewers; median/p90 на fixture, отдельно
  setup, annotation, review и сопровождение. Не считать пропущенные поля экономией.
- Deterministic replay: те же immutable input bytes, version/dependency pins
  и configuration дают одинаковый canonical output hash в повторных запусках;
  network/DB writes = 0. Исходный принятый corpus остаётся byte-identical.
- GO/NO-GO: заранее утвердить минимальное покрытие и пороги precision/recall/
  correction-time benefit на representative strata; численные результаты
  отсутствуют и пороги этим аудитом не утверждаются. Любые unresolved rights,
  source safety или false acceptance критических фактов означают NO-GO.
  Даже успешный benchmark означает лишь evidence для отдельного integration
  review, не разрешение подключить библиотеку.

**Risks / stop:** small/unrepresentative corpus, rights drift, dependency/model
upgrade drift, web format changes, RU semantic mismatch, hidden manual effort.
Любое требование новых persisted contracts, live network, PR10 изменений или
production writes останавливает ограниченную задачу до отдельного решения.

## OPEN QUESTION

1. Есть ли конкретный разрешённый recurring HTML/JSON-LD source demand,
   которого не закрывают E1–E3, с доступными representative fixture bytes?
2. Кто подтверждает source-specific retention/use rights и gold labels, и
   какой объём/тип ошибок делает extraction непригодным для этого спроса?
3. При будущем data enrichment: какие exact food/form/yield/storage gaps
   действительно остаются после текущих mappings и какая approved policy
   позволит их публиковать? Этот отчёт не переоткрывает PR10 решения.

## Проверка и независимое review

Tier — docs-only по [verification-policy](../family-food/verification-policy.md).
Локальные проверки выполнены: `git diff --check` между baseline и report tree,
`git diff --cached --check` через изолированный index — PASS; exact path audit —
один новый report; 96 относительных Markdown links — targets существуют в
baseline; таблицы/fences — PASS. Выполнены ручной status/proposal/privacy review
и целевой scan credential/private-key patterns; секреты и частные household
данные в добавленном отчёте не обнаружены. Это не полный security scan репозитория.
Публикуется только этот новый отчёт; source corpus и production files не меняются.

CI receipt привязывается к конечному HEAD в описании PR, чтобы отчёт не заявлял
заранее ещё не завершённый запуск. Docs CI проверяет existence относительных
ссылок, но не внешние URL/anchors, лицензионные выводы или correctness всех фактов.
Внешние первичные страницы проверены исследованием; complete link availability
и будущая неизменность URL не гарантируются.

Не выполнялись backend/frontend regression, внешние установки/benchmark,
corpus rebuild/import/publication, FoodKeeper distribution download/hash verification,
live crawling, safety validation или runtime
PR10 work. Неизменённые существующие тесты инспектированы, а не объявлены заново
пройденными. Доступ к private raw corpus/production DB для этого аудита не получен.

Для независимого reviewer: проверить E1–E12 по baseline, absence scope,
candidate ownership/rights, NO-SPIKE reasoning и отсутствие любых implied
authorizations. Review запрашивается в PR; merge и следующие задачи запрещены
без отдельного решения владельца.

**Acceptance trace:** baseline — §1; candidate/owner coverage — §4–5;
ingestion/publication/FDC/rights — E1–E7/E11; duplication/PR10 — §4/§6;
NO-SPIKE и proposed task — DECISION PROPOSAL; docs-only checks — этот раздел
и exact-head PR receipt; independent review — запрос в PR.
