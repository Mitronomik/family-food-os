# FamilyFoodOS — External Reuse & Integration Plan
## Исследование применимости готовых FoodTech-решений и ТЗ на безопасное переиспользование

**Дата:** 2026-10-29

**Версия:** Research RFC / Integration Technical Specification v0.1

**Статус:** **ПРЕДЛОЖЕНИЕ / НЕ APPROVED ADR / НЕ РАЗРЕШЕНИЕ НА RUNTIME**

**Назначение:** Project Sources и кандидат `docs/research/integration-reuse-2026-10-29.md` после review.

**Код/репозиторий:** в ходе исследования изменения не производились.

**Источник текущего состояния (финальная повторная проверка 2026-10-29):** подключённый GitHub, `Mitronomik/family-food-os`, accepted `main@edba04dcd491ef9663fe82c96f6f0c1c76504a27` после merge PR #248 (2026-10-29, 13:15:56 UTC). PR #246 merged ранее в `36ab339302557aafc2187f9d8a70b035869c8487`. PR #248 принят как contract/evidence/test-only change, **не** как fixture runtime, Prep eligibility или Gate2 PASS.

**Исторический снимок исследования:** `main@3c4645a27d675bb4464c913785aef3cd88de8681` после PR #244 (2026-10-27); при первоначальном анализе PR #246/#248 были OPEN/UNMERGED. Этот SHA остаётся базой исходной ветки RFC, а не обозначением текущего `main`.

**Ограничение исследования:** изучены канонические договоры проекта, ключевые существующие реализации и внешняя документация/публичный исходный код; **не выполнялись** локальные сборки внешних проектов, независимые инсталляции, нагрузочные/точностные эксперименты, юридические заключения или запуск всей тестовой матрицы FamilyFoodOS. По этой причине ROI и совместимость отдельных библиотек — **гипотезы до spike**.

---

# 1. Executive decision proposal

## DECISION proposed

**Не заменять FamilyFoodOS на готовую платформу и не связывать core с чужой БД/API.** Утверждённые доменные слои уже реализуют существенную часть бизнес-логики. Самая перспективная экономия времени — переиспользовать *узкие, доступные по лицензии инструменты* на границе ingestion/документирования и *машиночитаемые проверяемые данные* по питанию/выходу продуктов/хранению. Продуктовые паттерны чужих систем использовать для UX и будущего prepared-food workflow.

**В текущем PR10 допускается только read-only research и подготовка доказательств.** Не вносить новое ПО в runtime, не добавлять миграции и не изменять принятые gates. Предварительное исследование и изолированные прототипы разрешать отдельными явно согласованными, не влияющими на `main` задачами. После самостоятельного review/merge отдельного docs-only Implementation Contract Gate — выполнять малые PR в соответствующих фазах roadmap.

### Рекомендация в одну строку

`Existing deterministic FamilyFoodOS core` + `source-backed controlled data/adapters` + `reusable parser/format libraries` + `external UX benchmarks`, **не** `FamilyFoodOS = Grocy/Tandoor/Mealie fork`.

---

# 2. FACT — актуальный baseline FamilyFoodOS

## 2.1 Источники истины и дата

Обязательны: `AGENTS.md`, `state/current-focus.md`, `docs/family-food/architecture.md`, `docs/family-food/master-roadmap.md`, addenda `2026-09-13`, `2026-09-16`, `2026-09-19-data-corpus`, `docs/family-food/data-corpus-v1.md`, `docs/family-food/security-architecture.md`, PR10-ARCH/FD-ARCH/Option B/D3 и самый свежий merged `main`. Исторические Project Sources — только после актуальных repo contracts. В `state/current-focus.md` присутствует история нескольких задач; формулировки о pending review в исторических разделах сопоставляются с актуальными GitHub merge evidence. Merge PR #248 принимает ограниченный contract/evidence/test-only результат, **не** разрешает следующую runtime-задачу автоматически.

При финальной повторной проверке 2026-10-29 accepted `main` — `edba04dcd491ef9663fe82c96f6f0c1c76504a27`: PR #246 и PR #248 merged. Отрицательное evidence #246 (0/21 совпадающих recipe slots) сохраняется. Принятый HEAD #248 — `120d997f80e6f0aec0f15002567687a14813e216`: Option A contract, полный архив исходного synthetic receipt, portable QA reference и focused process-content regression test теперь находятся в `main`. Наличие архива устраняет прежнее замечание о его недолговечном хранении; **полная историческая Planner input parity, сквозная test-only seed-ID injection и воспроизводимость недели через реальный Planner всё ещё не доказаны**. Contract/evidence merge не является разрешением на runtime. `APPROVED_IMMEDIATE=0`, `NO_GO_TO_PR10_CORE_RUNTIME`, `PR10-FD-META=BLOCKED/TIME_UNRESOLVED`, safe-batch и portion-release gates остаются без изменений.

## 2.2 Реализованные bounded contexts — что нельзя строить заново

