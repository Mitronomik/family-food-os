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
→ Portions
→ Pantry
→ Shopping
→ Prep
→ PDF
```

Основной цикл MVP должен работать **без LLM и без retail parsers**.

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
Tenant isolation
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
PR0   Frozen Fork
PR1   Identity Detox
PR2   Food Domain Foundation (PR2-A contract → first schema implementation)
PR3   FoodIngredient Catalogue Core
PR4   Food Recipe Core
PR5   Pantry Core
PR6   Nutrition Engine
PR7   Household MealPlan Domain
PR8   Planner v0
PR9   Shopping Engine
PR10  Prep & Freezer Engine

----- MVP CORE GATE -----

PR11  New Consumer PWA Shell
PR12  Household Onboarding
PR13  Weekly UX
PR14  PDF / Printable Week

----- CLOSED MVP GATE -----

----- SHARED MULTI-FAMILY DEPLOYMENT GATE (triggered before shared families) -----

PostgreSQL + Auth + Tenant isolation + hosted deployment

PR15  Data Ingestion Platform
PR16  Retail Foundation
PR17  Feedback & Personalization
PR18  Optional AI Gateway

----- PAID BETA GATE -----

PR19  Paid Beta Commercial Foundation / Billing / Hardening
```

Shared-deployment work is trigger-based rather than tied to the late PR19
number. Its exact implementation PR must be scoped and reviewed before the
first shared multi-family deployment; it may be scheduled before PR15–PR18 if
shared validation starts earlier.

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

# PR2 — Food Domain Foundation

PR2-A фиксирует documentation-only architecture/persistence contract. Первый
food schema implementation после него использует SQLite, synchronous SQLAlchemy
2.x Core для runtime persistence и существующий custom migration runner как
единственный SQLite schema authority. PR2-A сам не добавляет dependency, schema
или migration.

## Goal

Добавить фундамент новой предметной области рядом со старой.

## Новые сущности

```text
Household
HouseholdMember
FoodPreference
ExcludedIngredient
HouseholdSettings
```

## Household

Минимально:

```text
id
name
city
timezone
weekly_budget
cooking_profile
created_at
updated_at
```

## HouseholdMember

```text
id
household_id
name
birth_date / age
sex optional
height optional
weight optional
activity_level
goal
active
created_at
updated_at
```

## Scope

Добавить:

- domain models;
- schemas;
- repositories;
- services;
- migrations;
- API;
- tests.

## API

Предварительно:

```text
GET    /api/households
POST   /api/households

GET    /api/households/{id}
PATCH  /api/households/{id}

GET    /api/households/{id}/members
POST   /api/households/{id}/members
PATCH  /api/household-members/{id}
```

## Non-goals

Не:

- удалять Client;
- строить меню;
- рассчитывать калории;
- делать frontend onboarding;
- добавлять auth.

## Acceptance criteria

Можно программно:

```text
create household
→ add 3 members
→ update household
→ update member
→ retrieve complete household
```

---

# PR3 — FoodIngredient Catalogue Core

## Goal

Создать системный каталог пищевых ингредиентов.

## Новая сущность

```text
FoodIngredient
```

`CanonicalIngredient` в более ранних Project Sources означает тот же
канонический platform food concept. В repository architecture используется имя
`FoodIngredient`; это не две разные сущности.

## Поля

```text
id
canonical_code
name
category
default_unit

density optional
edible_fraction

kcal
protein
fat
carbohydrates
fiber

allergen_flags
storage_profile

is_active
created_at
updated_at
```

Дополнительно:

```text
IngredientAlias
```

## Что переиспользовать

Из старого Ingredient:

- ID conventions;
- unit validation;
- Decimal patterns;
- archive/deactivate behavior;
- repository/service patterns;
- catalog category/tag ideas.

## Что удалить из новой модели

Не переносить:

```text
inci_name
supplier_hint
cosmetic usage notes
cosmetic categories
```

## Bootstrap

Добавить fixture:

```text
data/seed/canonical-ingredients.csv
```

Для первого этапа:

**80–120 ингредиентов.**

## Non-goals

- retailer SKU;
- parsing;
- цены магазинов;
- полноценный nutrition source catalogue.

## Acceptance criteria

Seed-команда автоматически создаёт каталог.

Повторный импорт не создаёт duplicates.

Поиск:

```text
"греч"
```

возвращает canonical ingredient без ручного создания пользователем.

---

# PR4 — Food Recipe Core

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
canonical_ingredient_id
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

# PR5 — Pantry Core

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

