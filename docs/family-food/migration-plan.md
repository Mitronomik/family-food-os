# FamilyFoodOS — Migration Plan from CosmeticWorkshopOS

**Версия:** 0.1
**Статус:** рабочий контракт миграции
**Исходный проект:** `Mitronomik/cosmetic-workshop-os`
**Целевой проект:** `Mitronomik/family-food-os`
**Исходная ветка:** `main`
**Исходная контрольная точка:** `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
**Метод реализации:** последовательные небольшие PR через Codex / Claude Code
**Цель первой фазы:** рабочий FamilyFoodOS MVP с полным циклом:

```text
Household
→ Members
→ Recipe Catalogue
→ Nutrition
→ MealPlan
→ Servings
→ Pantry
→ Shopping
→ Prep
→ PDF
```

Основной цикл MVP должен работать **без LLM и без retail parsers**.

## Каноническое разграничение документов

`docs/family-food/master-roadmap.md` — канонический контракт текущей
последовательности реализации и delivery gates. При конфликте старого порядка
в этом документе с Master Roadmap действует Master Roadmap.

Этот Migration Plan отвечает за:

- стратегию миграции;
- reuse/removal strategy;
- дисциплину замены legacy bounded contexts;
- bounded migration notes;
- историческое обоснование миграции.

Master Roadmap отвечает за текущий implementation order, delivery gates и
момент, когда разрешены PWA, Auth, Retail, AI и Billing.

---

# 1. Назначение документа

Документ определяет последовательность преобразования существующего проекта `cosmetic-workshop-os` в новый продукт `family-food-os`.

Главная цель — максимально использовать уже проверенные инженерные решения существующего репозитория, не перенося в новый продукт неподходящие косметические сущности и архитектурный долг.

Миграция выполняется не как одномоментное переписывание приложения.

Используется стратегия:

> **Fork → Stabilize → Introduce new domain → Replace bounded contexts → Remove legacy domain → Build new consumer UI → SaaS hardening.**

После каждого PR репозиторий должен:

- собираться;
- запускаться;
- проходить актуальный набор тестов;
- не содержать промежуточного состояния, которое невозможно продолжать безопасно.

---

# 2. Основные архитектурные решения

## 2.1. Backend переиспользуется

Сохраняются как базовые архитектурные паттерны:

```text
FastAPI
→ API routers
→ services
→ repositories
→ persistence
```

Сохраняются:

- разделение business logic и UI;
- immutable domain objects там, где это оправдано;
- Decimal для чувствительных числовых расчётов;
- migrations;
- transaction boundaries;
- AuditLog;
- import preview/apply;
- backup/export safety;
- structured errors;
- demo/seed infrastructure;
- тестовая инфраструктура.

---

# 3. Что не переносится как доменная модель

Не допускается механический rename:

```text
Client → HouseholdMember
Order → MealPlan
ProductionBatch → PrepBatch
PackagingItem → FoodPackage
```

Такие сущности имеют различную семантику.

Правило:

> сначала создаётся новая food-domain сущность, затем переводятся зависимости, затем старая сущность удаляется.

---

# 4. Frontend strategy

Существующий frontend используется как источник:

- UI/UX принципов;
- feedback patterns;
- loading/error states;
- dirty-state logic;
- confirmation patterns;
- accessibility решений;
- русского user-facing copy;
- tested interaction patterns.

Однако consumer frontend FamilyFoodOS создаётся как новое приложение.

Целевой frontend:

```text
Next.js
TypeScript
PWA
mobile-first
```

Старый vanilla TypeScript frontend не является целевой основой пользовательского приложения.

---

# 5. Временная persistence strategy

Для первых этапов:

```text
SQLite
```

используется для:

- local development;
- vertical slice;
- fixture testing;
- planner development.

Перед первым shared multi-family deployment:

```text
PostgreSQL
+
Auth
+
HouseholdMembership / authorization
+
Tenant isolation
+
Hosted operational baseline
```

становятся обязательными.

Это deployment gate, а не требование для local/isolated vertical slice.
Billing и subscriptions остаются отдельным более поздним commercial concern и
не входят в этот safety gate.

Для новых food bounded contexts runtime persistence использует synchronous
SQLAlchemy 2.x Core за repository/Unit-of-Work boundary. Пока активной базой
vertical slice остаётся SQLite, единственный schema authority — существующий
custom migration runner и его ordered lineage; новые food migrations добавляются
в эту цепочку. Alembic, `MetaData.create_all()` и вторая migration history против
активной SQLite базы запрещены.

Отдельный PostgreSQL cutover PR должен определить target schema baseline,
перенос и reconciliation данных, активацию PostgreSQL adapter и freeze исходной
SQLite lineage. После cutover Alembic становится единственным schema migration
authority для PostgreSQL. SQLite-specific historical migrations не обязаны
воспроизводиться против PostgreSQL. Ни одна физическая база не управляется двумя
независимыми migration histories.

---

# 6. Git strategy

Создать новый репозиторий с сохранением истории.

Пример:

```bash
cd ~/Projects

git clone \
  https://github.com/Mitronomik/cosmetic-workshop-os.git \
  family-food-os

cd family-food-os

git checkout main
git pull --ff-only