| Capability | Подтверждение в accepted репозитории | Статус/предел | Вывод |
|---|---|---|---|
| Household / Members | PR2-C, Household API/services | Implemented | Не заимствовать модель пользователей у других сервисов |
| FoodIngredient, aliases, units, nutrition/composition | PR3, PR6, DATA-CORPUS-V1 | Deterministic, provenance, `unknown != 0` | Не подменять каталог внешним SKU или сырой схемой FDC |
| Recipe + immutable RecipeVersion + Steps | PR4; `backend/app/domain/food_recipes.py`; `backend/app/services/food_recipes.py` | Source/rights/versioned publication | Внешний импорт только через `RecipeCandidate` / проверяемую публикацию |
| Controlled source-corpus ingestion | `backend/app/domain/recipe_source_corpus.py`; `backend/app/services/recipe_source_corpus_import.py`; `scripts/import_ru_normative_recipe_corpus.py` | RU normative cards, source versions and raw/text hashes; source staging does not publish RecipeVersion or establish Nutrition truth | Compare generic HTML/JSON-LD extraction against this existing source-specific baseline |
| Pantry & stock movements | PR5; `backend/app/services/pantry.py` | Household-scoped, transaction/negative-stock, locations, dates | Прямой переход на Grocy означал бы дублирование ledger |
| Member schedules / MealPlan / Serving | PR7 | 1–6 opportunities, mixed sources, revisioned plans | Чужой meal planner с 3 фиксированными приёмами не подходит |
| Planner | PR8 + дальнейшие доработки; `backend/app/domain/planner.py` | Deterministic, source constraints, source/corpus audit | Нельзя переносить закрытый SaaS-алгоритм и использовать LLM как планировщик |
| Shopping Engine | merged PR #186/#188/#190; `shopping_calculation.py`, `shopping.py` | Decimal scaling, FEFO, immutable snapshots, incomplete/unknown, no Pantry mutation, API | Уже сильнее типовой простейшей grocery-list логики; не заменять |
| Prep / freezer | PR10 research/contracts; merged PR #244/#246/#248 | **NO_GO_TO_PR10_CORE_RUNTIME**, 0 approved immediate steps; отдельно safe-batch/portion release gates | Нельзя объявлять хранение/готовые партии реализованными |
| PDF / PWA / Feedback | в roadmap после PR10 Gate 2 | Не подтверждены как completed | Изучать UX, не перепрыгивать gates |
| Retail, optional AI | поздние программы | Не реализуются сейчас | Не тащить MCP/retail как обязательные зависимости |

### Подтверждённые детали, важные для reuse

- `backend/app/domain/shopping_calculation.py`: версия движка `shopping-v1a`; `ShoppingQuantity`/`ShoppingLotAllocation`; source/content fingerprints; `ShoppingUnresolvedReason` для `LEFTOVER`, `PREPARED`, `READY_MEAL` и т.п. Эти источники **пока не считаются обеспеченным запасом**.
- `backend/app/services/shopping.py`: Unit of Work, идемпотентное повторение снимка по fingerprint, current MealPlan revision, чтение Pantry без списания.
- `backend/app/services/pantry.py`: отдельные подтверждённые `add_stock`, consume/adjust, записи движений; `planned != executed`.
- `backend/app/services/food_recipes.py`: уже есть `TrustedRecipeIngredientSeed` и `TrustedRecipeVersionSeed` с source ID/URL/version, rights status, output g, количествами и steps. Внешний парсер не должен выдавать эту модель как «trusted» напрямую.
- Existing FDC seed/import: `backend/app/seed/food_ingredients.py` reads `data/seed/food_ingredients/nutrition.csv`, accepts `USDA_FDC` Foundation/SR Legacy records, validates source identity/type and passes source ID/version/basis/nutrients through `TrustedNutritionSeed` and the existing catalogue/UoW boundary. This is already implemented; these seed rows do **not** automatically represent all current production V2 nutrition authority. Later publications have their own versions and review.
- Existing controlled RU source-corpus ingestion extracts normative HTML/card text and preserves source hashes separately from canonical FoodIngredient resolution and RecipeVersion publication. Generic multi-site schema.org/JSON-LD extraction is a **candidate gap to verify**, not a reason to rebuild source staging or publication. `RecipeCandidate` below is conceptual wording, not a claim that a runtime DTO with that exact name already exists.
- Merged PR #246 выявил **0/21 идентичных выбранных `(date, position, recipe code)`** при сравнении исторической и свежей синтетических недель несмотря на одинаковые 3/21/42 counts; это препятствует позитивной проверке двух подготовительных событий.
- Merged PR #248 — Option A contract/evidence/test-only: исходный synthetic receipt сохранён в репозитории; portable process-content checksum исправлен и покрыт focused regression test. Это не доказательство Planner input parity, стабильной генерации 21×42 fixture или готового runtime.

---

# 3. Comparison / buy–borrow–build matrix

Оценки: **IMPLEMENT** — собственный bounded engine уже существует или остаётся domain-specific; **LIBRARY** — возможно прямое подключение узкого пакета после spike/license; **DATA** — импорт source-backed данных; **REFERENCE** — исследовательский/UX-референс; **DEFER** — поздняя стадия; **REJECT** — не интегрировать целиком.