# PR6 — Nutrition Engine

## Goal

Создать полностью deterministic расчётный слой питания.

## Новый module

```text
backend/app/services/nutrition/
```

или согласованная аналогичная структура.

## Ответственность

- nutrition ingredient;
- nutrition recipe;
- nutrition serving;
- nutrition day;
- nutrition week;
- member target profile.

## Основное правило

LLM запрещён внутри Nutrition Engine.

## Вход

```text
HouseholdMember
Recipe
Serving
```

## Выход

```text
kcal
protein
fat
carbs
fiber
warnings
```

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

# PR7 — MealPlan Domain

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

# MVP CORE GATE A

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
- 30 recipes;
- 80+ ingredients;
- deterministic planner tests.

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

# PR10 — Prep & Freezer Engine

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

# MVP CORE GATE B

На этом этапе backend должен поддерживать полный vertical slice:

```text
Family
→ Week
→ Portions
→ Shopping
→ Pantry
→ Prep
```

Без frontend и без AI.

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

# PR12 — Household Onboarding

## Goal

Получить первую неделю максимум за несколько минут.

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
empty account
→ household
→ family members
→ constraints
→ first MealPlan
```

без обращения к admin UI.

---

# PR13 — Weekly Consumer UX

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

# PR14 — Weekly PDF

## Goal

Сделать FamilyFoodOS пригодным для использования без постоянного открытого приложения.

## PDF

Минимум:

### Page 1

Меню недели.

### Page 2

Покупки.

### Page 3

Заготовки.

### Далее

Краткие рецепты.

## Переиспользовать

- file creation safety;
- artifact handling;
- PDF generation pattern;
- non-overwriting filenames.

## Acceptance criteria

PDF:

- A4;
- русский текст;
- читаемый;
- печатаемый;
- соответствует текущему MealPlan.

---

# CLOSED MVP GATE

После PR14 можно начинать тестирование на:

**10–30 семьях.**

Local или isolated single-household testing не требует Auth/PostgreSQL. До того
как независимые семьи используют один hosted deployment, обязательно пройти
shared multi-family deployment gate:

```text
PostgreSQL
+ Auth
+ Tenant isolation
+ hosted deployment
```

Обязательный сценарий:

```text
onboarding
→ generate week
→ modify week
→ shopping
→ prep
→ use week
→ feedback
→ next week
```

---

# PR15 — Data Ingestion Platform

## Goal

Убрать ручное администрирование системной базы.

## Новый bounded context

```text
ingestion/
```

## Основные pipelines

```text
IngredientBootstrapJob
RecipeImportJob
NutritionImportJob
AliasResolutionJob
ValidationJob
```

## Reuse

Сохранить проверенную идею:

```text
Source
→ Draft
→ validation
→ preview
→ apply
```

Но для trusted automatic sources допускается configurable auto-approval.

## Новые сущности

```text
IngestionJob
RawSourceRecord
ReviewQueueItem
```

## Acceptance criteria

Можно массово загрузить:

- 300 ingredients;
- 100 recipes;

без ручного создания каждой сущности.

---

# PR16 — Retail Foundation

## Goal

Подготовить систему к актуальным магазинам и ценам.

## Новые сущности

```text
Retailer
RetailStore
RetailSKU
PriceSnapshot
RetailMapping
```

## Connector interface

```text
RetailConnector

search()
fetch_product()
fetch_price()
fetch_availability()
normalize()
```

## Matching

```text
RetailSKU
→ FoodIngredient
```

## Confidence

Поддержать:

```text
AUTO_APPROVE
REVIEW
REJECT
```

## Первый connector

Только одна сеть.

Не подключать три сети в одном PR.

## Non-goals

- полный ассортимент сети;
- оформление доставки;
- обход технических защит.

## Acceptance criteria

Для whitelist ingredients система получает актуальные candidate SKU и цены автоматически.

---

# PR17 — Feedback & Personalization

## Goal

Сделать следующую неделю лучше предыдущей без LLM.

## Сигналы

```text
LIKED
DISLIKED
SKIPPED
REPLACED
LEFTOVER
REPEAT_REQUESTED
```

## Новые сущности

```text
MealFeedback
RecipePreferenceScore
HouseholdIngredientPreference
```

## Planner integration

История влияет на score следующего MealPlan.

## Acceptance criteria

Если пользователь 3 раза отклонил рецепт, planner снижает вероятность его повторного предложения.

---

# PR18 — Optional AI Gateway

## Goal

Добавить natural-language interaction поверх deterministic system.

## Архитектура

```text
AI Gateway
        ↓
