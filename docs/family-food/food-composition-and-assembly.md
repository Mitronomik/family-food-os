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

Исходный PR6-ARCH-COMPOSITION установил документационную архитектуру. Runtime, schema,
миграции, production seeds, значения нутриентов, FoodIngredient, RecipeVersion,
profiles, assessments и MeasureMassEvidence в том PR не менялись. Концептуальные имена
исходного архитектурного решения не определяли SQL columns, persisted schema
или окончательные имена сущностей. Concrete runtime contract ниже фиксирует
результат отдельно разрешённой реализации Composition Core.
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
также fail closed. Ownership boundary остаётся обязательной. В разрешённом PR6-COMPOSITION-CORE
реализуется самостоятельный catalogue composition; конкретный producer/output
binding к RecipeVersion/RecipeAssembly отложен явным заданием пользователя.
Этот PR не создаёт и не копирует producer-owned graph.

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
registry определён в bounded `PR6-NUTRIENT-VECTOR-A` по авторитетным
datasets и продуктовым требованиям; см. [реестр и аудит](../../data/curation/pr6-nutrient-vector-a/README.md).
VECTOR-B с normalized values/runtime принят и merged в PR #26.

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
estimate/uncertainty policy. Реестр и provenance audit установлены VECTOR-A; OPEN:
конкретные будущие
schema/migration/backfill contracts, exact source/profile promotion, source-form
ambiguities, отсутствующее mass/yield/retention evidence и cross-source policy.
Ничто из этого не решается вымышленными значениями или данным docs PR.