| Проект/источник | Что полезно | Пересечение с FamilyFoodOS | Выбор | Причина и блокер |
|---|---|---|---|---|
| **Grocy** (`grocy/grocy`) | Stock transactions, expiration, recipe fulfillment, due-score, OpenAPI | Pantry/Shopping **уже работают** | **REFERENCE; REJECT platform integration** | PHP/SQLite, другая модель identity/ledger; dual-write и синхронизация разрушат ownership. MIT позволяет изучать/адаптировать изолированно с сохранением notices |
| **Eat This Much** | Целостный weekly UX, meal-prep, cooked leftovers | Planner/Prep UX, portions | **REFERENCE** | SaaS, закрытый алгоритм; нет доступной воспроизводимой engine реализации |
| **Mealie** | Recipe URL import, meal planner, shopping, API, localization | Recipe и consumer PWA | **REFERENCE / optional isolated import experiment** | AGPL-3.0; перенос runtime/копирование исходников — licensing review и дублирование архитектуры |
| **Tandoor Recipes** | Structured recipes, import, scaling, units, shopping | Recipe/versioning, ingestion | **REFERENCE; REJECT direct code reuse** | AGPL-3.0 + Commons Clause/Selling exception; коммерческий конфликт и другая система публикации/прав |
| **KitchenOwl** | Collaborative grocery list, mobile/offline patterns | будущая PWA/Shopping UI | **REFERENCE** | AGPL-3.0 и Flutter/Flask, не наш stack; смотреть поведение, не портировать UI |
| **RecipeSage** | Multiple import formats, ingredient/step scaling, export | ingestion и print UX | **REFERENCE only** | Коммерческое использование требует отдельной лицензии; нельзя брать production код без разрешения |
| **Cooklang specification / CookCLI** | Переносимое представление рецептов; import/export/CLI | Внутренний RecipeVersion уже существует | **LIBRARY/FORMAT experimental; later** | MIT у CookCLI; не менять canonical model; mapping и fidelity-test, формат может терять provenance/food identity |
| **`recipe-scrapers` Python** | Извлечение schema.org JSON-LD/HTML title/yield/ingredients/steps | DATA-3/Recipe ingestion | **LIBRARY candidate P1** | MIT; только контролируемые HTML + rights/SSRF policy; не выполняет семантическую валидацию |
| **`ingredient-parser-nlp`** | Извлечение имени, количества и единицы из английской строки | source parser/resolver | **LIBRARY candidate for English sources; RU adaptation requires separate evidence** | MIT; upstream поддерживает только English, готовой RU-модели нет. RU требует языковой обработки, размеченного корпуса и отдельного обучения; вывод — candidate, не trusted quantity |
| **USDA FDC** | Нутриенты, публичные dumps/API, CC0 | Nutrition/Composition/Catalogue; controlled FDC seed/import уже реализован | **DATA enrichment/automation candidate P1** | Дополнять конкретные пробелы существующей curation/publication, не подключать USDA заново; совместимость `food form`, basis, RU foods и текущая versioned authority обязательны |
| **USDA Food Buying Guide** | Таблицы edible yields и procurement per serving | Food form/yield, portion/purchase math | **DATA / methodology candidate P1** | US institutional/child-program context; не подменяет личные порции; требуется проверка прав/применимости конкретной таблицы |
| **USDA FoodKeeper** | JSON/XLS рекомендации по хранению и качеству | PR10-BATCH/SAFE-REUSE, storage metadata | **DATA + evidence P1, runtime only after safety contract** | Датасет в data.gov обозначен CC0; не все сроки = гарантированные safety limits; category/form/state/temperature match |
| **AFRS recipes** | Standardized institutional recipe yield, process & large batch scaling | Recipe/Prep educational methodology | **REFERENCE; optional rights-reviewed corpus input** | Рецепты на большие партии, домашняя масштабируемость и rights/provenance — отдельно; военная роботизация не даёт Planner engine |
| **Open Food Facts** | GTIN, packaged labels, ingredients, aliases | будущий Retail SKU | **DEFER; DATA adapter later** | ODbL/атрибуция/share-alike и crowdsourced quality; не Nutrition truth по умолчанию |
| **Grocy MCP / Mealie MCP, Pantry Raider** | NL→API tools patterns | future optional AI | **DEFER; REFERENCE only** | лишние привилегии и чужие auth/action contracts; наш AI должен делать structured proposal, не произвольные writes |

**Общий вывод:** **есть подтверждённые технические возможности переиспользовать внешние компоненты**, особенно `recipe-scrapers` и Cooklang, а также официальные пищевые данные. **Пока нет проверенных измерений**, что конкретный компонент ускорит весь проект; решение о production dependency принимается только по spike acceptance matrix.

---

# 4. Compatibility boundaries / what never changes

## 4.1 Non-negotiable architecture

```text
Platform-source / offline tools
    → acquired source snapshot (untrusted)
    → parser adapter (optional third-party dependency)
    → normalized candidate
    → canonical FoodIngredient resolver + unit/form validator
    → provenance, rights & nutrition/quantity validation
    → review / authorized publication of immutable RecipeVersion
    → existing Planner/Shopping/Pantry/Prep
```

- UI → API → application/domain → repository/UoW → DB. External parser NEVER returns a production RecipeVersion/Serving/PantryItem directly.
- No direct dependency on Grocy/Mealie/Tandoor services, DB schema or identity model in core.
- No silent migration of `FoodIngredient` IDs; raw/cooked edible form separation; no cross-source nutrient averaging without policy.
- `AI_ENABLED=false` functional path remains green.
- No LLM authority over nutrition, mass, portions, allergens, costs, expiry or safety.
- Pantry write only as explicit confirmed application command; Shopping/Prep generation read-only.
- Source dataset snapshots/version/provenance required; recipe source rights and reproducible publication required.
- External URL/file import is untrusted (SSRF, malware, redirect/host restrictions, content limits). No uncontrolled web spider.
- FoodKeeper data and FBG do not independently authorize time/temperature decisions for a prepared batch without applicable reviewed storage policy.
- All user-facing Russian UI/text; source English must not leak into UI. No fake translations of authoritative instructions.
- Existing PR10 Option B / D3 / frozen fixture and separate `SAFE_BATCH_READY` and `PORTION_RELEASE_READY` gates stay unchanged.

## 4.2 Crucial anti-corruption adapters

Future implementation may add **only on authorization**:

```text
ExternalRecipeHtml → RecipeParseCandidate
RecipeParseCandidate → CanonicalIngredientResolutionProposal
RecipeImportEvaluation → review / rejection / publication request
FdcFoodRecord → NutritionSourceCandidate
FbgYieldRecord → YieldEvidenceCandidate
FoodKeeperRecord → StorageEvidenceCandidate
CooklangDocument ↔ PortableRecipeDraft
```

These are conceptual, NOT committed entity names or table declarations. Existing recipe seed/import and nutrition authority contracts take priority; avoid duplicate aggregates. Use config flags to disable each adapter. Return `UNSUPPORTED/UNKNOWN/REVIEW_REQUIRED` explicitly.

## 4.3 Data-level invariants