LLMProvider
        ├── OpenAIProvider
        ├── GigaChatProvider
        └── future/local
```

## Разрешённые задачи

### Natural-language preference

> На следующей неделе меньше курицы.

↓

```text
structured constraint
```

### Schedule change

> В среду муж не ужинает.

↓

structured change.

### Pantry input

> Осталось полпачки гречки и шесть яиц.

### Replacement request

> Замени рыбу чем-нибудь дешёвым.

## Hard rule

AI не является источником истины для:

- kcal;
- nutrients;
- allergens;
- quantities;
- prices;
- availability;
- shopping;
- storage safety.

Все AI suggestions проходят deterministic validation.

## Feature flag

```text
AI_ENABLED=false
```

не должен ломать ни один core workflow.

---

# PAID BETA GATE

Перед следующим этапом необходимо подтвердить:

- пользователи возвращаются на вторую неделю;
- generated menu используется;
- shopping list реально используется;
- onboarding completion приемлемый;
- planner имеет достаточный acceptance rate.

Если продукт уже обслуживает несколько независимых семей в одном deployment,
shared multi-family deployment gate должен быть закрыт до этого момента, а не
откладываться до Paid Beta.

---

# PR19 — Paid Beta Commercial Foundation

## Goal

Добавить commercial capabilities после доказательства core value и закрытого
shared-deployment safety gate.

## Shared deployment prerequisite

PostgreSQL, Auth, tenant isolation и hosted deployment не являются scope PR19,
если они уже реализованы более ранним trigger-based PR. Если gate ещё не
закрыт, Paid Beta не начинается.

## Billing

Добавить `Subscription` и подготовить tiers:

```text
Core
Smart
Plus
```

## Feature flags

Пример:

```text
AI_ACCESS
RETAIL_PRICES
ADVANCED_HISTORY
```

## Production infrastructure

Добавить:

- container deployment;
- secrets;
- DB backups;
- error monitoring;
- structured logs;
- health checks;
- migration procedure;
- restore procedure.

## Acceptance criteria

Shared-deployment isolation tests уже проходят как prerequisite.

Billing не ослабляет household authorization и tenant boundary.

Production deployment восстанавливается из documented backup.

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
- tenant isolation;
- production deployment;
- backups;
- monitoring;

Дополнительно для Paid Beta:

- billing;
- минимум один RetailConnector;
- optional AI;
- feedback history;
- admin ingestion UI;
- legal/privacy documents.

---

# 26. Оценка этапов

Ориентировочно при плотной agent-assisted разработке:

| Этап | Срок |
|---|---:|
| PR0–PR1 | 1–2 дня |
| PR2–PR5 | 6–10 дней |
| PR6–PR8 | 5–8 дней |
| PR9–PR10 | 3–5 дней |
| PR11–PR14 | 6–10 дней |
| **Closed MVP** | **примерно 3–5 недель** |
| PR15–PR18 | ещё 2–3 недели |
| PR19 + hardening | ещё 2–3 недели |
| **Paid beta** | **примерно 7–10 недель от старта** |

Сроки предполагают:

- использование Codex/Claude Code;
- маленькие PR;
- быстрое review;
- отсутствие масштабного scope creep.

---

# 27. Возможная параллельная работа агентов

После PR3 можно частично параллелить.

### Agent A — Domain

```text
Recipe
Nutrition
Planner
```

### Agent B — Data

```text
ingredients
seed
recipes
ingestion preparation
```

### Agent C — Frontend

после стабилизации API:

```text
PWA shell
onboarding
weekly UX
```

### Agent D — QA / Reviewer

```text
tests
architecture compliance
regression
migration safety
```

Но один агент/оркестратор должен владеть:

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

После утверждения Migration Plan следующий технический шаг:

```text
PR0 — Frozen Fork
```

До начала PR1 необходимо сохранить:

```text
source repository
source commit
bootstrap tag
test baseline
build baseline
```

После PR0 выполняется:

```text
PR1 — Identity Detox
```

и только после него начинается изменение доменной модели.

---

# 32. Конечная архитектурная цель

FamilyFoodOS не должен выглядеть как переделанная «Мастерская косметолога».

Для пользователя это должен быть самостоятельный продукт.

Но внутри он должен наследовать наиболее сильные инженерные свойства исходной системы:

> **versioned, auditable, backend-owned, deterministic, recoverable и тестируемый core с максимально простым пользовательским интерфейсом.**
