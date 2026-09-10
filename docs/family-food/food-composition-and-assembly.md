# Состав продуктов и детерминированный конструктор рецептов

**Статус:** canonical food composition and assembly contract.
**DECISION:** PR6-ARCH-COMPOSITION, явно утверждено пользователем `2026-09-10`.
**База:** `47299ceb2c740f40f69f3b02359ce71c8be6b1c1` (PR #23).

Документ владеет atomic/composite FoodIngredient, composition modes и графом,
состояниями массы, transformation/yield/retention, взаимодействием с NutrientVector,
RecipeTemplate/RecipeAssembly, российской доступностью и привычностью блюда.
[Architecture](architecture.md) владеет границами контекстов и persistence,
[Nutrition Core](nutrition-core.md) — текущим v1 и направлением nutrient vector,
[русский языковой контракт](russian-language-contract.md) — всеми отображаемыми
текстами, [Master Roadmap](master-roadmap.md#5-canonical-master-sequence) — порядком.

Этот changeset устанавливает документационную архитектуру. Runtime, schema,
миграции, production seeds, значения нутриентов, FoodIngredient, RecipeVersion,
profiles, assessments и MeasureMassEvidence не меняются. Концептуальные имена
ниже не определяют SQL columns, persisted schema или окончательные имена сущностей.
Каждый последующий implementation PR требует отдельной bounded authorization.

## Принцип и food identity

> Пищевая ценность FamilyFoodOS рассчитывается снизу вверх от проверяемых пищевых
> сущностей, их фактических масс и проверяемых преобразований.

Цепочка: базовый продукт → составной продукт → полуфабрикат → смесь → блюдо →
приготовленное блюдо → порция. Название никогда не доказывает состав, энергию,
нутриенты, массу, edible fraction, плотность, вес штуки или cooking yield.
Критические факты принадлежат backend; core работает при `AI_ENABLED=false`.

**Option A — DECISION / APPROVED:** FoodIngredient остаётся единственной
канонической platform-owned food identity. Если две формы не могут правдиво
разделять один nutrition/composition contract, это разные FoodIngredient.
Лимон ≠ сок лимонный; апельсин ≠ сок апельсиновый; яблоко с кожурой ≠ очищенное;
сухие макароны ≠ приготовленные; шпинат ≠ молодой шпинат; свежая клубника ≠
замороженная без сахара; целый продукт ≠ очищенная съедобная часть.

`related_to` не означает `nutrition_equal`, `mass_equal`, `pantry_equal`,
`shopping_equal` или `substitutable`. Нарезка, бренд и упаковка сами по себе
не требуют нового FoodIngredient; split обосновывается изменением authoritative
food truth. Разная нарезка может требовать отдельной mass evidence при той же
nutrition identity. FoodIngredient ≠ RetailSKU. Обязательный промежуточный
`FoodProductType` и путь FoodIngredient → FoodProductType → Nutrition запрещены;
composite FoodIngredient не является переименованным FoodProductType.

## Atomic, composite и calculation authority

| Понятие | Значение и источник nutrition truth |
| --- | --- |
| `ATOMIC` | На выбранном уровне каталога внутреннее разложение не используется для production nutrition. Проверенный direct profile самого FoodIngredient. Это не химическая простота: примерами могут быть сырая морковь, яблоко, яйцо, мука, сахар, соль, масло, сырое мясо. |
| `COMPOSITE` | FoodIngredient состоит из других FoodIngredient, например соус, тесто, заправка, смесь, каша или полуфабрикат; возможна рекурсия. |
| `EXACT_COMPOSITION` | Количественный состав известен: каждый компонент имеет FoodIngredient, точную `input mass_g` и закреплённую версию profile/composition. Допускает bottom-up расчёт. |
| `DECLARED_ONLY_COMPOSITION` | Известен перечень компонентов без точных количеств; nutrition authority — проверенный профиль самого продукта, маркировка или официальная база. |

Например, количественно известный соус: помидоры 800 г, лук 120 г, масло 30 г,
сахар 10 г, соль 8 г, перец 2 г. Это иллюстрация состава, не production recipe,
не проверенные kitchen/yield/nutrition данные.

Для промышленных макарон декларация «мука, вода, яйцо, соль» не даёт граммов.
Из порядка ингредиентов **нельзя восстанавливать количества**: «мука первая →
70%» недопустимо. То же относится к промышленному соусу. Declared composition
может участвовать в идентичности, проверке аллергенов, объяснении, сопоставлении
и будущем retailer matching; без количеств она не вычисляет КБЖУ/микронутриенты.
Декларация не доказывает отсутствия неуказанного аллергена или следов.

Каждая версия продукта выбирает **один** calculation authority:

- `DIRECT_PROFILE` — профиль самого продукта;
- `DERIVED_EXACT_COMPOSITION` — расчёт из точного состава.

Наличие direct profile рядом с exact composition не разрешает double counting,
смешивание или усреднение. Нельзя частично взять готовое nutrition, частично
вычислить компоненты без отдельного утверждённого правила. Nutrient-level
provenance сохраняется даже внутри выбранного authority path; она сама по себе
не разрешает cross-source слияние.

## Единственный владелец composition truth

Recipe truth и reusable food identity не должны независимо хранить один и тот же
количественный граф как два источника истины.

- `RecipeVersion` владеет source-backed рецептурой: своими `RecipeIngredient`,
  точными количествами/входными массами и process graph для этого рецепта.
- `RecipeAssembly` владеет своим derived, воспроизводимым selected component/process
  graph, сформированным из проверенных template/rules.
- Food Catalogue владеет reusable `FoodIngredient` identity и самостоятельной
  composition truth только тогда, когда состав является свойством самого
  повторно используемого продукта, а не дубликатом конкретного RecipeVersion или
  RecipeAssembly.

Если приготовленный дома результат RecipeVersion/RecipeAssembly нужен как reusable
Composite FoodIngredient, его версия должна **ссылаться на producer/output truth**:
идентичность producer и его version, выходную food form, применённые transformation/
yield/retention и выбранный authoritative output. Она не копирует независимо тот
же список компонентов и количества. Изменение producer/version делает такую
output-binding новой/stale согласно будущему versioning contract; старый graph не
переписывается.

Покупной/промышленный composite является самостоятельным продуктом: при
`DECLARED_ONLY_COMPOSITION` он использует свой direct profile и сохранённую
декларацию без придуманных долей; при действительно известном независимом exact
составе может иметь собственный versioned composition. Это не создаёт второй
рецептурный источник истины для домашнего producer.

Графовые проверки должны учитывать producer/output bindings вместе с обычными
composition links: self-reference или цикл через RecipeVersion/RecipeAssembly
также fail closed. Точный persisted binding/schema относится к отдельно
авторизованному PR6-COMPOSITION-CORE; этот docs PR фиксирует ownership boundary.

## Recursive DAG и versioning

Exact composite может содержать atomic, другой exact composite или declared-only
продукт с самостоятельным authoritative direct profile. Например, блюдо содержит
макароны, мясо и соус; соус раскрывается на томаты, масло, лук, сахар, соль и перец.
Вычисление следует выбранному authority каждого узла и не считает повторно его
direct профиль и дочерние вклады. Если такой соус является результатом конкретного
RecipeVersion/RecipeAssembly, его component/process graph принадлежит producer и
повторно используемый FoodIngredient ссылается на этот output вместо копирования.

Composition graph обязан быть DAG. A → A и A → B → C → A запрещены.
Cycle detection проверяет достижимый граф закреплённых версий; при цикле —
**fail closed**, без authoritative частичного результата. Recursive calculation
детерминирован, Decimal-only, versioned, reproducible и cycle-safe. Отсутствующая
обязательная зависимость также не превращается в ноль или пропущенный компонент.

Изменение компонента, его массы, FoodIngredient reference, processing form,
authoritative profile, yield или transformation создаёт новую version truth.
Исторический расчёт сохраняет или однозначно ссылается на точные версии состава,
foods, nutrition profiles, массы, transformations, retention evidence и
calculation config. Указателя на «current» недостаточно для replay. История не
переписывается при смене текущей версии. Конкретный storage/invalidation/backfill
контракт определяется отдельно с сохранением B1 profile/assessment history.

## Mass-state contract

Одно поле `weight` не описывает всю цепочку.

| Концепт | Смысл |
| --- | --- |
| `gross_purchase_mass_g` | Приобретённая масса, возможно с несъедобными частями. |
| `recipe_input_mass_g` | Фактическая масса пищевой формы на входе конкретного процесса/рецепта; канонический calculation input concept. |
| `prepared_pre_cook_mass_g` | Масса после подготовки до cooking, если очистка, нарезка, отжим или иной этап существенны. |
| `cooked_output_mass_g` | Масса результата после приготовления. |
| `discard_mass_g` | Удалённые кости, кожура, семена, слитая жидкость и другие части. |
| `serving_mass_g` | Масса фактически выделенной порции. |

«В граммах до приготовления» означает входную форму процесса: сырое мясо, сухая
крупа, сухие макароны, а для рецепта из уже готового продукта — приготовленный
продукт как поставлен на вход. Нельзя искусственно возвращать его в биологически
сырой вид. Gross input с костями нельзя напрямую умножать на edible profile:
нужна доказанная связь между mass state, формой и базисом профиля.

Источник сохраняет «2 яйца», «стакан молока», «ложка масла», но nutrition требует
доказанного `recipe_input_mass_g`. `pcs → g` и `ml → g` возможны только через
food/form-specific reviewed mass evidence. Ни 60 г на яйцо, ни 1 мл = 1 г,
ни универсальный вес стакана не являются default authority. B1 exact-evidence
и row-binding contract остаётся действующим и должен быть совместим с развитием.

**Immutable rule:** raw/input/cooked массы не равны по умолчанию. 100 г сухих
макарон ≠ 100 г приготовленных. Массовая связь между состояниями — evidence,
не следствие одинакового названия, числа порций или nutrition density.

## Transformation и yield

Будущий versioned `Yield / MassTransformation` описывает:

```text
input mass + process inputs
→ transformation
→ output edible mass + discard / loss
```

Yield происходит из authoritative source, проверенного recipe source, kitchen
measurement, утверждённого dataset или иного проверенного evidence. Evidence
сохраняет применимые food forms, процесс, исходный/конечный mass state и версию.
Если yield неизвестен, `cooked_output_mass = unknown`; guessed value запрещено.

Вода поглощается, испаряется или сливается; жир добавляется, вытапливается или
остаётся в посуде; кожура, кости, семена удаляются. Evaporation, absorption,
drainage, rendered fat и discarded liquid входят в transformation model, когда
влияют на authoritative расчёт. Поглощённая вода увеличивает массу, не создавая
калорий; плотность нутриентов на 100 г меняется. Возможные потери нутриентов со
сливом моделируются отдельно. Нельзя дважды учитывать process inputs или потери
на соседних этапах. Количественные yield estimates этим PR не принимаются.

## NutrientVector и retention

Целевая модель: `NutrientDefinition → FoodNutritionProfileVersion → NutrientValue[]`
(или эквивалентная расширяемая representation). Каждый nutrient имеет стабильный
internal code, русское display name, canonical unit, source nutrient identifier,
Decimal value или unknown, provenance, version/release и estimation/uncertainty
state. Набор расширяется без новой database column на каждый nutrient: энергия,
белки, жиры, углеводы, пищевые волокна, минералы, витамины и другие необходимые
микронутриенты. Окончательный список не фиксируется здесь. Initial canonical
registry обязан определить отдельно authorized `PR6-NUTRIENT-VECTOR` по
авторитетным datasets и продуктовым требованиям.

**Unknown != zero** для каждого macro/micronutrient. Отсутствие данных не
становится нулём ради суммы. Нельзя склеить kcal производителя, белки USDA и
витамины другого generic food и назвать это единым measured profile. До отдельной
versioned cross-source policy действует fail closed / explicit uncertainty.

Для exact смеси до обработки вклад каждого nutrient равен значению совместимого
профиля × exact component input mass / profile mass basis; input total — сумма
вкладов в Decimal arithmetic. Нельзя складывать несовместимые nutrient definitions
или units без утверждённой нормализации. Неизвестный обязательный вклад сохраняет
неизвестность соответствующего authoritative total, а не частичную «полную» сумму.

**Yield описывает массу; retention — сохранение конкретного nutrient.** Будущий
versioned `FoodTransformation + NutrientRetentionEvidence` допускает разные
retention для витамина C, витаминов B, минералов, белка, жира и других нутриентов.
Универсальный `cooking_loss_percent` для всех nutrients запрещён.

Если input nutrition известно, а влияние процесса на nutrient неизвестно,
сохраняется известный input total; cooked total не объявляется exact. Uncertainty
должна быть явной: скрытый `retention = 100%` запрещён. Нельзя вычислить достоверную
cooked density/Serving из неизвестного output/yield или retention. Известные
диагностические input values не теряются; authoritative cooked результат
fail-closed на затронутой части.

```text
FoodIngredient → composition → input mass_g → input NutrientVector
→ transformation → yield → retention → prepared NutrientVector
→ cooked_output_mass_g → Serving → member/day/week
```

Ни одна стадия не угадывает предыдущую. Serving и member/day/week принадлежат
PR7; этот pipeline не заявляет, что они уже существуют.

## RU availability и familiarity gates

Россия — целевой рынок; Санкт-Петербург — первоначальная область проверки.
[Существующая curation policy](recipe-localization-and-substitution.md#5-ingredient-market-compatibility-classification)
сохраняет классификации и количественный порог `RU_MASS_MARKET` (3 из 5 сетей).
Panel: Пятёрочка, Перекрёсток, Лента, О'КЕЙ, Магнит; ВкусВилл — secondary evidence.
Это curation gate, не Retail runtime. Evidence имеет дату/регион и обновляется:
ассортимент изменяется; позже Retail Program владеет live availability snapshots.
Существующие исключения для водопроводной воды и category-level commodity evidence
сохраняются; они не разрешают домысливать доступность других продуктов.

RU availability применяется к **покупаемым terminal inputs** выбранного
RecipeVersion/RecipeAssembly. Каждый обязательный продукт, который household должен
купить для выполнения default recipe, имеет актуальное доказательство обычной
российской розничной доступности. Если reusable composite готовится дома по
проверенному producer/output path, он сам не обязан продаваться в магазине: gate
рекурсивно проверяет его purchase-required terminal inputs. Если тот же composite
выбран как готовый покупной продукт, availability evidence требуется уже для него.
Выбор «сделать дома» и «купить готовым» является явным плановым решением, а не
автоматической взаимозаменяемостью или Pantry/Shopping conversion.

`RU_MASS_MARKET` предпочтителен. `RU_AVAILABLE` допустим в каталоге, но стандартная
неделя не может зависеть от редкого purchase-required input без подтверждённого
обычного substitution path. `SPECIALTY_OR_UNCLEAR` запрещён как обязательный
покупаемый terminal input default automatic recipe. Производный домашний composite
не проходит retail gate фиктивной записью о собственной продаже; его готовность
доказывается producer/output и доступностью terminal inputs.

До consumer Planner нужен базовый российский каталог: обычные свежие продукты,
мясо, птица, рыба, яйца, молочные продукты, крупы, макароны, мука, хлеб, масла,
овощи, фрукты, специи, простые соусы и распространённые составные полуфабрикаты.
Каждая запись имеет правильные identity/form/composition mode, nutrition
provenance, Russian display и market evidence там, где продукт является покупаемым
terminal input; домашний derived output вместо фиктивной retail-доступности имеет
проверяемый producer/output binding. Этот PR записей не добавляет.

Доступности недостаточно. **`RU_RECIPE_FAMILIAR` — hard default-recipe gate**
(точный internal code можно уточнить в data PR). Review проверяет обычные продукты,
бытовую технику, понятные способы обработки, разумное число действий, отсутствие
обязательной specialty-техники и экзотического ингредиента, семейную подачу,
понятный формат и возможность приготовить обычной семьёй. Произвольных числовых
порогов времени/числа компонентов здесь нет. International dishes допустимы при
curated familiarity/kitchen review; российский контекст не ограничен национальной
русской кухней.

Текущие **30 FNS RecipeVersion — technical regression/architecture corpus** для
provenance, regression, Nutrition testing и migration/history, а не финальный
consumer recipe catalogue России. Consumer exposure требует отдельной русской
product/data readiness; прежний market audit не доказывает все новые gates.

## RecipeTemplate и deterministic assembly

Recipe Assembly Engine работает при `AI_ENABLED=false`. LLM не является свободным
генератором production recipes. Входы: verified FoodIngredient catalogue,
composition, nutrition, versioned RecipeTemplate, allowed component rules,
exact quantity rules, transformations/yield и RU availability/familiarity.
Выход — validated reproducible RecipeAssembly.

Versioned template/rule truth концептуально задаёт тип блюда, обязательные роли,
допустимые atomic/composite foods, gram ranges/exact quantity equations, способ
и последовательность приготовления, transformation contracts, culinary
compatibility, optional components, substitutions, kitchen verification и RU
familiarity status. Диапазон должен разрешиться проверенным правилом в exact grams;
произвольный midpoint не получает authority.

Пример структуры «Макароны с мясом и томатным соусом»: сухая крахмальная основа,
разрешённые проверенные варианты говядины/курицы/индейки, verified tomato-based
composition, allowed fat quantity range и allowed vegetable set. Это пример
структуры, не разрешение «любой продукт + любой продукт» и не kitchen verification.

Результат содержит selected FoodIngredient, exact `recipe_input_mass_g`,
composition version, nutrition authority, transformation rule и yield evidence.
«Штука», «стакан», «по вкусу» без mass authority не завершают nutrition calculation.
Atomic и composite участвуют как food components; Nutrition раскрывает exact
соус только по его выбранному composition authority. Optional components
становятся частью выбранного варианта явно; скрытого включения в сумму нет.

### Assembly trace

Каждый результат хранит или однозначно ссылается на template version, selected
foods, composition versions, exact input grams, applied rules, rejected candidates,
substitution rules, nutrition config, transformation/yield/retention versions,
RU availability evidence version, language/display version где релевантно и
validation result. Это обеспечивает воспроизводимость без нового LLM-вызова.

### Validation и kitchen verification

`ASSEMBLY_VALIDATED` означает валидные структуру, граммы, nutrition inputs,
cooking rules, RU availability и ограничения. Это не означает, что данную
комбинацию приготовил человек. `KITCHEN_VERIFIED` — отдельный evidence-backed
статус (или эквивалент); LLM не может его присвоить. Default consumer constructor
опирается на kitchen-verified templates, kitchen-validated rules/variants и
curated substitutions, а также familiarity и Russian display gates.

### Границы Recipe, Planner, Shopping и Pantry

Source-backed production RecipeVersion остаётся immutable authoritative recipe
truth и владеет своим recipe-specific component/process graph. Assembly —
derived/reproducible state и владеет своим selected graph; оно не переписывает
RecipeVersion и не создаёт тысячи near-duplicate versions. Reusable Composite
FoodIngredient, произведённый таким процессом, ссылается на producer/output binding
и не дублирует тот же graph. Публикация assembly как отдельного canonical recipe —
отдельная trusted publication operation.

Household constraints → Recipe Assembly / verified Recipe Catalogue → валидный
candidate pool → Planner → MealPlan. Planner выбирает валидные candidates и не
владеет culinary truth. PR7 учитывает immutable RecipeVersion **или** validated
RecipeAssembly как selection origin, переиспользует Nutrition и не дублирует её.

Assembly определяет конечный набор FoodIngredient. Shopping агрегирует уже
утверждённый состав и не изобретает substitutions. Для make-at-home composite
будущий Shopping использует purchase-required terminal inputs выбранного producer;
для явно выбранного покупного composite — сам покупаемый FoodIngredient. Это не
разрешает автоматически заменять один путь другим. Pantry не превращает лимон
в сок без отдельной transformation/substitution logic. Shopping generation
по-прежнему read-only к Pantry; новые правила состава не разрешают автоматическое
списание, резервирование или смешение raw/cooked inventory.

## Совместимость, supersession и открытые решения

Nutrition v1 был корректным bounded engine для принятого тогда data contract.
`FAMILY_FOOD_NUTRITION_V1` и его пять полей остаются текущим runtime; tests/history
PR #18 действительны. Новое пользовательское решение расширяет versioned target.
B2-B1 (PR #23) сохраняется как полезное research evidence: split Option A теперь
утверждён, но конкретные profile/source candidates должны быть повторно
классифицированы и reviewed для нового composition/form/nutrient контракта.

**Old PR6-DATA-B2-B2: SUPERSEDED / PENDING REDESIGN.** Прежний план
«form/profile corrections + explicit estimate policy» больше не является
допустимым следующим implementation PR. Сначала нужны NutrientVector, composition,
mass states, transformation/yield, RU catalogue и Russian display requirements.
Исследованные LEMON_JUICE, APPLE_PEELED, SPINACH_BABY, CAULIFLOWER_FROZEN и другие
candidates не теряются, но прежний promotion plan напрямую не исполняется.

Все **43 estimate candidates остаются non-executable** до отдельно утверждённой
estimate/uncertainty policy. OPEN: initial nutrient registry, конкретные будущие
schema/migration/backfill contracts, exact source/profile promotion, source-form
ambiguities, отсутствующее mass/yield/retention evidence и cross-source policy.
Ничто из этого не решается вымышленными значениями или данным docs PR.

Новый порядок и отдельные authorizations определяет
[Master Roadmap](master-roadmap.md#5-canonical-master-sequence).
PR6 — NOT COMPLETE; PR6-NUTRIENT-VECTOR — NOT STARTED / requires separate
authorization after merge; PR7+ — UNAUTHORIZED.

## Архитектурные риски

| Риск | Обязательное ограничение |
| --- | --- |
| Catalogue explosion | Split только при изменении authoritative food truth, не из-за нарезки/бренда/упаковки как таковых. |
| Composition double counting | Один calculation authority path на version; producer-owned recipe/assembly graph не дублируется в reusable FoodIngredient. |
| Hidden yield assumptions | Versioned evidence; unknown остаётся unknown. |
| Micronutrient false precision | Nutrient-level provenance, unknown != zero, явная retention uncertainty. |
| Russian catalogue drift | Timestamped curation evidence; позже Retail live snapshots. |
| Recipe generator becomes LLM | Детерминированные templates/rules; optional AI отдельно; kitchen/culinary validation не выводится из расчёта. |
| Localization leakage | Обязательный русский display layer, запрет English fallback, будущие automated leakage gates. |