For an imported quantity preserve at least:

```yaml
source_id: external/source-id
source_version: published/date/version
source_url: https://example.com/recipe
raw_ingredient_text: '2 средние моркови'
parsed_quantity: '2'
parsed_unit: pcs
candidate_food: CARROT
mass_in_g: null          # no unapproved piece→grams conversion
validation_status: REVIEW_REQUIRED
parser_name: bounded-adapter
parser_version: pinned
rights_status: UNREVIEWED
```

**Never** fill `mass_in_g=160` as authoritative unless reviewed `IngredientUnitProfile` provides the compatible piece-weight semantics. Candidate fields must be traceable to source and not silently interpreted as measured facts.

---

# 5. Integration programs / dependency order

The following integration tasks are **proposals**, not permission to start them. They must be fitted into existing roadmap gates and current `state/current-focus.md`. All production-facing high-coupling changes require a separately approved **docs-only Implementation Contract Gate** before runtime.

## REUSE-0 — Read-only baseline/duplicate capability inventory (NOW, when owner authorizes bounded docs task)

**Goal:** Freeze exact accepted main code inventory and prevent building duplicate subsystems.

**Scope:** reconcile current accepted `main`, merged PRs, existing import/corpus scripts, tests, release gates and file ownership. Prepare a matrix `already exists / missing / blocked / authorized later`. Identify stable interfaces for later adapters, without changing them.

**Non-goals:** PR10 runtime, data publication, schema/migration, dependency introduction, global roadmap rewrite.

**Code/API/UI/Data:** N/A.

**Tests:** docs source/link/sha verification, manual independent reviewer inventory.

**Acceptance:** every proposed library mapped to explicit owning bounded context; no invented missing feature; exact main SHA recorded.

**Risk:** PR #246 and PR #248 are now merged into the refreshed baseline. Later accepted PRs may change evidence/current focus; recheck exact refs before any separately authorized task. Contract/evidence acceptance must not be confused with implemented fixture runtime.

**Follow-up:** refresh inventory after independently merged PRs only.

## REUSE-1 — Isolated parser benchmark (DATA PROGRAM; preparatory spike may be independently approved earlier)

**Goal:** determine whether `recipe-scrapers` meaningfully reduces manual extraction work on **permitted** recipes.

**Scope:** offline, manually supplied HTML/snapshots only; pin exact package/license/version; map output to existing `Recipe Candidate` / seed staging boundary, never to publish. Compare to in-repository existing parsing scripts. Optional second arms: Cooklang import and `ingredient-parser-nlp` on permitted English ingredient lines (separately scored). A bounded RU baseline may document unsupported behavior against dictionary/regex extraction, but a benchmark does not authorize building a Russian model: language-specific processing, corpus labelling, training and maintenance require a separate cost/benefit decision.

**Non-goals:** broad crawlers, arbitrary URLs from users, live background scraping, AI-publishing, recipe activation, new SQL.

**Architecture:** pure infrastructure adapter, no import of package into domain; release kill switch.

**Data:** independent curated evaluation set from rights-reviewed local fixture sources; include Russian phrases, mixed units, ambiguous quantities, allergens, cooked/raw forms, missing steps, duplicate ingredient names.

**API/UI:** N/A for experiment.

**Tests:** baseline corpus exact-replay unaffected; parser output schema; no unauthorized publication; malicious HTML/plain-text; inconsistent count/yield; reproducibility; missing fields; Russian output.

**Acceptance:** measured field-level precision/recall, manual correction time, failure categorization, zero direct trusted publication, explicit licensing decision. Compare baseline time and parser time on same inputs; adopt only if measurable improvement and no safety deterioration. Threshold is set before evaluation, not guessed after results.

**Risks:** `ingredient-parser-nlp` currently supports English only; Russian adaptation is separate development, not a measured ready-made capability. Source terms/robots/rights and dependency supply-chain remain independent risks.

**Follow-up:** REUSE-2 after authorization or reject candidate with receipt.

## REUSE-2 — Controlled recipe ingestion adapter (in DATA-3, after gate)

**Goal:** integrate winning source extractor into existing reviewable ingestion pipeline.

**Scope:** `SourceSnapshot → parser → candidate → resolver → nutrition checks → rights/review → immutable publication`. Pinned parser version and stored raw hashes; idempotent reimport and retry. Reuse `TrustedRecipeVersionSeed` only **after** policy approves provenance/rights; never bypass trusted seed semantics.

**Non-goals:** new planner, new recipe domain, automatic external authoring, ongoing site crawling.

**Architecture:** isolated infrastructure module and adapter interface; dependency only via interface; source source_id/version; no direct DB touch by parser.

**Data changes:** ideally none if existing source corpus/source history suffices; if additional fields/persistence needed, first independent docs-only contract + forward migration.

**API/UI:** first admin/internal CLI, **not** consumer UI; production API only if necessary and separately justified.

**Tests:** old corpus exact bytes/revisions preserved; malformed input cannot publish; zero invented quantities; idempotency; downgrade/replay/conflict; report source parser version; Russian text; no cross-household data; failure rollback.

**Acceptance:** validated batch import with no increase in unreviewed publication; can disable the parser and use existing controlled importer; source audit preserved; time improvement against baseline proven.

**Risks:** source rights, compatibility drift, under-specification of food form.

**Follow-up:** extend more sources only after evidence.

## REUSE-3 — USDA nutrition/yield source adapters (DATA PROGRAM / existing Nutrition validation)

**Goal:** accelerate specific corpus enrichment gaps in the already implemented controlled FDC seed/import and reviewed nutrition publication workflows, without rewriting Nutrition or Serving.