git tag bootstrap-cosmetic-workshop-2026-08-31

git remote rename origin cosmetic-upstream

git remote add origin \
  git@github.com:Mitronomik/family-food-os.git

git push -u origin main
git push origin bootstrap-cosmetic-workshop-2026-08-31
```

После этого:

```bash
git switch -c migration/pr0-frozen-fork
```

---

# 7. Правила PR

Каждый PR обязан содержать:

```text
Goal
Scope
Non-goals
Architecture impact
Data model impact
Migration impact
Backend changes
Frontend changes
Tests
Acceptance criteria
Known limitations
Follow-up
```

PR не должен одновременно:

- менять несколько независимых bounded contexts;
- выполнять массовый rename и менять business logic;
- менять persistence technology и domain model;
- менять backend и полностью redesign frontend без необходимости;
- подключать AI и изменять deterministic core одновременно.

---

# 8. Общий порядок

```text
✅ PR0   Frozen Fork
✅ PR1   Identity Detox
✅ PR2-A Architecture & Persistence Contract
✅ PR2-B Persistence Foundation
✅ PR2-C Household Foundation

→ PR3   FoodIngredient Catalogue
→ PR4   Recipe Catalogue
→ PR5   Pantry
→ PR6   Nutrition Core
→ PR7   MealPlan / Serving + serving-nutrition integration
→ PR8   Planner v0

──────── GATE 1 — PLANNING CORE ────────

→ PR9   Shopping Engine
→ PR10  Prep / Freezer
→ PR10-PDF Backend Weekly PDF

──────── GATE 2 — MVP0 BACKEND ────────

→ PR11  Consumer PWA Shell
→ PR12  Household Onboarding UX
→ PR13  Today / Week / Shopping / Prep / Pantry UX
→ PR14  PDF / Print UX
→ PR15  Feedback & History v0

──────── GATE 3 — CONSUMER CORE ────────

→ DATA READINESS GATE

→ SHARED-1 PostgreSQL Cutover
→ SHARED-2 Auth + HouseholdMembership
→ SHARED-3 Tenant Isolation + Hosted Operations

──────── GATE 4 — SHARED DEPLOYMENT ────────

→ REAL FAMILY TESTING
   10–30 households
   week → use → feedback → next week

→ DATA PROGRAM — Data Ingestion Platform
→ Catalogue expansion / quality automation

→ RETAIL PROGRAM — Retail Foundation
→ Retail Connector #1

→ Optional AI Gateway

→ Commercial / Billing
→ Production Hardening
→ Additional Retail Connectors
→ Production v1
```

Эту последовательность нельзя материально менять внутри Migration Plan.
`PR2-DOCS` является docs-only governance operation между PR2-C и PR3, а не
новым product milestone.

---

# PR0 — Frozen Fork

## Goal

Создать технически идентичную копию CosmeticWorkshopOS и зафиксировать доказуемую стартовую точку.

## Scope

- клонировать repository history;
- создать новый remote;
- создать bootstrap tag;
- проверить branch;
- зафиксировать исходный commit;
- прогнать backend tests;
- прогнать frontend build;
- прогнать frontend tests;
- проверить запуск приложения.

Создать:

```text
docs/migration-source.md
```

В документе сохранить:

- source repository;
- source commit;
- source tag;
- дату fork;
- команды проверки;
- результаты тестов.

## Non-goals

Не менять:

- product name;
- UI;
- domain;
- database schema;
- API;
- branding.

## Files to keep

Практически весь репозиторий.

## Acceptance criteria

- новый repository существует;
- история Git сохранена;
- `bootstrap-cosmetic-workshop-2026-08-31` существует;
- working tree clean;
- backend tests проходят;
- frontend build проходит;
- frontend tests проходят;
- приложение запускается;
- fork reproducible.

---

# PR1 — Identity Detox

## Goal

Отделить новый repository от идентичности CosmeticWorkshopOS, не меняя business domain.

## Scope

Изменить:

```text
cosmetic-workshop-os
→ family-food-os
```

```text
COSMETIC_WORKSHOP_*
→ FAMILY_FOOD_*
```

Обновить:

- Python package metadata;
- frontend package metadata;
- app title;
- product constants;
- env variables;
- database default filename;
- user-data directory;
- README;
- launcher naming;
- test fixtures, связанные только с identity;
- GitHub-oriented documentation.

Создать:

```text
docs/migration-plan.md
docs/family-food-product-brief.md
```

## Project-owned skill

Создать:

```text
.agents/skills/family-food-ui/
```

Старый `cosmetic-workshop-ui` удалить или архивировать только после переноса необходимых общих правил.

## Non-goals

Не менять:

- таблицы business domain;
- рецептурную математику;
- clients;
- orders;
- production.

## Acceptance criteria

Поиск:

```bash
rg -n "cosmetic-workshop|Мастерская косметолога|COSMETIC_WORKSHOP"
```

не должен показывать runtime-зависимостей, кроме:

- migration history;
- historical docs;
- source provenance.

Все тесты остаются зелёными.

---

# PR2 — Completed foundation split

Старый единый этап `PR2 — Food Domain Foundation` заменён и полностью завершён
тремя bounded milestones:

```text
PR2-A Architecture & Persistence Contract — COMPLETE
PR2-B Persistence Foundation               — COMPLETE
PR2-C Household Foundation                 — COMPLETE
```

PR2-A зафиксировал dependency direction, synchronous SQLAlchemy 2.x Core,
repository/Unit-of-Work boundary, custom SQLite migration authority и
PostgreSQL/Auth/tenant-isolation gate. PR2-B реализовал persistence foundation
без production food schema. PR2-C реализовал `Household` и `HouseholdMember`
через migration `0022_household_foundation`.

PR2-C принят итоговым project review (`PR2-C FINAL REVIEW: ACCEPT`) и merged в
GitHub PR `#5`; merge commit:
`48c72aeba19a1e6ece0dc729f0a80de930be88a8`.

