# PR6-NUTRIENT-VECTOR-A — реестр нутриентов и аудит происхождения

**FACT / scope:** research/data/docs and offline validator/tests only. Starting
main is exactly `307ba3475581087b079ebcf2fa643e19a00bf06d`, merge PR #24
PR6-ARCH-COMPOSITION. Branch: `data/pr6-nutrient-vector-a-registry`.
This changeset establishes the registry/provenance audit for final review; it
does not implement NutrientVector or authorize VECTOR-B. A/B are bounded parts
of the existing roadmap operation, not new milestones.

## Reproducible artifacts and verified sources

- [nutrient-registry.json](nutrient-registry.json): 51 reviewed definitions,
  51 APPROVED_FOR_VECTOR_B, 0 DEFINITION_BLOCKED, 0 DEFERRED_EXTENSION.
  Approval describes definition readiness for later review/implementation,
  not authorization to execute VECTOR-B or a claim of source-value coverage.
- [source-mappings.json](source-mappings.json): 140 release-specific FDC mappings,
  including explicit rejected/unproven candidates; no profile micronutrients.
- [legacy-v1-crosswalk.json](legacy-v1-crosswalk.json): 183 profiles × 5 fields =
  915 observations, identified by food code + profile provenance + field.
- [source-manifest.json](source-manifest.json): authoritative references, retrieval
  instants, raw hashes where obtainable, selected nutrient vocabulary/food/amount
  rows, and complete accepted nutrition seed revision inventory.
- [summary.json](summary.json): derived deterministically by the validator.