**Scope:** first inventory existing FDC mappings, import validation and current versioned nutrition authority; then evaluate only uncovered or costly-to-maintain mappings using a USDA FDC CC0 pinned snapshot/version, FBG yield tables and canonical FoodIngredient. Compare exact edible/source basis, raw/cooked form and units. Do not equate legacy seed coverage with the whole current V2 catalogue.

**Non-goals:** blanket replacement of approved Russian records; use FBG child-institutional portions as household targets; silent yield inference; adding source-specific IDs as domain identity.

**Architecture:** DATA/Curation adapters only, calculate through existing Nutrition/Composition contracts.

**Data:** provenance `{source, record id, snapshot release, checked_at, rights, reference mass/form, uncertainty}`; publish only after applicable source review.

**API/UI:** none initially.

**Tests:** raw-vs-cooked negative; edible-gross-net conversion boundary; inconsistent USDA/RU form; missing nutrient `unknown != 0`; version pinned results; reverse/retry/idempotency; published versions immutable.

**Acceptance:** 100% of accepted input-to-published mappings auditable; independent domain/Data review, measurable reduction in manual curation cost on relevant gaps.

**Risk:** Russian product identity mismatch and non-applicable institutional yields.

**Follow-up:** additional sources only when needed.

## REUSE-4 — FoodKeeper storage evidence research (PR10-BATCH/SAFE-REUSE, NOT NOW runtime)

**Goal:** obtain defensible, machine-readable *evidence candidates* for food/storage guidance.

**Scope:** download/license+hash+version of official FoodKeeper JSON; map product/category/preparation state, storage location and conditions, distinguish `quality duration` vs `safety rule`. Compare to applicable Russian regulation and sources; identify gaps and contradictions.

**Non-goals:** auto-assign `expires_at` or `safe_until` from an English category without review; make frozen-food safe shelf-life claims from quality guidance; auto-create prepared stock; bypass PR10 D3.

**Architecture:** standalone offline reference importer; authoritative policy registry proposed **only after** later reviewed safety contract.

**Data:** source snapshot fingerprint, jurisdiction, `safety_or_quality`, category/form/storage temperature/applicability, optional reviewed mapping to exact RecipeVersion/food form; unsupported remains UNKNOWN.

**API/UI:** none prior to safety gate. Subsequent Russian UX must label known vs unknown storage guidance.

**Tests:** chilled vs frozen, raw vs cooked, open vs unopened, conflicting/source-stale category, absent temperature, unsupported recipe, rules revoked, rollback to older policy does not reactivate unsafe advice.

**Acceptance:** no unsourced automatic time limit; every published rule source-backed and policy-reviewed; fail closed on category mismatch; independent qualified safety review; D3 anti-rollback semantics preserved.

**Risks:** FoodKeeper quality rather than food-safety scope; domestic conditions differ; US source not sufficient for RU release.

**Follow-up:** separately approved storage policy/PreparedBatch execution contract, not part of REUSE-4.

## REUSE-5 — Consumer UX reference adaptation (at PR11–PR15 only)

**Goal:** shorten UX ideation with existing user workflows.

**Scope:** UX comparison on Eat This Much, Mealie, KitchenOwl, Grocy; adapt generic screen flow and usability questions **without copying third-party source/assets**. Map into canonical `Сегодня / Неделя / Купить / Заготовки / Дома`, incl. partial/unknown explanations and manual corrections.

**Non-goals:** copying AGPL app components, visual assets, branding; introducing new consumer functionality before API/gates; front-end calculations.

**Architecture:** current FastAPI contracts own all operations; Next.js/PWA consumer client.

**Data/API:** reuse current endpoints; new API only through separate context contract.

**Tests:** 375/390/430 px; single-hand interactions; error/loading; Russian strings; unresolved shopping/Prep statuses; stale derived state; confirmation of inventory mutations.

**Acceptance:** key jobs within existing project UX target and observed user usability; no duplicate math; no unlicensed copied files.

**Risks:** interface assumptions from business-oriented products don't fit family use.

**Follow-up:** real-family testing after shared deployment gate.

## REUSE-6 — Portable recipe import/export (optional after working consumer core)

**Goal:** avoid lock-in and hand-coded text format by supporting Cooklang or RecipeSage-compatible public interchange where licensing permits.

**Scope:** one optional import/export adapter to/from internal RecipeVersion projection; no replacement of canonical database.

**Non-goals:** lossless claim before full field mapping, automatic publishing, copying RecipeSage service code.

**Tests:** exact roundtrip for supported fields; intentionally rejected missing provenance/rights/food identity; no implicit quantity rounding; Russian and Unicode; half/whole units; unsupported fields clearly noted.

**Acceptance:** documented supported-subset roundtrip with provenance preserved outside portable format, user data export without business truth degradation.

**Risks:** external plain-text recipe languages may not encode immutable source/food IDs; explicit lossy boundaries mandatory.

**Follow-up:** optional, not MVP0/Gate2 blocker.

## REUSE-7 — AI/MCP patterns (after deterministic Core/consumer proof; optional)

**Goal:** use existing MCP designs as behavioral references for structured tool invocation, not plug an untrusted Grocy/Mealie connector into production.

**Scope:** narrow read-only tools for recipes/plans initially; later proposal→validate→user confirm→domain command with object authorization, rate/resource bounds, audit.

**Non-goals:** direct DB/SQL/tool shell access, arbitrary web fetch, uncontrolled stock writes/recipe publication, LLM numeric authority.

**Tests:** prompt injection and cross-household isolation, invalid proposed quantity, destructive action without confirmation, tool replay, AI_DISABLED full regression.

**Acceptance:** security review + deterministic validation + opt-out; no runtime until AI program explicitly authorized.

**Risk:** excessive agent authority; privacy of children/household data.

**Follow-up:** optional future program, not part of PR10.

---

# 6. Build vs integrate — anti-duplication design details