PR2 больше не является будущим implementation PR.

---

# PR3 — FoodIngredient Catalogue

## Goal

Создать canonical platform-owned каталог пищевых ингредиентов. Каталог не
принадлежит отдельному Household.

`FoodIngredient` — canonical repository-domain name. `CanonicalIngredient` в
ранних Project Sources — исторический alias того же понятия, а не второй
aggregate.

`FoodProductType` не является обязательным MVP aggregate. Retail/catalogue
classification может появиться позже только при подтверждённом downstream use
case.

## Minimum model and capabilities

```text
FoodIngredient
IngredientAlias
FoodNutritionProfile / equivalent provenance representation
IngredientUnitProfile where genuinely required
```

Поддержать:

- canonical code и name;
- category;
- default unit;
- optional density;
- edible fraction;
- nutrition/macros/fiber либо ссылку на nutrition profile;
- nutrition source/version/provenance;
- allergen metadata;
- storage metadata/profile;
- active/deactivate;
- timestamps;
- name/alias lookup;
- idempotent seed/import.

## Что переиспользовать

Из старого Ingredient допускается адаптировать:

- ID conventions;
- unit validation;
- Decimal patterns;
- archive/deactivate behavior;
- repository/service patterns;
- catalog category/tag ideas.

Не переносить косметические поля и invariants:

```text
inci_name
supplier_hint
cosmetic usage notes
cosmetic categories
```

## Technical slice

Первая реализация содержит:

**80–120 `FoodIngredient`.**

Более широкий MVP target остаётся примерно **250–350**, но PR3 не должен
пытаться реализовать полную automation платформы каталогов.

## Tests

- idempotent seed/import;
- alias lookup;
- unit validation;
- Decimal semantics;
- nutrition provenance required;
- duplicate prevention;
- deactivation behavior;
- no `RetailSKU` coupling.

## Non-goals

- `RetailSKU`;
- retailer parsing;
- retailer prices;
- full ingestion automation;
- Recipe;
- Pantry;
- Nutrition Engine calculations;
- Planner;
- AI.

## Persistence constraints

PR3 продолжает synchronous SQLAlchemy 2.x Core через repository contracts и
Unit of Work, использует SQLite и custom migration chain, добавляет следующую
migration после `0022` и не вводит Alembic, ORM, async, PostgreSQL или Auth.

## Acceptance criteria

Платформа идемпотентно создаёт bounded catalogue slice, не создаёт duplicates,
находит ингредиенты по имени/alias, требует verifiable nutrition provenance,
корректно деактивирует записи и не связывает `FoodIngredient` с `RetailSKU`.

---

# PR4 — Recipe Catalogue

## Goal

Адаптировать сильную часть существующего RecipeVersion architecture для еды.

## Сохранить концепцию

```text
Recipe
→ RecipeVersion
→ RecipeIngredient
```

Допускается сохранить имя `RecipeTemplate`, если оно остаётся архитектурно полезным.

## Recipe

Добавить:

```text
meal_type
servings
prep_time_minutes
cook_time_minutes
difficulty

child_friendly
batch_friendly
freezable

storage_days_fridge
storage_days_freezer
```

## RecipeVersion

Сохраняются:

- immutable historical versions;
- source version;
- change note;
- active/draft/archive.

## RecipeIngredient

```text
recipe_version_id
food_ingredient_id
quantity
unit
position
prep_note
optional
```

## RecipeStep

Создать отдельную сущность:

```text
RecipeStep
```

## Удалить food-incompatible rules

Не использовать:

- косметическую нормализацию процентов;
- обязательную сумму 100%;
- cosmetic phases как основной calculation invariant.

`phase` можно сохранить как optional cooking group/stage, если полезно.

## Seed

Добавить:

**30 рецептов для vertical slice.**

## Acceptance criteria

Для каждого recipe:

```text
load recipe
→ scale servings
→ calculate ingredients
→ return structured preparation steps
```

Историческая версия не изменяется после создания новой.

---

# PR5 — Pantry

## Goal

Превратить проверенные inventory concepts в домашний учёт продуктов.

## Новые сущности

```text
PantryItem
PantryMovement
```

Опционально:

```text
PantryLot
```

если lot semantics дают реальную пользу.

## Storage locations

```text
PANTRY
FRIDGE
FREEZER
```

## PantryItem

```text
household_id
ingredient_id
quantity
unit
location

purchase_date
opened_at
expires_at

estimated
active
```