The [USDA current download inventory](https://fdc.nal.usda.gov/download-datasets/)
was checked on 2026-09-10: **Foundation April 2026**, archive dated 2026-04-30;
**SR Legacy April 2018**, final SR release. The downloaded archives match hashes
already recorded by B2-B1. FNDDS 2021–2023, October 2024 is listed by USDA but
is not needed for these selected definitions or current profiles. No FNDDS food
values or candidate B2-B1 values are promoted.

The Data Dictionary is the actual XLSX bundled with Foundation, not a guessed API
schema. Its `food_nutrient` amount is per 100 g in `nutrient.unit_name`; food FDC
identity, component identity and food_nutrient observation identity are different
keys. Selected vocabulary rows retain both `id` and `nutrient_nbr`, raw English
name, raw unit, release and data type. Vocabulary membership does not prove a
food has a value for that nutrient. The manifest stores only required vocabulary
rows, all five legacy observations when present and alternative energy rows.

[FAO/INFOODS identifiers](https://www.fao.org/infoods/infoods/standards-guidelines/food-component-identifiers-tagnames/en/)
are external vocabulary, never FamilyFoodOS primary keys. The 2012 Food Matching
Annex 2 clarifies older tag spellings and carbohydrate/activity distinctions;
the 2012 Conversion Guidelines identify mineral tags. These references do not
authorize survey-style imputation, cross-source blending or source substitution.
The official PART2 link on the index is malformed; the root-relative published
PART2.TXT URL in the manifest was read successfully through web retrieval.
Shell retrieval of FAO documents returned HTTP 403; available official web text
was inspected instead. Unavailable raw-byte hashes remain null with explanations.
The selected factual tag records have a separate canonical-content hash, not a
pretended original-document hash. Three narrow INFOODS mappings remain unproven.

The Russian [МР 2.3.1.0253-21](https://ion.ru/upload/medialibrary/e70/xq18hm3mm1f1b3izde8kcb5136l8373z/%D0%9D%D0%BE%D1%80%D0%BC%D1%8B%20%D1%84%D0%B8%D0%B7%D0%B8%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D1%85%20%D0%BF%D0%BE%D1%82%D1%80%D0%B5%D0%B1%D0%BD%D0%BE%D1%81%D1%82%D0%B5%D0%B8%CC%86%202021.pdf)
was read from the authoring nutrition research institute's publication. Sections
4.1–4.3 support product relevance and Russian terminology. Its broader vitamin A
RE and vitamin E activity conventions are not silently treated as FDC RAE or
alpha-tocopherol mass. No numeric daily norms, member targets, medical formulas or
therapeutic claims are imported. Names below are project Russian translations;
raw official English names remain only in source evidence.

### Raw source SHA-256

| Manifest reference | SHA-256 |
| --- | --- |
| `FDC-DICTIONARY` | `84597b955d1d0b9ea4b407b0cc24a32b84f7bbc0ee06ef38a1d24011f3a281b4` |
| `FDC-DOWNLOADS` | `8611bb2030246fb0062622991213fc841c6ceb83b8761e5e5a9e81381102ba5d` |
| `FDC-FOUNDATION` | `70457ee9d9342f43bda2010318c85f04210c689fdeb9cd2da4c513b0e8dbc655` |
| `FDC-FOUNDATION-DOC` | `cc5dc67ee71a71860ebdc5c59774aa0642ef9f2dfecb81094a674d9837d691c9` |
| `FDC-SR` | `b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0` |
| `INFOODS-CONVERSIONS` | Raw hash unavailable; see limitation in manifest |
| `INFOODS-ENERGY` | Raw hash unavailable; see limitation in manifest |
| `INFOODS-MATCHING` | Raw hash unavailable; see limitation in manifest |
| `INFOODS-OCEANIA` | Raw hash unavailable; see limitation in manifest |
| `INFOODS-PART2` | Raw hash unavailable; see limitation in manifest |
| `INFOODS-PART3` | Raw hash unavailable; see limitation in manifest |
| `INFOODS-PART4` | Raw hash unavailable; see limitation in manifest |
| `USDA-AH74` | `88997b0743ed647b056daafd61fcdc6adfabf1b9a0b7faaeb07c42dd32bf0e9d` |
| `RU-MR` | `cf96c7ea7fab087d16b478b2c8c097406d7572e495b2beb43405e4fd05917d79` |

Selected canonical extracts (UTF-8 JSON, sorted keys, compact separators):

- Foundation: `8f6e4d366fbab399e9d7fac1e0251292e65cc0c023f94121ca58cdba3ff34375`.
- SR Legacy: `319e2202c7f20315cfbbf332293a045423bde7a39bae13fc32744f6907fd90ca`.
- INFOODS identifiers: `a2c36ff619f8670536c6074dc01a8cebd4a9307d5f4b504e5aecd05391009104`.

USDA archive data are public domain / CC0. Source attribution is retained.
FAO full publications and the Russian MR are not copied into the repository;
references, project-written definitions and selected factual identifiers suffice.
Full archives, raw documents and temporary extraction tooling are not committed.

## Canonical registry

Internal identity is the project `canonical_code`, never FDC ID or INFOODS tag.
Canonical microgram spelling is **`µg` (U+00B5)**. `ug`, `UG`, `mcg` are source
spellings, not additional canonical units. Russian unit display is exactly
`kcal → ккал`, `g → г`, `mg → мг`, `µg → мкг`; all 51 names are present and
admin-ready, with no English/code fallback. Unit distribution: **16 g, 1 kcal,
20 mg, 14 µg**. Categories: 9 proximate, 9 lipid, 15 mineral, 18 vitamin entries.

`DIRECT_COMPONENT` describes a chemical substance or chemically defined group.
It does **not** certify that any source value was directly measured: a component
value can be analysed, summed, imputed, averaged or otherwise derived by its
source. Those value-level facts remain provenance. `DERIVED_COMPONENT` describes
an operational calculation/activity definition (energy, nitrogen-derived protein,
carbohydrate by difference/summation, RAE, D2+D3 sum and DFE). Both classes preserve
source method and uncertainty; neither grants an estimated=false flag.

All following entries have status `APPROVED_FOR_VECTOR_B`. Exact definitions,
tracking tier, evidence references and limitations are in the registry JSON.
Tracking tiers organize food vocabulary and are not personal nutrition targets.

| Canonical code | Русское название | Unit | Definition kind | INFOODS tag |
| --- | --- | --- | --- | --- |
| `ALPHA_LINOLENIC_ACID` | Альфа-линоленовая кислота | g | DIRECT_COMPONENT | F18D3CN3 |
| `BETA_CAROTENE` | Бета-каротин | µg | DIRECT_COMPONENT | CARTB |
| `BIOTIN` | Биотин | µg | DIRECT_COMPONENT | — |
| `CALCIUM` | Кальций | mg | DIRECT_COMPONENT | CA |
| `CARBOHYDRATE_AVAILABLE` | Усвояемые углеводы | g | DERIVED_COMPONENT | CHOAVL |
| `CARBOHYDRATE_BY_DIFFERENCE` | Углеводы по разности | g | DERIVED_COMPONENT | CHOCDF |
| `CHLORIDE` | Хлориды | mg | DIRECT_COMPONENT | CL |
| `CHOLESTEROL` | Холестерин | mg | DIRECT_COMPONENT | CHOLE |
| `CHOLINE_TOTAL` | Холин, всего | mg | DIRECT_COMPONENT | — |
| `CHROMIUM` | Хром | µg | DIRECT_COMPONENT | CR |
| `COPPER` | Медь | mg | DIRECT_COMPONENT | CU |
| `DHA` | Докозагексаеновая кислота | g | DIRECT_COMPONENT | F22D6N3 |
| `ENERGY_KCAL` | Энергетическая ценность | kcal | DERIVED_COMPONENT | ENERC |
| `EPA` | Эйкозапентаеновая кислота | g | DIRECT_COMPONENT | F20D5N3 |
| `FATTY_ACIDS_MONOUNSATURATED_TOTAL` | Мононенасыщенные жирные кислоты, всего | g | DIRECT_COMPONENT | FAMS |
| `FATTY_ACIDS_POLYUNSATURATED_TOTAL` | Полиненасыщенные жирные кислоты, всего | g | DIRECT_COMPONENT | FAPU |
| `FATTY_ACIDS_SATURATED_TOTAL` | Насыщенные жирные кислоты, всего | g | DIRECT_COMPONENT | FASAT |
| `FATTY_ACIDS_TRANS_TOTAL` | Трансжирные кислоты, всего | g | DIRECT_COMPONENT | FATRN |
| `FAT_TOTAL` | Жиры | g | DIRECT_COMPONENT | FAT- |
| `FIBER_TOTAL_DIETARY` | Пищевые волокна | g | DIRECT_COMPONENT | FIBTG |
| `FLUORIDE` | Фториды | mg | DIRECT_COMPONENT | FD |
| `FOLATE_DFE` | Фолаты, пищевые эквиваленты | µg | DERIVED_COMPONENT | FOLDFE |
| `FOLATE_TOTAL` | Фолаты, всего | µg | DIRECT_COMPONENT | FOL |
| `FOLIC_ACID` | Фолиевая кислота | µg | DIRECT_COMPONENT | FOLAC |
| `IODINE` | Йод | µg | DIRECT_COMPONENT | ID |
| `IRON` | Железо | mg | DIRECT_COMPONENT | FE |
| `LINOLEIC_ACID` | Линолевая кислота | g | DIRECT_COMPONENT | F18D2CN6 |
| `MAGNESIUM` | Магний | mg | DIRECT_COMPONENT | MG |
| `MANGANESE` | Марганец | mg | DIRECT_COMPONENT | MN |
| `MOLYBDENUM` | Молибден | µg | DIRECT_COMPONENT | MO |
| `NIACIN` | Ниацин | mg | DIRECT_COMPONENT | NIA |
| `PANTOTHENIC_ACID` | Пантотеновая кислота | mg | DIRECT_COMPONENT | PANTAC |
| `PHOSPHORUS` | Фосфор | mg | DIRECT_COMPONENT | P |
| `POTASSIUM` | Калий | mg | DIRECT_COMPONENT | K |
| `PROTEIN` | Белки | g | DERIVED_COMPONENT | PROTCNT |
| `RETINOL` | Ретинол | µg | DIRECT_COMPONENT | RETOL |
| `RIBOFLAVIN` | Витамин B2 (рибофлавин) | mg | DIRECT_COMPONENT | RIBF |
| `SELENIUM` | Селен | µg | DIRECT_COMPONENT | SE |
| `SODIUM` | Натрий | mg | DIRECT_COMPONENT | NA |
| `STARCH` | Крахмал | g | DIRECT_COMPONENT | STARCH |
| `SUGARS_TOTAL` | Сахара, всего | g | DIRECT_COMPONENT | SUGAR |
| `THIAMIN` | Витамин B1 (тиамин) | mg | DIRECT_COMPONENT | THIA |
| `VITAMIN_A_RAE` | Витамин А, эквивалент активности ретинола | µg | DERIVED_COMPONENT | VITA_RAE |
| `VITAMIN_B12` | Витамин B12 | µg | DIRECT_COMPONENT | VITB12 |
| `VITAMIN_B6` | Витамин B6 | mg | DIRECT_COMPONENT | VITB6- |
| `VITAMIN_C` | Витамин С | mg | DIRECT_COMPONENT | VITC |
| `VITAMIN_D_D2_D3` | Витамин D, сумма D2 и D3 | µg | DERIVED_COMPONENT | VITD |
| `VITAMIN_E_ALPHA_TOCOPHEROL` | Витамин Е, альфа-токоферол | mg | DIRECT_COMPONENT | TOCPHA |
| `VITAMIN_K_PHYLLOQUINONE` | Витамин К1, филлохинон | µg | DIRECT_COMPONENT | — |
| `WATER` | Вода | g | DIRECT_COMPONENT | WATER |
| `ZINC` | Цинк | mg | DIRECT_COMPONENT | ZN |

Future extension categories, not auto-added candidates: individual amino acids,
additional fatty-acid species, individual carotenoids, additional vitamin K forms,
other vitamers, organic acids and other validated food components. Adding a
definition must add a registry entry, not a new nutrient SQL column. This initial
universe is not a permanent maximum.

## Mapping results and exceptions

FDC counts are **release-specific mappings**, not unique nutrients or food values:
76 EXACT, 24 METHOD_SPECIFIC, 24 DISTINCT_COMPONENT, 6 UNIT_CONVERSION_REQUIRED,
10 NO_ACCEPTABLE_MAPPING. Each selected relation is represented for Foundation
2026-04-30 and SR Legacy 2018-04 with that archive's exact name/unit/nbr.
FDC nutrient 2000 is named `Total Sugars` in Foundation and `Sugars, Total` in
SR; raw names are retained without changing project identity.

INFOODS counts are **registry entries**: 36 EXACT, 11 METHOD_SPECIFIC,
1 UNIT_CONVERSION_REQUIRED, 3 NO_ACCEPTABLE_MAPPING. These two denominators must
not be compared as though both counted food observations.

Explicit unproven mappings:

- `CARBOHYDRATE_AVAILABLE` has no selected FDC match. The definition is the
  specific INFOODS **CHOAVL** sum of sugars, starch and glycogen by component
  weight. CHOAVLDF (by difference), CHOAVLM (monosaccharide equivalents), CHOCDF
  and CHOCSM are different definitions, not aliases or automatic conversions.
- FDC 1050 (`Carbohydrate, by summation`) does not establish its exact summed
  fractions in the selected dictionary. It is NO_ACCEPTABLE_MAPPING for CHOAVL;
  neither equivalence nor a particular CHOCSM composition is inferred by name.
- `CHLORIDE` is defined through INFOODS CL / Russian «Хлориды». FDC 1088 says
  `Chlorine, Cl`; its selected dictionary entry does not establish chloride-only
  speciation. Both the absent approved FDC match and the unproven 1088 candidate
  are explicit. No numeric amount is used from 1088.
- FDC 1063's similar sugar name does not establish compatibility with selected
  total sugar semantics. Its mapping remains NO_ACCEPTABLE_MAPPING, rather than
  inferring equivalence to 2000 from the label.
- Narrow INFOODS identifiers for **BIOTIN, CHOLINE_TOTAL and
  VITAMIN_K_PHYLLOQUINONE** were not established in the selected documents and
  remain null. The FDC-backed definitions are valid; no tag is invented. INFOODS
  VITK denotes K1+K2, so it is not accepted for phylloquinone alone.

The 12 rejected component pairs, each represented in both releases, are:
available carbohydrate ← 1005; total fat ← 1085 (NLEA);
linoleic acid ← 1269 (unspecified 18:2); ALA ← 1270 (unspecified 18:3);
vitamin A RAE ← 1105, 1107, 1104 or 1156; folate DFE ← 1177;
folate total ← 1186; alpha-tocopherol ← 1158 (activity equivalents);
phylloquinone ← 1183 (menaquinone-4). All fail closed if promoted to EXACT.
There is no invented OMEGA_3_TOTAL or rule for adding overlapping lipid totals.

### Allowed conversion requirements for VECTOR-B

Only documentation here; no conversion runtime is implemented.

| Source | Canonical amount requirement | Conditions |
| --- | --- | --- |
| FDC 1099 / INFOODS FD, µg fluoride | mg = source / 1000 | Exact dimensional conversion; source basis preserved. |
| FDC 1110, D2+D3 IU | µg = source / 40 | INFOODS VITD defines 40 IU/µg. One observation selected, never added to 1114. |
| FDC 1062, energy kJ | kcal = source / 4.184 | [USDA Handbook 74](https://www.ars.usda.gov/ARSUserFiles/80400525/Data/Classics/ah74.pdf), revised February 1973, preface p. iii confirms the unit factor; energy method remains material. Does not replace accepted source kcal. |

Upper/lower-case source mass-unit spellings normalize without scaling. There is
no universal vitamin A IU→RAE, RE→RAE, vitamin E activity→mass, folate mass→DFE,
fatty-acid→total-fat or total→available-carbohydrate scalar conversion. Derived
calculations would require their complete inputs and a separately versioned
calculation contract. Six decimal places are the legacy representation contract,
not a blanket claim of scientific precision for every future micronutrient.

## Legacy-v1 coverage and results

The inventory unions **every nutrition.csv revision reachable from the exact
starting main**, including all historical provenance identities. The original
PR3 100 profiles and PR4-DATA expansion to 183 use unchanged values/provenance
for the original 100. No accepted profile has been replaced: **183 distinct
profiles, 183 current, 0 historical-only**. The focused test reads all
food_nutrition_profiles from a disposable accepted seed database without an
is_current filter. It also proves that replacement in a separate test scenario
retains a historical profile and that an extra historical inventory identity
cannot pass with missing crosswalk rows.

This is the complete accepted repository production corpus, not an assertion
about unknown deployments or private developer data. A deployment with any
additional current/historical profiles needs a full provenance export and audit
before VECTOR-B backfill. Such profiles must never be silently omitted. No
developer or real-user database was opened or mutated.

| Legacy result | Observations |
| --- | ---: |
| SOURCE_COMPONENT_CONFIRMED | 870 |
| LEGACY_PROFILE_VALUE_CONFIRMED_SOURCE_ID_UNAVAILABLE | 0 |
| VALUE_MISMATCH | 0 |
| DEFINITION_AMBIGUOUS | 0 |
| VALUE_ABSENT | 45 |

All mismatch rows: **none**. All ambiguous rows: **none**. There are **64 known
zero observations** and **45 unknown fibre observations**, all retained as such.
138 profiles have five confirmed source values; 45 have four plus absent fibre;
0 have unresolved provenance for a present legacy value. Absence is reported
separately from unresolved provenance, and never counted as a fifth confirmed ID.

Source selection is independently evidenced by the protected accepted
[seed transformation rules](../../seed/food_ingredients/README.md#transformation-and-review-rules)
and the actual downloaded food_nutrient rows. Numeric comparison parses raw CSV
amount text as Decimal, uses a private precision-80 ROUND_HALF_UP context and
normalizes to 6 decimal places under the existing contract. Equality has no
tolerance. Raw source amount and normalized amount are both retained.

**Energy:** all 183 kcal values match their selected source observation and food:
81 SR Legacy 1008; 97 Foundation 2048 (specific factors); 5 Foundation 2047
(general factors). Source name/unit/nbr/release and observation ID are retained.
1008 is not relabelled as a specific-factor calculation. Alternative energy rows
are evidence only, never additional contributions or a recomputed replacement.

**Carbohydrate:** all 183 profiles use FDC 1005, carbohydrate by difference.
None is classified as available carbohydrate. Legacy fibre subtraction does not
derive a new accepted nutrient. **Vitamin A:** RAE, retinol and beta-carotene stay
separate. **Folate:** total, DFE and folic acid stay separate. No new food amounts
for any of these micronutrients are produced by the registry.

## VECTOR-B implementation recommendation

This section is implementation-ready guidance within the approved architecture,
not permission to write schema/runtime. SQL naming and migration mechanics belong
to the separately authorized VECTOR-B review.

### One profile container and one current selector

Keep the existing **FoodNutritionProfile** as the platform-owned profile/version/
provenance container. Preserve its identity, FoodIngredient FK, immutable source
snapshot, 100 g basis and current-profile selection. Add normalized values by FK
to that existing profile. The conceptual FoodNutritionProfileVersion in the target
diagram is that versioned role, not a mandate for a second competing profile table.
Preserve B1 assessment FKs and historical bindings; no automatic review rebinding.

Recommend one effective value per `(profile identity, canonical nutrient code)`.
Retain a reference to an immutable version of the registry/source mapping used.
Do not use raw FDC IDs as project PKs. If a source has several energy rows, the
existing legacy selection wins during compatibility backfill; retain the selected
component/method and never add the alternatives. Any new selection precedence
outside this proven backfill requires explicit review, not insertion-order choice.

Minimum recoverable provenance:

| Level | Required information |
| --- | --- |
| Existing immutable profile FK | FoodIngredient identity; source food name/id; source release/data type; basis grams; verification instant; profile estimation state. |
| Nutrient value | Canonical code; nonnegative finite Decimal amount; source component ID/nbr/name/unit; source food_nutrient observation locator; source derivation/method; raw source amount; mapping version/status; unit normalization; nutrient uncertainty/estimation state. |
| Immutable evidence/mapping FK | Exact component metadata, release and method documentation can be referenced instead of copied into every value, provided history is recoverable without network or a mutable “current mapping”. |

The source locator must be nutrient-level, even when release and source food are
inherited from the profile. Unknown derivation detail or `estimated=null` stays
unknown. Semantic EXACT is not “analytically measured” and does not imply no
uncertainty. A future below-quantification observation needs a censor/limit state;
it is never auto-imported as an exact zero. Cross-source blending remains forbidden
without separately approved policy.

### Absence versus zero, tested adversarially

Recommendation accepted for VECTOR-B: **no persisted nutrient-value row = unknown
authoritative amount** for that nutrient in the selected immutable profile.
**Persisted amount = 0 = known numeric zero**, retaining its source/method/uncertainty.
Do not materialize a full profile × nutrient matrix of nullable numeric rows.

This interpretation applies to a complete, successfully loaded profile snapshot:

| Adversarial case | Required behavior |
| --- | --- |
| Source omitted nutrient or legacy fibre is null | No numeric row; unknown. Never insert zero. |
| Source explicitly reports zero | Keep zero with provenance. It is not a missing row. |
| Source below detection/quantification limit | No fabricated exact amount; preserve limit/uncertainty evidence separately. |
| Filtered/lazy repository query omitted rows | Query omission is not nutrient absence. Full value-set read contract or explicit loaded coverage is required. |
| Import crashes after a subset | Atomic transaction rolls back; partial profile must not become current/available. |
| Source has an unmapped/ambiguous component | No accepted canonical amount; keep rejected/blocked source observation in review evidence. |
| New definition added to registry | Missing historical values remain unknown; no mass insertion of zero/null rows. |
| Required aggregate component unknown | Its nutrient total remains unknown; never sum only known contributions as a complete total. |
| Historical profile replay | Read pinned profile/value-set and mapping versions, never current-profile substitutions. |

Absence describes availability, not the reason. Distinct reasons (not analysed,
mapping rejected, censored, not imported) live in source/review/ingestion evidence
when needed. No case found requires a nullable numeric row to preserve those
reasons. VECTOR-B must atomically backfill/seal the value set and enforce complete
reads; adding values later must not silently rewrite an immutable historical
snapshot. The initial migration is an explicitly reviewed augmentation of existing
profile identities. Later enrichment/versioning rules are not authorized here.

### Legacy projection rules

- SOURCE_COMPONENT_CONFIRMED: transfer the accepted 6-decimal amount under the
  proven canonical code with the exact source locator; preserve v1 behavior.
- LEGACY_PROFILE_VALUE_CONFIRMED_SOURCE_ID_UNAVAILABLE: retain accepted amount as
  **LEGACY_PROJECTION**, with component ID/name/unit unknown and explicit origin
  status. A canonical code may be assigned only if its legacy semantics are
  independently proved. Never claim SOURCE_COMPONENT_CONFIRMED or invent an ID.
- VALUE_MISMATCH: preserve the accepted legacy value for v1 replay and flag the
  conflict; do not substitute the newer/retrieved value without separate review.
- DEFINITION_AMBIGUOUS: do not create an authoritative canonical value by guess.
  Keep original v1 field/history separately available until a decision resolves it.
- VALUE_ABSENT: no numeric row; v1 projection remains null. Never manufacture zero.

For the current accepted corpus all present amounts are confirmed; the four
exception paths remain explicit requirements for deployment-specific extensions.
Compatibility projection retains the existing five field meanings, rounding and
FAMILY_FOOD_NUTRITION_V1 behavior. Micronutrient absence cannot change v1 calories
or fill unknown fibre. Existing profiles and assessment identities remain stable.

## Verification and protected boundary

```sh
backend/.venv/bin/python scripts/validate_pr6_nutrient_vector_a.py
AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests/test_pr6_nutrient_vector_a_registry.py
ruff check scripts/validate_pr6_nutrient_vector_a.py backend/app/tests/test_pr6_nutrient_vector_a_registry.py
ruff format --check scripts/validate_pr6_nutrient_vector_a.py backend/app/tests/test_pr6_nutrient_vector_a_registry.py
git diff --check
backend/.venv/bin/python scripts/validate_pr6_nutrient_vector_a.py --staged
git diff --cached --check
```

`--write-summary` writes only summary.json, after content validation. Ordinary
tests/validator never access the network. Re-downloading sources is a research
operation; verify full archive/member hashes before re-extracting the selected
rows. Source extraction selects `nutrient.csv` IDs referenced by source mappings,
`food.csv` IDs from the full legacy inventory and legacy/alternative-energy
`food_nutrient.csv` rows for those foods. Source strings are copied losslessly;
selection hashes use the canonical JSON encoding described above.

Verification tier: data curation with focused adversarial research tests,
documentation links and scope checks. No runtime change warrants full regression.
The validator compares all changes against the exact starting-main tree and an
explicit 15-file research/docs/test allowlist; 961 existing files are protected.
It verifies the migration registration remains 0027 and all 43 existing estimate
rows still have null mass. Tests include duplicate/missing/historical coverage,
Russian display, units, forged provenance, semantic collisions and Decimal edge
cases. Actual executed outcomes are recorded in
[state/progress.md](../../../state/progress.md#pr6-nutrient-vector-a-verification).

Production seeds, runtime, repositories/UoW, APIs, frontend/admin/PDF, migrations,
B1 evidence/assessments, B2-A recipes and B2-B1 research remain byte-identical.
No real database is mutated. No migration 0028, production nutrient tables,
micronutrient amounts, composition model, member targets or estimate policy.
The unrelated local .DS_Store change is excluded from delivery.

**PR6 — NOT COMPLETE. PR6-NUTRIENT-VECTOR — NOT COMPLETE.
VECTOR-B — NOT AUTHORIZED. COMPOSITION-CORE — UNAUTHORIZED. PR7+ — UNAUTHORIZED.**
No autonomous merge or automatic next operation.