## 6.1 Pantry/Grocy

**FACT:** Grocy provides stock transactions/recipe fulfillment and OpenAPI, MIT license. **FACT:** FamilyFoodOS already has a confirmed ledger, household scope, FEFO and shopping subtraction. **DECISION proposed:** do not replace Pantry or run a second live inventory. Only benchmark three ideas for *later* improvements: minimal input fields, expiring stock prioritization, recipe fulfillment UX. If migration/interop ever needed, first produce one-way **read-only** export proof and independent identity/transaction contract; no dual-write. **Do not invent a near-term Grocy adapter.**

## 6.2 Meal planner/Eat This Much

**FACT:** Eat This Much publicly documents automatic meal planning and leftovers workflows; it does **not** supply an openly reusable algorithm in the reviewed sources. **ASSUMPTION:** these workflows may reduce decision effort for FamilyFoodOS users; their value, retention impact and willingness-to-pay require separate validation. Product existence and feature documentation do not prove that value. FamilyFoodOS already has 1–6 meal patterns and individual member Serving; keep own deterministic Planner. Product benchmark should measure weekly meal changes, leftover scheduling, prep time and decision count — without claiming exact parity of serving optimization.

## 6.3 Structured recipes/Tandoor/Mealie/RecipeSage

External platforms solve recipe extraction and library management, but their core code/licenses and model differ. Prefer `recipe-scrapers` MIT library + existing `RecipeVersion/seed` contract instead of running all of Tandoor/Mealie. Examine UI/validation patterns; don't transplant licences or authenticated APIs without explicit authorization.

## 6.4 Portion calculus/FBG

FBG is a source of **procurement/yield method**; not an individual household caloric policy. Maintain separation:

```text
member energy/nutrient target
→ member-specific Serving (existing policy)
→ RecipeVersion base_servings and input ingredient demand
→ measured/reviewed output yield when available
→ prep/cooked portion allocation only under accepted source/form policy
```

No presumed `raw_g == cooked_g`. No treating school/institutional portion tables as validated home limits. Current `PORTION_RELEASE_READY=PASS` gate remains unmet until reviewed evidence, regardless of library.

## 6.5 Storage/FoodKeeper

FoodKeeper catalogued storage durations may describe **freshness/quality**, not a universal safety guarantee. Keep storage evidence, applicable reviewed policy and physically confirmed PreparedBatch separately. Until review: display `UNKNOWN/NEEDS_REVIEW`, not fictive dates. When authority changes, ensure revocation/latest policy cannot be bypassed by rolling back an app build.

---

# 7. Dependency/security/license decision matrix

| Source | Verified public terms from upstream | Permitted proposal | Forbidden without further legal decision |
|---|---|---|---|
| Grocy | MIT | Study or adapted small logic with attribution/license notice | Full service replacement without architecture decision |
| CookCLI | MIT | Offline CLI/helper under pinned version, if proven useful | Treat files as authoritative RecipeVersion |
| Python recipe-scrapers | MIT | Offline/controlled HTML parsing | Crawl arbitrary websites and copy protected recipe texts |
| ingredient-parser-nlp | MIT; English-only upstream support | English-source benchmark; separately scoped RU feasibility assessment | Auto-publish guessed grams/name matches or assume an available RU model |
| USDA FoodData Central | CC0/public domain | Licensed/source-attributed snapshot curation | Blind mass/form or nutrient authority transplant |
| USDA FoodKeeper | data.gov distribution CC0 | Evidence candidate for reviewed storage policy | Invent generalized safe holds for every dish |
| USDA Food Buying Guide | Official public tables; **specific rights/retention verify per resource** | Methodology + candidate yield data | Assume any child-institutional value applicable to adult serving |
| Mealie | AGPL-3.0 | Study/API schema benchmarking | Incorporate protected service/UI code without license strategy |
| KitchenOwl | AGPL-3.0 | UX research | Copy frontend implementation into closed service sans review |
| Tandoor | AGPL with Commons Clause restriction | Study and map concepts | Commercial hosted copy/service reuse without lawyer clearance |
| RecipeSage | Non-commercial AGPL / commercial only by arrangement | Study publicly described features | Commercial copy/deploy/embedded code absent explicit license |
| Open Food Facts | ODbL database terms | Later candidate SKU enrichment with data separation/legal review | Blend ODbL corpus into untracked proprietary authoritative table |
| AFRS | Official public service recipe catalogue; re-use of individual source assets needs rights review | Methodology, individually-reviewed source candidates | Unreviewed bulk import/provenance loss |

**Important:** MIT license applies to implementation code, **not** rights to recipes fetched from unrelated sites. Third-party API accessibility is not redistribution permission. Exact copyright and database licensing decisions must be reviewed for commercial RU distribution. This document is not legal advice.

---

# 8. Prioritization and measurable decision gates

### Evaluation dimensions

For every candidate maintain a single pre-declared record:

1. **Overlap:** does existing FamilyFoodOS already implement the same capability?
2. **Net time saved:** hours to reach same *accepted* output with and without package, including maintenance/setup/review.
3. **Integration cost:** interfaces, schema/migration impact, deployment, data conversions and dependency risk.
4. **Correctness:** source/form/quantity preservation, regression and safety behavior.
5. **Rights/security:** package license, dataset rights, CVEs/supply-chain, network attack surface.
6. **Exit strategy:** can dependency be disabled/removed without changing core truth?

No fabricated day/week estimates. Before each spike, record baseline manual-work time, fixture set, metric and stop-loss criterion. **Adopt only** when measurable net benefit outweighs its operational and licensing costs. Approval belongs to project owner after independent review.

### Indicative priority (sequencing ≠ immediate authorization)

