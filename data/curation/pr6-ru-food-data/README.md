# PR6-RU-FOOD-DATA

Bounded Russian food-data foundation, based on verified main
`d5b5ce3fdc4ec79de5454b3ed23b1d527772c0bc` (PR #27 merged).
Migration head remains `0029_food_composition_core`. PR6 is **NOT COMPLETE**.

## Scope and measured population

The package audits the 81 FoodIngredient codes used by all 30 current
RecipeVersions: 185 required + 4 optional rows. Seven additional form candidates
are research records, with no existing recipe binding changed.

[food-readiness.json](food-readiness.json) is the versioned machine-readable
review record. `canonical_name_ru` is a checked projection of the existing
`FoodIngredient.canonical_name`, never a second database display authority.
`food_form` preserves the exact source description as engineering provenance;
it is not a Russian consumer label. Required/optional current usages are separate.

The complete reproducible [audit](implementation-evidence.json) measures:

- 183 existing foods/profiles/seals retained; 2 new foods/profiles/seals;
- 66 new normalized nutrient values, 33 per new profile;
- 60 RU_READY records (58 existing + 2 additions), 28 NOT_READY;
- all 88 researched records: 4 RU_MASS_MARKET, 73 RU_AVAILABLE,
  11 SPECIALTY_OR_UNCLEAR;
- 60 immutable ATOMIC versions; no COMPOSITE, nodes, transformation, yield,
  retention or recipe production additions;
- second seed: zero inserts and identical database contents;
- all existing rows preserved, all 183 former vectors readable before and after;
- identical full Nutrition v1 readiness report: 30 recipes / 189 rows /
  30 INCOMPLETE; 66 exact / 21 no-conversion / 37 review-required / 65 blocked;
  all 43 estimates remain non-executable.

These are actual accepted production-seed results on disposable databases.
Adversarial synthetic profiles exist only in tests and are excluded from counts.
No developer/household database is opened by the audit.

## Seven reviewed candidate decisions

| Candidate | Decision | Exact evidence and limitation |
| --- | --- | --- |
| APPLE_PEELED | DEFER | SR 171689, raw without skin, revalidated. No acceptable purchased peeled-raw form established. Whole-apple purchase evidence cannot stand in for a separately reviewed preparation/output path. |
| CAULIFLOWER_FROZEN | PROMOTE | SR 170398, frozen unprepared; official inspected Lenta listing of plain frozen florets. Distinct from fresh CAULIFLOWER. No claim that this product is ready to eat raw. |
| LEMON_JUICE | DEFER | B2-B1 FNDDS 2709180 remains a generic research proposal; no approved FNDDS registry mapping or exact raw/packaged default. Whole lemons do not supply juice yield or purchased juice evidence. |
| ORANGE_JUICE | DEFER | B2-B1 FNDDS 2709186 blends ordinary and calcium-added packaged juices. No approved exact single-form/default or FNDDS mappings; primary fresh-juice page retrieval returned 401. No concentrate/fruit remap. |
| PASTA_COOKED | DEFER | SR 168928, cooked unenriched without salt, revalidated. Inspected purchase lead includes salt, oil and a chicken cutlet; dry pasta cannot prove this exact cooked form. Home preparation/output binding is outside scope. |
| SPINACH_BABY | DEFER | Foundation 1999632 revalidated. A third-party baby-spinach listing is a lead only; no inspected primary retailer/SPB evidence established. Generic spinach does not prove baby leaves. |
| STRAWBERRY_FROZEN_UNSWEETENED | PROMOTE | SR 168173, frozen unsweetened; official inspected Lenta listing has only strawberry in its ingredient list. Distinct from raw STRAWBERRY. |

Promotion is deliberately bounded to two named source identities. Source failure
produces DEFER, not a substituted profile. No candidate is rejected as inherently
invalid. The remaining 23 existing NOT_READY records retain their active catalogue
records. Nineteen have open B2-B1 identity/profile review; additional evidence
mismatches include frozen green beans versus raw, raw sesame purchase versus toasted,
whole-lime purchase versus juice, and milk-source vitamin fortification not
established by the market evidence. The retained artifact lists every blocker.
No existing current profile is replaced to remove these blockers.

## Market evidence and default eligibility

[market-evidence.json](market-evidence.json) retains source URL/ID, Russian wording,
exact observed form, SPB/LO region, date, chain, status, form review and review
reference. Reused PR4-DATA2 observations retain their original date and exact
source observation/form IDs. Their source files are hash-pinned. Materially
incompatible forms are UNCERTAIN rather than silently reusing a purchase-family
classification. New forms have fresh research records dated 2026-09-12.
[research-log.json](research-log.json) records queries, inspections and limitations.

Classification counts distinct qualifying chains in the unchanged five-chain
panel. Three give RU_MASS_MARKET; one/two give RU_AVAILABLE. Secondary VkusVill
and unconfirmed research leads do not count toward that threshold. Missing evidence
fails closed. Tap water uses the documented explicit exception; ordinary commodity
categories retain actual source evidence. No evidence TTL is introduced.

The accepted PR4 method allows an official chain-neutral product listing plus
inspected official SPB/LO chain presence. AVAILABLE means representation in the
curation panel, not store-level stock. The primary [cauliflower listing](https://lenta.com/product/kapusta-cvetnaya-zam-400g-645567/),
[strawberry listing](https://lenta.com/product/klubnika-zam-300g-495855/) and
[Lenta SPB/LO store directory](https://lenta.com/info/shops/?citykey=spb&withRedirect=true)
were inspected; no cart, address, price or live-stock facts are imported.

RU_READY describes the bounded food-data contract, including explicit unknowns.
It does not mean every nutrient is known, or that an existing recipe is valid.
The artifact separately derives `default_pool_eligible`: only RU_READY plus
RU_MASS_MARKET passes this food/market gate (EGG, SUGAR, WATER here). RU_AVAILABLE
records, including both additions, remain blocked from default selection until a
reviewed ordinary substitution path is supplied. No substitution path is invented.
Later consumers must also check their requested nutrient coverage, preparation,
recipe/assembly and kitchen gates. This PR authorizes no consumer recipe or menu.
In particular, an empty sealed WATER vector remains explicitly unknown under the
unchanged zero policy; a market/display flag does not make its nutrients complete.

## Nutrition and immutable composition

[source-manifest.json](source-manifest.json) retains exact archive URLs, SHA-256,
member hashes, retrieval instant, source releases/data types, all food_nutrient
rows for five SR/Foundation candidates, vocabulary and available derivation rows.
Both official archives were downloaded again from USDA and matched B2-B1 hashes:
SR April 2018 and Foundation 2026-04-30. Retained facts are bounded public-domain
USDA extracts, with attribution; no source images or branding are imported.
Foundation's archive lacks a derivation table; that absence is recorded, not filled.

The separate `ru_food_vector_import.py` path imports all positive source values
with approved EXACT/METHOD_SPECIFIC same-unit mappings in the existing 51-code
registry. All 33 compatible positive observations per promoted profile are imported
at source Decimal precision. Incompatible components, unselected energy methods,
missing values and unresolved source zeros remain dispositions in the sealed
observation inventory. Neither source has a positive additional compatible
unit-conversion observation omitted by this rule. No densification, cross-source
merge, implicit zero, averaging or new zero policy exists. SR energy 1008 is the
explicit source choice for both; legacy fields are projections of that same row
set. The historical `nutrient_vector_backfill_v1.py` is byte-identical to main.

Profile/vector/composition are created in one project UoW. Repositories do not
commit independently. Vector values precede their seal. Composition versions pin
local UUIDs resolved from exact profile provenance, never mutable current selectors.
The artifact's natural reference is `(food_code, composition version=1, operation,
profile source name/id/release)`; local generated UUIDs are not committed as data.
Conflicting data aborts the entire transaction. Historical snapshots are compared,
never rewritten. Sealed reads and CompositionCalculator validate each approved food.

## Reproduction and recovery

Use the accepted migrations and seed chain first, then the explicit RU seed.
Historical loaders do not silently acquire later production data:

```sh
# From backend/, on a deliberately selected database:
AI_ENABLED=false .venv/bin/python -m app.seed.food_recipes
AI_ENABLED=false .venv/bin/python -m app.seed.nutrition_measure_evidence
AI_ENABLED=false .venv/bin/python -m app.seed.recipe_corrections corrections
AI_ENABLED=false .venv/bin/python -m app.seed.recipe_corrections assessments
AI_ENABLED=false .venv/bin/python -m app.seed.ru_food_data
AI_ENABLED=false .venv/bin/python -m app.seed.ru_food_data
```

The audit runs that full production baseline on a fresh temporary database,
compares all pre-existing tables/rows and the full readiness report, reads every
seal and approved composition, and proves the second RU seed is a no-op:

```sh
AI_ENABLED=false backend/.venv/bin/python scripts/audit_pr6_ru_food_data.py
AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests/test_ru_food_data.py
```

For raw source replay, download the exact archive URLs from the manifest into an
external temporary directory as `SR-RELEASE.zip` and `FOUNDATION-RELEASE.zip`, then:

```sh
backend/.venv/bin/python scripts/validate_pr6_ru_food_sources.py --source-directory /path/to/archives
```

It checks archive and member hashes before comparing all retained rows to primary
CSV bytes; ordinary tests need no network. The seed verifies fixed package hashes
and protected input hashes before opening a database. JSON is reviewed, versioned
repository data, not mutable external runtime input. Its statuses are independently
derived by deterministic gates and verified against expected vector digests.

Failure before commit rolls back all new food/profile/vector/composition rows.
After successful commit, operational rollback restores a pre-seed backup through
the existing backup/restore procedure; it does not delete immutable historical
truth. The schema/export table inventory is unchanged, and new rows use the
already-supported 0029 tables. Retain this exact package with its database backup.

No API, UI, AI, Retail runtime, Recipe Assembly, recipe remapping or estimate
acceptance is introduced. The next candidate after reviewed merge is separately
authorized PR6-DATA-B2-B2-REDESIGNED; it does not start automatically.