## PantryMovement

```text
IN
OUT
ADJUSTMENT
CONSUMPTION
WASTE
```

## Переиспользовать

- transaction model;
- stock movement pattern;
- negative balance protection;
- expiration logic;
- FEFO;
- auditability.

## Упростить

Для household UX нельзя заставлять пользователя вести промышленный lot accounting.

Должно поддерживаться:

```text
"яйца — 6 шт."
```

без supplier/lot-code.

## Acceptance criteria

```text
buy 10 eggs
→ pantry = 10

consume 4
→ pantry = 6

attempt consume 10
→ safe error
```

---

# PR6 — Nutrition Core

## Goal

Создать deterministic Nutrition Core до появления Serving.

## Новый module

```text
backend/app/services/nutrition/
```

или согласованная аналогичная структура.

## Ответственность

```text
FoodIngredient nutrition
→ RecipeVersion nutrition
→ Member target formula/config foundation
```

PR6 не рассчитывает Serving, member/day totals или week aggregates: сущность
`Serving` появляется только в PR7.

## Основное правило

LLM запрещён внутри Nutrition Engine.

## Вход и выход

Входом служат versioned `FoodIngredient` nutrition data, `RecipeVersion` и
данные `HouseholdMember`, необходимые для target formula/config foundation.
Результат включает детерминированные kcal/macros/fiber, member target profile и
явные warnings без зависимости от Serving.

## Требования

Расчёты должны иметь:

- deterministic output;
- versioned formula/config;
- unit tests;
- bounded rounding.

## Fixtures

Добавить тестовые семьи:

```text
family_2_adults
family_2_adults_1_child
family_2_adults_2_children
```

## Non-goals

- медицинские диагнозы;
- лечебное питание;
- LLM recommendations.

## Acceptance criteria

Одинаковый input всегда даёт один и тот же output.

---

# PR7 — MealPlan / Serving + serving-nutrition integration

## Goal

Создать центральную сущность новой системы.

## Новые сущности

```text
MealPlan
MealPlanDay
MealSlot
Serving
```

## MealPlan

```text
household_id
week_start
status

budget_target
planning_mode
created_at
```

## MealSlot

Пример:

```text
BREAKFAST
LUNCH
DINNER
SNACK
```

## Serving

Связь:

```text
Meal
→ HouseholdMember
→ portion
```

Один рецепт может иметь разные порции для разных членов семьи.

## Nutrition integration

PR7 интегрирует:

```text
RecipeVersion nutrition
→ Serving nutrition
→ Member/day totals
→ week aggregates
```

MealPlan history начинается вместе с MealPlan context. Structured feedback и
personalization history принадлежат PR15.

## Non-goals

Не переименовывать `Order`.

Создать новый bounded context.

## Acceptance criteria

Для семьи из трёх человек можно вручную собрать:

```text
7 days
× meals
× recipe
× member servings
```

и получить корректный structured MealPlan.

---

# PR8 — Planner v0

## Goal

Автоматически создавать недельный MealPlan.

## Planner inputs

```text
Household
Members
Recipes
Nutrition
Preferences
Excluded ingredients
Budget
Cooking constraints
Recent history
Pantry
```

## Planner v0

Первоначально допускается:

- deterministic scoring;
- heuristics;
- constraint filtering.

Не нужно начинать сразу с математически идеального solver.

## Candidate score

Пример:

```text
cost
nutrition fit
preference
cooking time
repetition
pantry usage
batch compatibility
```

## Hard constraints

- исключённый ингредиент отсутствует;
- рецепт доступен;
- количество повторов ограничено;
- meal type подходит;
- week complete.

## Soft constraints

- бюджет;
- разнообразие;
- cooking time;
- leftovers;
- preferences.

## Planner Debug Trace

Сохранять:

```text
candidate
score
rejected_reason
selected_reason
```

## Acceptance criteria

Тестовая семья получает полный 7-day MealPlan без ручного выбора рецептов.

---

# GATE 1 — PLANNING CORE

После PR8 запрещено переходить дальше, пока не работает:

```text
Household
→ Recipe catalogue
→ Nutrition
→ Planner
→ 7-day MealPlan
→ individualized servings
```

Минимум:

- 3 fixture households;
- 30 verified recipes;
- 80+ `FoodIngredient`;
- deterministic Planner;
- соблюдение exclusions и всех hard constraints;
- complete week для каждого fixture либо явный bounded failure;
- individualized Servings;
- reproducible planner trace с candidates, rejections, scores, selections и
  warnings.

---

# PR9 — Shopping Engine

## Goal

Автоматически получить список покупок из MealPlan.

## Pipeline

```text
MealPlan
→ RecipeIngredients
→ Scale by servings
→ Aggregate
→ Subtract Pantry
→ ShoppingList
```

## Новые сущности

```text
ShoppingList
ShoppingItem
```

## ShoppingItem

```text
ingredient_id
required_quantity
pantry_quantity
purchase_quantity
unit
estimated_price
status
```

## Цены

Пока:

```text
FoodIngredient.average_price
```

или отдельная generic price table.

## Non-goals

- RetailSKU;
- магазины;
- scraping.

## Acceptance criteria

