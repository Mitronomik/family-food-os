# Русский язык во всех поверхностях FamilyFoodOS

**Status:** canonical cross-cutting product contract.
**DECISION:** PR6-ARCH-COMPOSITION, явно утверждено пользователем `2026-09-10`.

## Обязательный русский язык

FamilyFoodOS является русскоязычным продуктом. **Всё, что доступно обычному
пользователю или администратору продукта, обязано быть на русском языке.**
Это hard product invariant, включая административные review/audit screens.
Документ владеет языком product surface; engineering docs, Python classes,
SQL tables, repository methods и внутренние machine identifiers переводить не
требуется. Срок реализации определяется [Master Roadmap](master-roadmap.md).
Этот docs PR не переводит production seeds и не реализует UI/API/PDF/localization.

Обязательный scope:

- меню, навигация, заголовки, кнопки, формы, placeholders, подсказки, onboarding;
- названия разделов, статусы, ошибки, validation messages, empty states,
  notifications, confirmations и предупреждения;
- FoodIngredient и составные продукты, Recipe/RecipeTemplate/RecipeAssembly,
  названия блюд и Recipe Steps;
- cooking methods, ingredient roles, unit display, allergens, macro nutrients,
  micronutrients;
- Pantry, Shopping, Prep, PDF, печатные документы и consumer exports;
- administrator UI, review screens и audit statuses, видимые администратору.

## Display readiness и запрет English fallback

**Русского display text нет → объект не готов для consumer/admin surface.**
Отсутствие перевода является data/product publication blocker.
**English fallback запрещён:** нельзя показывать английское имя, описание,
ошибку или сырой enum, если русского представления нет. Русская оболочка страницы
не делает англоязычные ingredient names, steps или status labels допустимыми.

Каждая видимая сущность должна иметь валидное русское display representation до
publication: FoodIngredient, Composite FoodIngredient, Recipe, RecipeTemplate,
RecipeAssembly, NutrientDefinition, Allergen, CookingMethod, Status/Warning и Unit.
Административный экран не является исключением: Food Form Mismatch, Review
Required, Current Profile, Ingredient Mapping, Blocked, Unknown Fiber недопустимы
как product labels; им нужны русские отображаемые строки.

## Machine-code boundary и provenance

Backend/database могут сохранять стабильные `APPLE_PEELED`, `LEMON_JUICE`,
`FOOD_FORM_MISMATCH`, `APPROVED_EXACT` и другие identifiers. Они не попадают напрямую
в human-facing UI/PDF/errors или consumer exports вместо текста.

| Machine identifier | Обязательное человеческое представление — пример |
| --- | --- |
| `APPLE_PEELED` | Яблоко очищенное |
| `LEMON_JUICE` | Сок лимонный |
| `VITAMIN_B12` | Витамин B12 |
| `PROFILE_REPRESENTATIVENESS_REVIEW` | Требуется проверка соответствия профиля пищевой ценности |

Точные external provenance identifiers **не искажаются**: URL, FDC ID, DOI,
source IDs, machine codes в точной provenance reference, source hashes и official
release identifiers сохраняются. Это узкое исключение для точной ссылки/идентификатора,
не разрешение использовать raw code как label. Product/admin UI вокруг них русский.

Raw English source description может храниться как provenance/dev evidence.
Оно не является допустимой основной строкой admin UI. Если описание источника
необходимо показать администратору, должна существовать русская human-facing
representation; точный оригинал сохраняется в evidence без подмены provenance.

## Будущие автоматические gates

Каждый соответствующий frontend/admin/API/PDF implementation PR обязан
предусмотреть автоматическую проверку границы display text:

- raw enum и machine-code leakage;
- английские labels и errors;
- отсутствующие русские names;
- untranslated statuses/warnings, nutrients, ingredients, recipe titles/steps;
- любой English fallback.

API может передавать стабильный machine code как программное поле; human-facing
message/display остаётся русским и не строится fallback из этого кода. Эти gates
должны проверять consumer и admin outputs, PDF/print и exports, включая failure
и missing-translation paths. Механизм тестов/реестра переводов этим PR не создаётся.

Русский display — отдельная часть
[data readiness](nutrition-data-readiness.md#pr6-arch-composition-later-approved-decisions),
а [RU availability/familiarity](food-composition-and-assembly.md#ru-availability-и-familiarity-gates)
— отдельные продуктовые проверки. Перевод не доказывает доступность, привычность,
nutrition correctness или kitchen verification текущих 30 технических рецептов.