| Priority | Work | When | Decision |
|---|---|---|---|
| P0 | Inventory and duplicate-implementation audit | may be separately owner-authorized as a bounded read-only task | PROPOSED, NOT AUTHORIZED by this RFC or its merge |
| P0 | Restore PR10 original fixture reproducibility/provenance | current owner-approved PR10 work | Existing priority; third-party library does not solve it |
| P1 | `recipe-scrapers` offline benchmark | optional research spike or DATA-3 stage | Candidate, measured GO/NO-GO |
| P1 | USDA FDC/FBG controlled gap audit | data stage or standalone research | Candidate, no automatic publication |
| P1 | FoodKeeper safety/quality scope audit | PR10 future safety evidence research, no runtime | Candidate, safe-source decision required |
| P2 | Cooklang import/export | after core/ingestion as justified | Optional |
| P2 | Mealie/KitchenOwl UX benchmarking | PR11–13 | Reference, no code reuse |
| P3 | Open Food Facts, Grocy interop, MCP | Retail/AI later | Not current |

---

# 9. Required integration regression pack

Create tests in the owning bounded context, not a single massive cross-domain PR. Minimum adversarial scenarios:

- **Identity/form:** chicken breast raw vs cooked different canonical truth; 2 pcs carrot → no unapproved grams; bad density remains UNKNOWN.
- **Recipe rights:** parsed recipe with no usage rights → review/reject; source URL/date/hash/parser version recorded; repeat ingest exact replay not duplicate.
- **Nutrition:** FDC absent macro is UNKNOWN, not 0; wrong per-100-g basis blocked; published NutritionVersion unchanged.
- **Planner:** `AI_ENABLED=false`, all 1–6 opportunities remain representable; household exclusions dominate; old/reproducible fixture pins preserved.
- **Shopping:** two matching ingredient demands aggregate once; pantry date/FEFO respected; derived source fingerprints stable; generation never consumes stock; unsupported LEFTOVER/PREPARED supply remains INCOMPLETE.
- **Pantry:** concurrent consume cannot go negative; cross-household access blocked; source parser cannot write Pantry.
- **Prep:** all UNKNOWN produces no executable task; only one approved event fails two-event technical gate; exact Step version/Decimal input; no implied safe batch/freezer; current revocation denial survives rollback.
- **Storage:** quality vs safety split; cooked-vs-raw and fridge-vs-freezer mismatch withheld; no source/temperature means no expiry authority.
- **Security:** malformed HTML/JSON, XSS/injection, URL→loopback/internal network SSRF, resource limits, unsupported encodings, huge input, replay, idempotent retries and PII minimization.
- **Licensing/reproducibility:** pinned dependency lock/version/notice, external dataset release/hash, fail-safe tool unavailable/AI disabled/retailer unavailable.

**Cross-context guard:** source-driven integration must not silently make Shopping/Prep/PDF current on a stale MealPlan revision. Immutable snapshots and explicit regeneration remain authoritative.

---

# 10. Draft PR delivery map for future Codex

Each item is a **single bounded PR**, after current owner explicitly authorizes and applicable contract gate is accepted. Do not open all PRs at once.