Меню из 20 блюд с повторяющимися ингредиентами создаёт единый агрегированный список без дублей.

---

# PR10 — Prep / Freezer

## Goal

Создать план предварительных заготовок.

## Новые сущности

```text
PrepPlan
PrepTask
PreparedBatch
```

## Planner должен понимать

- batch-friendly recipe;
- freezer-friendly recipe;
- repeated ingredient preparation;
- cooking dependencies.

## Пример результата

```text
Воскресенье

1. сварить рис
2. подготовить 1.5 кг фарша
3. сделать 12 тефтелей
4. сделать 8 котлет
5. заморозить часть
```

## Freeze fields

```text
freeze_stage
freezer_life
defrost_method
reheat_method
```

## Non-goals

- industrial ProductionBatch semantics;
- sale price;
- packaging;
- taxes.

## Acceptance criteria

MealPlan автоматически выдаёт PrepPlan.

---

# PR10-PDF — Backend Weekly PDF

## Goal

Создать backend-generated Weekly PDF как derived artifact уже существующего
детерминированного состояния:

```text
MealPlan + ShoppingList + PrepPlan
→ Backend Weekly PDF
```

Минимальный artifact содержит меню недели, shopping list, prep/freezer plan и
краткие рецепты/инструкции. Он должен быть A4-readable, reproducible по source
revisions и renderer version, безопасно создаваться без silent overwrite и не
становиться source of truth.

PR10-PDF находится в MVP0 backend до Consumer PWA. Consumer download/print UX
появится отдельно в PR14.

## Non-goals

- Consumer PWA;
- browser print/download UX;
- Auth;
- Retail;
- AI.

---

# GATE 2 — MVP0 BACKEND

На этом этапе backend должен поддерживать полный vertical slice:

```text
Household
→ Members
→ Planner
→ 7-day MealPlan
→ Serving calculation
→ ingredient aggregation
→ Pantry subtraction
→ ShoppingList
→ PrepPlan
→ PDF
```

Обязательные условия:

```text
AI_ENABLED=false
RetailConnector=none
```

Exact fixture:

- 1 Household;
- 3 members;
- 30 verified recipes;
- 80–120 `FoodIngredient`.

Backend Weekly PDF уже существует.

Все основные операции покрыты API tests.

---

# PR11 — Consumer PWA Shell

## Goal

Создать новый мобильный пользовательский интерфейс.

## Новый frontend

Рекомендуется:

```text
frontend-next/
```

до момента окончательного переключения.

После migration:

```text
frontend/
```

## Stack

```text
Next.js
TypeScript
PWA
```

## Основная navigation

```text
Сегодня
Неделя
Купить
Заготовки
Дома
```

Secondary:

```text
Семья
Настройки
```

## Не переносить

Consumer пользователь не видит:

- API;
- migrations;
- import drafts;
- audit IDs;
- system catalog;
- retailer matching;
- technical health status.

## Acceptance criteria

Приложение удобно работает:

- 375 px;
- 390 px;
- 430 px;
- tablet;
- desktop.

Horizontal page overflow отсутствует.

---

# PR12 — Household Onboarding UX

## Goal

Получить первую неделю максимум за несколько минут.

До появления Auth это onboarding Household и первой недели, а не
account-registration/auth onboarding. Fixture/local identity не должна
маскироваться под готовую авторизацию.

## Flow

### Step 1

Сколько человек?

### Step 2

Возраст / базовые параметры.

### Step 3

Что не едите?

### Step 4

Примерный недельный бюджет.

### Step 5

Сколько готовы готовить?

### Step 6

Где обычно покупаете?

### Step 7

Создать неделю.

## UX rule

Не более:

**5–7 коротких экранов.**

Не спрашивать данные, которые можно заполнить default.

## Progressive profiling

Необязательные параметры запрашивать позже.

## Acceptance criteria

Новый пользователь проходит:

```text
empty product state
→ household
→ family members
→ constraints
→ first MealPlan
```

без обращения к admin UI.

---

# PR13 — Today / Week / Shopping / Prep / Pantry UX

## Goal

Сделать основную неделю реально используемой.

## `/today`

Показывает:

- сегодня;
- блюда;
- порции;
- время;
- что достать из морозилки.

## `/week`

Показывает:

```text
ПН–ВС
```

с возможностью:

- открыть рецепт;
- заменить;
- пропустить;
- перенести.

## `/shopping`

- checklist;
- группировка по отделам;
- стоимость.

## `/prep`

- последовательность заготовок;
- freezer instructions.

## `/pantry`

- краткие остатки;
- быстрый ввод.

## Acceptance criteria

Основные household jobs выполняются максимум в 1–3 действия.

---

# PR14 — PDF / Print UX

## Goal

Добавить consumer download/print UX для backend Weekly PDF, уже реализованного
в PR10-PDF.

## Consumer UX

Пользователь может открыть, скачать и распечатать существующий artifact.
Представление охватывает:

### Page 1

Меню недели.

### Page 2

Покупки.

### Page 3

Заготовки.

### Далее

Краткие рецепты.

PR14 не владеет backend PDF generation, его persistence/provenance или
renderer. Он использует существующий backend API/artifact contract.

## Acceptance criteria

Consumer PDF/Print UX:

- A4;
- русский текст;
- читаемый;
- печатаемый;
- соответствует текущему MealPlan.

---

# PR15 — Feedback & History v0

## Goal

Замкнуть цикл `week → use → feedback → next week` до real-family testing и до
Retail, полностью без обязательного LLM.

## Structured signals

```text
LIKED
DISLIKED
SKIPPED
REPLACED
LEFTOVER
REPEAT_REQUESTED
```

## Minimum model/capabilities

```text
MealFeedback
RecipePreferenceScore
HouseholdIngredientPreference, where justified
```

MealPlan history начинается раньше, вместе с MealPlan context в PR7. PR15
владеет structured feedback и deterministic personalization/history signals,
которые Planner использует для следующей недели.

## Acceptance criteria

Household может завершить неделю, сохранить structured feedback и получить
детерминированное изменение scoring следующего плана. Например, повторно
отклонённый рецепт получает более низкую вероятность нового предложения.

---

# GATE 3 — CONSUMER CORE

Consumer flow должен поддерживать:

```text
Household onboarding
→ generate week
→ Today / Week
→ meal change
→ recalculated Shopping
→ Pantry
→ Prep
→ PDF/print
→ finish week
→ structured feedback
→ next week
```

PR12 onboarding до Auth означает Household/product setup, а не регистрацию
аккаунта.

---

# DATA READINESS GATE

Data Readiness — quality gate, а не требование заранее реализовать полную Data
Ingestion Platform.

До real-family testing активный каталог должен иметь:

- `50–80+` verified recipes;
- complete required `FoodIngredient` resolution;
- `100%` required FoodIngredient coverage для active recipe corpus;
- valid nutrition source/version/provenance;
- отсутствие unresolved required ingredients;
- отсутствие critical sanity-validation errors;
- reviewable RecipeVersion source provenance и rights status;
- reasonable weekly variety;
- broader FoodIngredient target примерно `250–350`.

Gate может быть закрыт bounded seed/import и review work. Полная ingestion
automation следует позже в Data Program.

---

# SHARED-1 — PostgreSQL Cutover

## Goal

До shared-family deployment определить PostgreSQL target baseline, перенос и
reconciliation данных, adapter conformance и freeze/retirement правила custom
SQLite lineage. Только на этом явном cutover Alembic может стать единственным
PostgreSQL migration authority.

---

# SHARED-2 — Auth + HouseholdMembership

## Goal

Добавить authenticated principal, `HouseholdMembership`, roles/authorization и
trusted propagation разрешённого Household scope. Client-provided
`household_id` не является proof of authorization.

---

# SHARED-3 — Tenant Isolation + Hosted Operations

## Goal

Доказать adversarial tenant isolation и установить hosted operational baseline:
deployment, secrets, backup/restore, monitoring и безопасные migration
operations для shared environment.

---

# GATE 4 — SHARED DEPLOYMENT

До того как независимые реальные семьи используют один deployment, обязательны:

```text
PostgreSQL
+ Auth
+ HouseholdMembership / authorization
+ tenant isolation
+ hosted operational baseline
```

Billing не входит в этот safety gate.

---

# REAL FAMILY TESTING

После Consumer Core, Data Readiness и Shared Deployment gates начинается
тестирование на **10–30 households**:

```text
week → use → feedback → next week
```

Local или isolated single-Household validation может выполняться раньше, но не
должна называться shared real-family testing.

---

# DATA PROGRAM — Data Ingestion Platform

## Goal

После core/shared-family validation убрать ручное администрирование и расширять
качество системной базы через automation.

## Основные pipelines

```text
IngredientBootstrapJob
RecipeImportJob
NutritionImportJob
AliasResolutionJob
ValidationJob
```

Сохраняется безопасный flow:

```text
Source
→ Draft
→ validation
→ preview/review or trusted-source policy
→ apply
```

`IngestionJob`, `RawSourceRecord` и `ReviewQueueItem` могут поддерживать
catalogue expansion / quality automation. Повторный импорт идемпотентен, а
untrusted parsed data не становится production truth автоматически.

---

# RETAIL PROGRAM — Retail Foundation / Connector #1

## Goal

После generic Shopping Engine и Data Program добавить Retail как отдельный
enrichment layer.

## Model

```text
Retailer
RetailStore
RetailSKU
PriceSnapshot
RetailMapping
```

```text
FoodIngredient
→ RetailMapping
→ RetailSKU
→ PriceSnapshot
```

Первым вводится только один connector. Не импортируется весь ассортимент и не
обходятся технические защиты. Retail failure не ломает generic ShoppingList.

---

# Optional AI Gateway

AI добавляется только как provider-neutral optional layer поверх deterministic
system. Natural-language preferences, schedule changes, Pantry input,
replacement suggestions и explanations проходят deterministic validation.

```text
AI_ENABLED=false
```

не ломает ни один core workflow. AI не является источником истины для kcal,
nutrients, allergens, quantities, prices, availability, shopping или storage
safety.

---

# Commercial / Billing

Commercial capabilities появляются после core/shared-family validation,
Data/Retail foundation и optional AI position in the sequence. Billing остаётся
отдельным поздним concern и не входит в Shared Deployment gate.