Новый порядок и отдельные authorizations определяет
[Master Roadmap](master-roadmap.md#5-canonical-master-sequence).
PR6 — NOT COMPLETE. VECTOR-A и VECTOR-B merged в PR #25 / #26.
COMPOSITION-CORE отдельно авторизован 2026-09-12; реализация описана ниже.
PR7+ — UNAUTHORIZED. Действующий container для atomic values —
существующий FoodNutritionProfile с сохранённой identity и историей, без второго
current-profile selector. Отсутствие value row означает unknown только в полном
атомарно опубликованном snapshot. Числовой `0` означает source-reported zero;
для authoritative exact zero при normalized import нужны достаточные source
provenance и approved import policy. Все 64 исследованных нуля пока unresolved;
их exact backfill заблокирован. Production v1 values остаются без изменений.

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


## PR6-COMPOSITION-CORE — concrete runtime contract

**DECISION — 2026-09-12, explicitly approved after preflight:** exact composition
is **mass-authoritative**. Each node persists an exact positive finite Decimal
`input_mass_g` and the exact child composition version ID. Total input mass is
the deterministic exact sum of node masses. There are no persisted normalized
fractions and no `sum(fractions) == 1` invariant. Ratios such as `1/3` are never
approximated into authoritative component fractions. This resolves the task's
reference to an undefined normalization invariant; it supersedes the unapproved
fraction proposal recorded during preflight.

`FoodCompositionVersion` belongs to FoodIngredient, with immutable UUID and
positive version number unique within that food. `ATOMIC` pins exactly one
existing FoodNutritionProfile/sealed vector; `COMPOSITE` pins ordered node IDs,
child version IDs, input masses and their explicit child-output mass states.
ATOMIC is the direct-profile calculation path; a declared-only product may use
its own authoritative direct profile, but no declaration parsing or inferred
quantitative graph is introduced. No second food identity or nutrient registry
is created. Steps pin ordered transformation version IDs.

`RAW`, `INPUT`, `DRAINED`, `COOKED`, `YIELDED`, `GROSS_PURCHASE`,
`PREPARED_PRE_COOK`, `DISCARD` and `SERVING` are explicit internal mass-state
codes. The latter codes represent mass concepts only; they do not implement
Serving or other future contexts. Each node's state must match its child's
calculated output state. Composite `input_state` describes the combined input
basis; it does not relabel individual child foods. Consecutive transformation
input/output states and yield/retention evidence states must agree. There is
no global transition matrix and no automatic raw/edible/cooked conversion.

A transformation retains immutable ID/version, process type, input/output
states and source/version/evidence/review references. Optional YieldModel and
NutrientRetentionProfile references are pinned. Yield must be finite positive
Decimal. Sparse retention factors reference the existing canonical nutrient
codes; they are finite nonnegative Decimal with no arbitrary upper bound.
Each factor also retains its own evidence/review reference. Required absence
is represented explicitly rather than granting an implicit factor of one.
Every applied transformation requires yield to calculate output mass, including
an unchanged-mass process (reviewed factor `1`). Every requested nutrient needs
its own retention factor to declare the transformed amount known.

`CompositionCalculator.calculate(root_version_id, nutrient_codes=...)` is the
single driver-independent entry point for future consumers. The nonempty,
explicit requested nutrient set defines result completeness, without expanding
the sparse registry into a dense matrix. It reads full sealed atomic vectors,
checks canonical definition/unit/registry compatibility, aggregates child nutrient
amount × node input mass / child output mass, then separately multiplies nutrient
amounts by retention and output mass by yield. It never persists these derived
ratios or calculated vectors as new base nutrient authority.

The versioned calculation configuration is `FOOD_COMPOSITION_V1`. Finite source
mass sums and products use sufficient private Decimal precision to remain exact.
Division uses a private precision of 80 with `ROUND_HALF_UP`, independent of
caller precision, rounding, flags and traps. Following the existing Nutrition
output convention, nutrient amounts/concentrations round once to six places at
the root result boundary. Recursive child results are not quantized. Component
masses and calculated output masses are not quantized; intermediate amount and
mass evidence is retained. Six-place result representation does not certify
measurement accuracy or promote estimated/unreviewed source observations.

Result semantics for the explicitly requested set:

- `COMPLETE`: all requested nutrient amounts and output concentrations available.
- `PARTIAL`: at least one requested amount/concentration available and at least
  one unavailable; known values do not include unknown child contributions.
- `INCOMPLETE`: no requested amount/concentration available, including unknown
  output mass. Known input or retained amounts remain diagnostic evidence.

Each result nutrient carries amount and concentration or `None`, plus explicit
`AVAILABLE`/`UNKNOWN` availability. Missing input contributions and retention
never become zero; a reviewed zero retention remains an explicit numeric zero.
Missing yield leaves output mass/concentration unknown. Structural corruption,
missing pinned dependencies, incompatible states/definitions, cycles and unavailable
or corrupt atomic vectors fail closed with exceptions rather than an empty
apparently authoritative vector. Stable issue codes accompany sparse unknowns.

Replay contains the calculation version, request set, all composition snapshots,
node/step identities and masses, atomic profile IDs and full vector provenance,
registry identity, transformations, yield/retention snapshots, ordered stages and
issues. Mutable `is_current` profile metadata is excluded. No timestamp or random
identity is created during calculation. Iterative DAG traversal is cycle-safe
without a Python recursion-depth limit; shared children remain valid.

Migration `0029_food_composition_core` creates seven empty tables: composition
versions/nodes/steps, transformations, yield models, retention profiles/values.
Repositories use synchronous SQLAlchemy Core on the project UoW connection and
never commit. Nodes/steps/factors are inserted before their owning snapshot;
deferred FKs prevent committing an unpublished set. Owning snapshots check row
counts; readers also verify deterministic SHA-256 over complete domain snapshots.
SQL triggers forbid UPDATE/DELETE/REPLACE and inserts after publication, including
replacement via alternate unique keys. SQL recursive cycle guards complement
build-time full-DAG validation and runtime defense. The nutrient vector seal FK
and profile-owner validation bind atomic food/profile identity.

No production composition/yield/retention data is seeded or backfilled. Migration
uses the existing transactional runner, registered lineage/table inventories and
native backup/restore contract. Injected failure rolls back schema/data/marker;
rerun is deterministic. Successful deployment rollback uses a pre-upgrade backup,
not deletion of historical composition truth. Nutrition v1, B1 bindings and
VECTOR-B registry/values/seals remain unchanged. No public API/UI or Recipe
Assembly implementation is added. PR6 remains NOT COMPLETE.


## PR6-RU-FOOD-DATA — bounded ATOMIC reconciliation

The separately authorized RU operation supplies a reviewed repository food-data
readiness package, using existing `FoodIngredient.canonical_name` as Russian
primary display. No availability database context or second display column exists.
Its explicit seed appends ATOMIC versions for approved direct-profile foods and
pins the exact sealed profile ID resolved from source name/food ID/release.
The reviewed natural reference is food code + version 1 + operation + exact
profile provenance; local UUIDs remain database identities. Existing compositions,
profiles, vectors and RecipeVersions are never rewritten.

[The versioned package](../../data/curation/pr6-ru-food-data/README.md) owns the
exact promotion/defer decisions, market references, sparse unknown inventory,
source hashes and reproducible audit. RU_READY is food-data readiness with explicit
unknowns; default eligibility additionally requires the unchanged market gate.
Requested nutrient completeness and later recipe/assembly/kitchen gates still apply.
No producer/output binding, composite, transformation, yield or retention data is
introduced. Migration head remains 0029. PR6 remains NOT COMPLETE.

## PR6-DATA-B2-B2-REDESIGNED — direct-profile replacement facts

The [bounded re-curation](../../data/curation/pr6-data-b2-b2-redesigned/README.md)
appends three exact SR replacement profiles/vectors and corresponding ATOMIC
compositions. Actual main has no existing composition for these three candidate
foods: PR28 classified them NOT_READY. Their first publication is therefore v1;
no historical composition is synthesized from an unresolved old profile.
When an existing v1 pins an old profile, replacement must append v2 and retain
v1 replay. This conditional case is exercised with explicitly synthetic fixtures;
all 60 actual pre-existing compositions replay unchanged in the production audit.

Composition replay continues to use exact pinned profile IDs and sealed vectors,
never mutable current-profile selection. The only historical profile mutation is
the catalogue's existing `is_current` retirement; old sealed values/provenance
and old profile facts remain unchanged. New vectors use only positive compatible
values under the accepted registry/zero policy. Recipe food-form corrections
reuse the two PR28 compositions; no composite, transformation, yield or retention
truth is introduced. The separate data upgrade uses one existing project UoW,
requires a populated 0029 catalogue and leaves schema/lineage unchanged.


## RECIPE-ASSEMBLY-A — evidence preflight blocked

2026-09-12: following reviewed PR30 merge, the user authorized exactly three
production RecipeTemplate families. The [preflight package](../../data/curation/recipe-assembly-a/README.md)
records a screen of all 30 accepted current RecipeVersions and three deferred
candidate families. Existing row mass/form authority cannot be carried forward
as three publishable templates; reviewed kitchen/variant scope, curated
substitutions and default RU eligibility are also unestablished.

No RecipeTemplate runtime, persisted schema, production seed or RecipeAssembly
was introduced. Migration remains 0029; 0030 is still required if catalogue
implementation resumes. The hard three-family gate caused the stop, not a
schema-without-migration exception. Positive USDA collection-level testing evidence
is retained with its limited scope; it does not verify arbitrary FNS/WIC recipes
or generalized variants. No source, quantity, composition, estimate, language,
market or kitchen gate is weakened. Assembly A is BLOCKED, not COMPLETE;
Assembly B and PR7+ remain NOT STARTED and require separate authorization.

### RECIPE-ASSEMBLY-A-R1 — bounded donor recovery

2026-09-12: after the explicitly authorized merge of checkpoint PR31, the
[separate R1 evidence package](../../data/curation/recipe-assembly-a-r1/README.md)
screens 23 institutional donors and deep-reviews nine. R1 is BLOCKED: no
final three satisfy all gates. AFRS plain oatmeal supplies exact source input
weights and existing atomic paths. The authorized R1 market correction applies
the existing commodity/product-reason policy: R1-21 is INDIVIDUALLY_READY only
for its published 100-portion batch; selected_final_three remains empty. SALT
remains RU_AVAILABLE and passes default-use as an exact basic commodity. This
corrects R1, not the canonical policy or production truth. Published alternatives
do not automatically inherit kitchen verification.
No production truth or schema changes; migration remains 0029. The original
Assembly A gate remains blocked, and Assembly B / PR7+ remain unauthorized.


### RECIPE-ASSEMBLY-A-R2 — targeted recovery

2026-09-12. PR32 is MERGED at `8730b9fcfdb56cec2215f7e70319241c83431371`; R1 is COMPLETE
AS BLOCKED RESEARCH, accepted baseline 1/3. The [R2 evidence package](../../data/curation/recipe-assembly-a-r2/README.md)
reopens only R1-23 and R1-13. Outcome A is derived: R1-21 and R1-23 individually
ready, 2/3; selected final three = []. All R1 bytes remain unchanged.

AFRS General Information A001 and F00400 are retained from the same official
June 2003 system. Weight is EP, Issue is AP; 22 lb gives 9979.03214 g edible INPUT
with the accepted Decimal constant. EGG's existing INPUT composition is used for
whole edible egg, excluding shell. The source's 200 each is informational; no
piece mass, cooked output, yield or household-scale claim follows. Only method 1
(hot-water hard cooked), published 100 portions, is individually ready.

Cooking Rice rights are ACCEPT solely under the existing RIGHTS-FACTS policy:
factual data and independently authored Russian rules with USDA/FNS/project
attribution; ICN hosting is not authorship or a whole-card license. USDA FBG's
fresh-minced-garlic row supplies 2½ oz per ¼ cup. Exact rational scaling gives
35.43690390625 g for the source's 2 Tbsp, retained solely as R2 mass evidence.
No production measure row is created.

R1's candidate-level kitchen label does not establish every rice alternative.
The chosen water/regular-long-grain branch has exact current identities and
input masses, but its 27 oz table weight differs from step 3's 29 oz per pan;
separate applicable kitchen testing/process clarification is not established.
Each proposed replacement is checked as a full variant. Missing form,
Composition, mass and/or kitchen evidence keeps all substitutions unverified.
The seasoning OR joins two variations, with cilantro AND lime in one branch;
independent optional component omission is not proved. This does not mean the
unseasoned base requires either variation. Collective optional-role and verified
substitution gates stay open.

These are evidence decisions, not changes to canonical nutrition/composition,
accepted R1 bytes, production data, schema or runtime. Migration stays 0029.
Assembly A remains BLOCKED; Assembly B / PR7+ NOT STARTED. Stop for R2 review.
Resume implementation (0030) only after separate explicit authorization.


### RECIPE-ASSEMBLY-A-R3 — Third-Family Closure

2026-09-12. PR33 is MERGED at `f2b6bc9015a1b892bb533b5d322d981d5a1782bd`.
R1 and R2 are COMPLETE AS BLOCKED RESEARCH. The user authorized only a bounded
third-family evidence search; both accepted packages and the exact 100-portion
E00100 / F00400 method 1 decisions remain byte-for-byte unchanged.

[R3 evidence](../../data/curation/recipe-assembly-a-r3/README.md) exhausts the
12-candidate prefilter; none passes, so zero deep reviews occur. R3 BLOCKED,
2/3 individually ready; third candidate null and selected final three empty.
AFRS N50200 supplies explicit optional pepper/tomato garnish with separate
2 lb EP masses, but both full recipe branches retain incompatible turkey form
and missing required Composition. Source OR and exact garnish weights do not
close a substitution when the shared required base fails. Other candidates fail
current form/Composition or exact masses. Unreviewed rights/testing/market gates
remain unreviewed; they are not inferred from hosting or a recipe title.

The final-three family-count, optional-role and verified-substitution gates
remain OPEN. Other passing aggregate gates apply only to the two fixed members.
No source text semantics, market exception, food identity or production data is
relaxed. Migration stays 0029. Assembly A remains BLOCKED, not COMPLETE; B/PR7+
NOT STARTED. Stop for R3 review. No further search, food repair or implementation
is automatically authorized; any later Assembly A implementation with 0030
requires separate explicit authorization.