| Proposed PR ID (not actual GitHub #) | Goal | Scope | Non-goals | Tests / exit |
|---|---|---|---|---|
| `REUSE-DOC-1` | Exact duplicate-capability and evidence baseline | Docs-only; source/licensing + accepted main matrix | No dependency/runtime/schema | Independent docs review and source pins |
| `REUSE-SPIKE-PARSER` | Compare existing ingestion vs MIT extractor | Offline fixture harness; no publishing | No crawling/API/new tables | Field-level benchmark, Go/No-Go with manual time comparison |
| `REUSE-CONTRACT-PARSER` | Freeze approved parser→candidate anti-corruption interface | **Docs-only contract gate** if new authority/persisted contract | No runtime | QA adversarial matrix and rollback |
| `DATA-RECIPE-ADAPTER` | Controlled integration of winning recipe parser | Admin ingestion boundary, shadow mode | No consumer UI, auto publish, LLM truth | Idempotent/import/reject tests; rights enforcement |
| `DATA-NUTRIENT-EVIDENCE` | FDC/FBG controlled enrichment | Data adapter & source version evidence | No food IDs/schema leaks | Source/form and unknown-value regression |
| `PR10-SAFETY-RESEARCH` | FoodKeeper source/policy applicability | docs + isolated evidence snapshots | No expiry/runtime/PreparedBatch approval | Qualified review and unsupported-case matrix |
| `UX-BENCHMARK` | Derive mobile interactions from market reference | PR11–13 research/UX specs | No borrowed AGPL components | Russian UX, stale/error state tests |
| `PORTABLE-RECIPE` | Optional Cooklang adapter | External import/export boundary | No canonical storage replacement | Roundtrip supported subset and loss report |
| `AI-TOOL-BROKER` | Optional structured proposal tools | Only after AI authorization | No direct critical writes | Authorization, prompt injection, AI=false |

Every actual task must contain `Context / Goal / Scope / Non-goals / Architecture constraints / Data model / API / Frontend / Tests / Acceptance criteria / Risks / Required final report`. Include `N/A` for irrelevant sections. Before high-coupling runtime: docs-only implementation gate reviewed+merged, then bounded runtime PR, then exact-head tests, independent review, explicit human merge. Update `state/current-focus.md`, `state/progress.md`, `state/handoff.md` only on actually authorized work.

---

# 11. Open questions / stop conditions

1. **Which current corpus preparation/import tools already solve the same parsing job?** Need repository-wide targeted audit before a dependency is adopted (this research examined key runtime files, not every ingest script).
2. **Do existing source corpora contain rights-cleared HTML/JSON-LD with representative Russian ingredient strings?** Without that, parser ROI cannot be measured honestly.
3. **Would adapting the English-only `ingredient-parser-nlp` to Russian save more work than a bounded dictionary/regex baseline?** No ready-made RU support exists upstream. Labelled RU data, language-specific processing, model training and maintenance costs must be evaluated separately; this RFC does not authorize that development.
4. **What is an authoritative and applicable storage-safety policy for Russian household finished dishes?** FoodKeeper by itself does not close this gate.
5. **How to prove physical serving size/output at accepted home scale?** Neither external planner nor USDA FBG automatically passes `PORTION_RELEASE_READY`.
6. **Does Cooklang transfer any field currently painful to store/export?** If not, no reason to add an early import format.
7. **What commercial/license posture will FamilyFoodOS adopt?** Any AGPL/ODbL/Commons-Clause integration requires a documented approval before production reuse.
8. **How will full historical Planner input parity and test-only seed identity be proven without changing production Planner?** Merged PR #248 now retains the complete original receipt and freezes the bounded contract; actual fixture reproducibility remains unproven and requires separately authorized work, independent from external library adoption.

**Mandatory stop:** fail any licensing, rights, food-form, provenance, source-text, reproducibility, safety, household isolation or high-coupling gate → **NO_GO** until reviewed alternative is accepted. No amount of interface convenience overrides these checks.

---

# 12. Evidence register — primary URLs

### FamilyFoodOS repository, historical snapshot and refreshed accepted baseline

- Repo: https://github.com/Mitronomik/family-food-os
- Accepted 2026-10-27 PR #244: https://github.com/Mitronomik/family-food-os/pull/244
- PR #246 MERGED 2026-10-29 at `36ab339302557aafc2187f9d8a70b035869c8487` (negative fixture evidence retained): https://github.com/Mitronomik/family-food-os/pull/246
- PR #248 MERGED 2026-10-29 at refreshed accepted main `edba04dcd491ef9663fe82c96f6f0c1c76504a27`, accepted HEAD `120d997f80e6f0aec0f15002567687a14813e216`; contract/evidence/test-only, no runtime approval: https://github.com/Mitronomik/family-food-os/pull/248
- Accepted Option A contract and remaining input/seed-seam limits: https://github.com/Mitronomik/family-food-os/blob/edba04dcd491ef9663fe82c96f6f0c1c76504a27/docs/family-food/pr10-core-option-a-stable-fixture-implementation-contract-2026-10-27.md
- Existing FDC seed/import (pinned accepted main): https://github.com/Mitronomik/family-food-os/blob/36ab339302557aafc2187f9d8a70b035869c8487/backend/app/seed/food_ingredients.py
- Existing controlled source-corpus extraction (same pin): https://github.com/Mitronomik/family-food-os/blob/36ab339302557aafc2187f9d8a70b035869c8487/backend/app/services/recipe_source_corpus_import.py
- Implemented Planner PR #59: https://github.com/Mitronomik/family-food-os/pull/59
- Implemented Shopping PR #186/#188/#190: https://github.com/Mitronomik/family-food-os/pull/186 , https://github.com/Mitronomik/family-food-os/pull/188 , https://github.com/Mitronomik/family-food-os/pull/190
- Canonical project docs: `AGENTS.md`, `docs/family-food/architecture.md`, `docs/family-food/master-roadmap.md`, later addenda, `docs/family-food/security-architecture.md`, `docs/family-food/data-corpus-v1.md`, PR10 contracts.

### External systems and legal sources

- Grocy GitHub/openapi/license: https://github.com/grocy/grocy , https://github.com/grocy/grocy/blob/master/grocy.openapi.json , https://github.com/grocy/grocy/blob/master/LICENSE.md
- Eat This Much: https://www.eatthismuch.com/how-to/
- Tandoor README/licensing: https://github.com/TandoorRecipes/recipes
- Mealie README/licensing: https://github.com/mealie-recipes/mealie
- KitchenOwl README/licensing: https://github.com/TomBursch/kitchenowl
- RecipeSage licensing: https://github.com/julianpoy/recipesage
- Cooklang/CookCLI MIT: https://cooklang.org/ , https://github.com/cooklang/cookcli
- Python recipe-scrapers doc/license: https://docs.recipe-scrapers.com/ , https://github.com/hhursev/recipe-scrapers
- Ingredient-parser-nlp MIT: https://github.com/strangetom/ingredient-parser
- Ingredient-parser English-only support and separate-language adaptation requirements (checked 2026-10-29): https://ingredient-parser.readthedocs.io/en/latest/how-to/extending.html
- USDA FDC CC0/licensing/dumps: https://fdc.nal.usda.gov/api-guide/ , https://fdc.nal.usda.gov/download-datasets/
- USDA Food Buying Guide tables/RAW: https://foodbuyingguide.fns.usda.gov/Appendix/DownLoadFBG , https://foodbuyingguide.fns.usda.gov/Appendix/ResourceAppendixA
- USDA FoodKeeper dataset JSON/XLS and CC0 metadata: https://catalog.data.gov/dataset/fsis-foodkeeper-data
- Open Food Facts documentation: https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/
- Army AFRS: https://quartermaster.army.mil/jccoe/publications/food_links.html

---

# 13. Final recommendation / proposed authorization

**Approve conceptually** the *reuse-first, bounded integration strategy*. **Do not yet approve** any production dependency, schema or API change. Immediate practical first step, if owner explicitly authorizes, is **`REUSE-DOC-1` docs-only audit of our currently accepted source/import tooling and contracts**. The result determines whether a parser experiment saves anything in the real codebase; it must not interrupt the already authorized PR10 fixture/review path. Only then propose the **single** highest-return isolated spike, with measurable baseline and go/no-go. No parallel feature branches or hidden reprioritization.

The fastest compliant path is to **stop reimplementing plumbing at data boundaries, but keep the domain logic and authoritative state under FamilyFoodOS control**.