Допускаются `Subscription`, tiers и feature flags, но они не ослабляют
Household authorization или tenant boundary.

---

# Production Hardening → Additional Retail Connectors → Production v1

Hardening включает production-grade observability, backup/restore, error
monitoring, safe migration procedure и operational evidence. Только после него
следуют дополнительные Retail Connectors и Production v1.

---

# 9. Legacy removal plan

Старые bounded contexts удалять только после появления функционального replacement.

## Cosmetic client domain

Удалить после:

```text
Household + HouseholdMember
```

стабилизированы.

Удаляются:

```text
Client
ClientRecipe
ClientWish
ClientFeedback
```

после переноса полезных patterns.

---

# 10. Orders domain

Удалить после появления:

```text
MealPlan
Shopping
Prep
```

Не пытаться сохранить Order как MealPlan.

---

# 11. Production domain

Удалить после появления:

```text
PrepPlan
PreparedBatch
PantryMovement
```

Сохранить только общие transactional patterns.

---

# 12. Packaging domain

Cosmetic packaging domain удалить.

Если в будущем понадобится:

```text
RetailPackage
```

это будет частью RetailSKU, а не наследником `PackagingItem`.

---

# 13. Finance/tax domain

Удалить полностью из consumer food product:

```text
tax rate
sale price
margin
profit
production revenue
```

FamilyFoodOS использует:

```text
food cost
budget
planned spend
actual spend
waste
```

Это новая финансовая семантика.

---

# 14. Reports domain

Существующие workshop reports заменить на:

```text
WeeklySummary
BudgetHistory
WasteHistory
MealAcceptance
RecipeHistory
```

---

# 15. Admin UI strategy

Consumer frontend не должен одновременно быть admin interface.

Предусмотреть отдельные restricted routes:

```text
/admin/ingredients
/admin/recipes
/admin/imports
/admin/retail
/admin/review
/admin/audit
```

Обычный household user их не видит.

---

# 16. Тестовая стратегия миграции

Каждый новый bounded context получает:

## Unit

- calculations;
- validation;
- scoring;
- unit conversion.

## Repository tests

- create;
- update;
- archive;
- tenant boundary позднее.

## Service tests

- business invariants.

## API tests

- happy path;
- validation;
- failure path.

## Integration tests

Главные цепочки.

---

# 17. Главный integration test MVP

Обязательный fixture:

```text
Household:
  2 adults
  1 child

Pantry:
  rice
  eggs
  carrots

Preferences:
  no mushrooms

Budget:
  configured
```

Тест:

```text
Generate MealPlan
        ↓
Validate 7 days
        ↓
Validate exclusions
        ↓
Calculate member servings
        ↓
Aggregate ingredients
        ↓
Subtract pantry
        ↓
Create ShoppingList
        ↓
Create PrepPlan
        ↓
Generate PDF
```

---

# 18. Regression policy

Пока legacy module существует, его тесты продолжают выполняться.

После удаления bounded context одновременно удаляются:

- API;
- models;
- repositories;
- services;
- schemas;
- migrations only if safely historical;
- frontend;
- tests;
- docs references.

Исторические migration files нельзя удалять необдуманно, если они необходимы для upgrade path.

---

# 19. Seed data

Создать отдельную структуру:

```text
data/
  seed/
    ingredients/
    recipes/
    households/
    pantry/
```

Не смешивать:

- test fixtures;
- production seed;
- demo data.

---

# 20. Demo household

Создать демонстрационную семью:

```text
Демо-семья

Анна
Сергей
Ребёнок
```

с:

- ограничениями;
- pantry;
- историей;
- планом.

Demo-mode должен позволять понять продукт без заполнения onboarding.

---

# 21. Observability уже на MVP

Planner особенно важно диагностировать.

Для каждого generation:

```text
generation_id
household_id
planner_version
recipe_pool
constraints
rejections
selected_recipes
score
duration
warnings
```

Нельзя диагностировать проблемы planner исключительно по жалобам пользователя.

---

# 22. Planner versioning

Каждый MealPlan должен помнить:

```text
planner_version
nutrition_engine_version
recipe_versions
```

Это позволит впоследствии понять:

> почему система составила именно такой план.

---

# 23. Migration completion criteria

Миграция CosmeticWorkshopOS → FamilyFoodOS считается завершённой, когда production repository больше не содержит runtime dependency на:

```text
Client
ClientRecipe
Order
ProductionBatch
PackagingItem
cosmetic Ingredient fields
tax/margin workshop logic
workshop profile
```

кроме:

- Git history;
- migration provenance;
- archived historical documentation.

---

# 24. Definition of Done для MVP

Пользователь может:

1. открыть PWA;
2. создать семью;
3. добавить членов;
4. указать ограничения;
5. указать бюджет;
6. получить готовую неделю;
7. посмотреть индивидуальные порции;
8. заменить блюдо;
9. увидеть автоматически пересчитанный shopping list;
10. отметить покупки;
11. перенести продукты в Pantry;
12. получить PrepPlan;
13. пользоваться экраном Today;
14. завершить неделю;
15. оставить feedback;
16. получить новую неделю;
17. скачать PDF.

Весь сценарий работает при:

```text
AI_ENABLED=false
```

и при отсутствии RetailConnector.

---

# 25. Definition of Done для Paid Beta

Shared-deployment prerequisites, которые должны быть выполнены раньше при
первом shared multi-family deployment:

- PostgreSQL;
- auth;
- `HouseholdMembership` / authorization;
- tenant isolation;
- hosted operational baseline;
- backups;
- monitoring;

Дополнительно для Paid Beta:

- проверенная recurring value и готовность к Commercial / Billing только после
  shared-safety gate;
- `Feedback & History v0`, уже обязательный до real-family testing;
- legal/privacy документы, соответствующие фактическому способу использования
  данных и коммерческому запуску;
- production operational readiness, включая support/incident ownership,
  security, backup/restore и monitoring на требуемом уровне.

`RetailConnector`, AI и admin ingestion UI не являются безусловными условиями
Paid Beta. Retail Connector добавляется только если актуальное product evidence
и отдельное решение подтверждают его необходимость. AI остаётся optional и
добавляется только если улучшает продукт при сохранении `AI_ENABLED=false`.
Admin ingestion UI появляется только при доказанной операционной потребности;
Data Readiness может быть достигнут bounded curation/import/review без полной
ingestion automation platform.

---

# 26. Оценка этапов

Старые оценки, привязанные к superseded downstream numbering, удалены: они
больше не являются planning authority. Сроки оцениваются отдельно для
canonical milestones и gates из `docs/family-food/master-roadmap.md` без
изменения их порядка.

---

# 27. Возможная параллельная работа агентов

Параллельная работа разрешена только внутри текущего milestone/gate или для
явно ограниченных supporting-задач, которые не реализуют будущий milestone:

- research и проверка evidence;
- QA, adversarial review и regression;
- fixture/data preparation в рамках уже разрешённого scope;
- документация и non-conflicting supporting work.

Параллельные агенты не дают разрешение перепрыгивать порядок
`docs/family-food/master-roadmap.md`. В частности:

- Planner implementation ждёт canonical PR8;
- Consumer PWA ждёт Gate 2 и PR11;
- Retail ждёт позднюю Retail Program;
- AI остаётся optional и поздним.

Один агент/оркестратор должен владеть:

- domain contracts;
- schema;
- API contracts;
- merge order.

---

# 28. Запрещённые shortcuts

Не допускается:

### 1.

Переименовать все cosmetic models массовым search/replace.

### 2.

Начать новый frontend до фиксации основных API contracts.

### 3.

Добавить AI до появления deterministic Planner.

### 4.

Добавить retail parsers до появления generic Shopping Engine.

### 5.

Мигрировать на PostgreSQL в PR2 только потому, что production когда-то потребует PostgreSQL.

### 6.

Оставить две параллельные модели одного понятия надолго.

### 7.

Перенести косметические business invariants в food domain ради reuse кода.

### 8.

Создать 5000 рецептов до проверки planner на 30–50 хороших рецептах.

---

# 29. Главный принцип миграции

Каждый шаг должен отвечать на вопрос:

> **что из существующей системы является универсальной инженерной ценностью, а что является случайностью косметической предметной области?**

Переиспользуются:

- safety;
- architecture;
- transactions;
- versioning;
- imports;
- audit;
- validation;
- testing;
- human-readable UX patterns.

Не переиспользуются автоматически:

- названия сущностей;
- business workflow;
- косметическая математика;
- desktop information architecture.

---

# 30. Итоговая последовательность продукта

Исходная система:

```text
Recipe
→ Client Recipe
→ Order
→ Production
→ Stock Write-off
→ Purchase Suggestion
```

Целевая система:

```text
Household
        ↓
Members
        ↓
Preferences + Constraints
        ↓
Recipe Catalogue
        ↓
Nutrition Engine
        ↓
Meal Planner
        ↓
Weekly MealPlan
        ↓
Servings
        ↓
Pantry
        ↓
Shopping Engine
        ↓
Prep / Freezer Engine
        ↓
Daily Use
        ↓
Feedback
        ↓
Next Week
```

---

# 31. Первый практический этап после утверждения документа

## Историческая миграционная provenance

При первоначальном утверждении Migration Plan следующим техническим шагом был:

```text
PR0 — Frozen Fork
```

До начала PR1 требовалось сохранить:

```text
source repository
source commit
bootstrap tag
test baseline
build baseline
```

После PR0 был выполнен:

```text
PR1 — Identity Detox
```

Этот раздел фиксирует выполненную историческую последовательность и не является
текущей инструкцией. PR0, PR1 и PR2-A/B/C завершены. Текущий следующий
product milestone — `PR3 — FoodIngredient Catalogue`, но его implementation
начинается только после review и merge документационного sync PR2-DOCS.
Актуальный порядок всегда определяется
`docs/family-food/master-roadmap.md`.

---

# 32. Конечная архитектурная цель

FamilyFoodOS не должен выглядеть как переделанная «Мастерская косметолога».

Для пользователя это должен быть самостоятельный продукт.

Но внутри он должен наследовать наиболее сильные инженерные свойства исходной системы:

> **versioned, auditable, backend-owned, deterministic, recoverable и тестируемый core с максимально простым пользовательским интерфейсом.**
