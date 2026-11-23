# TAXONOMY GATE — EAEU/Russia food-component classification research and proposed decision

**Status:** RESEARCH / PROPOSED / NOT AN APPROVED TAXONOMY / NO_RUNTIME.
**Date:** 2026-11-23.
**Accepted base:** `main@66bcaafc600e3a12e2041fcc04fdc4c20f30cad9` (PR #300 and #301 merged).
**Owning context:** Food Catalogue / exact `FoodIngredient` identity. **Market:** Russia; EAEU regulatory baseline.
**Parent contract:** [allergen attestation publication implementation contract](../../family-food/allergen-attestation-publication-implementation-contract-2026-11-23.md).
**Owner action sought:** independent review of the **taxonomy proposal**, not automatic production authorization.

## 1. Purpose and boundary

Determine whether TR TS 022/2011, article 4, section 4.4, points 13–17, can serve as a *version-pinned regulatory component-flagging baseline* for FamilyFoodOS. Distinguish legally listed components from clinical allergen claims. The regulation primarily governs **food labelling**, not medically complete allergy risk prediction or universal ingredient safety. Its list must not be used to declare foods allergy-free.

This is deliberately one **docs-only research/decision PR**. It creates no approved per-food mapping, review authority, source-byte receipt, migration, runtime taxonomy table, publisher, seed publication, Planner/Shopping admission or consumer UI. It does not close SOURCE/TRUST or LEGACY ADMISSION.

## 2. FACT — source and effective-status evidence

| Evidence | Verified from | Finding | Limitation |
| --- | --- | --- | --- |
| Original technical regulation | [Official EEC-hosted TR TS 022/2011 PDF](https://eec.eaeunion.org/upload/medialibrary/9db/TrTsPishevkaMarkirovka.pdf), article 4 §4.4 pts 13–17 | Text lists 15 classes of components relevant to allergic reactions **or** contraindications in specified diseases, as part of labelling requirements; point 17 addresses possible presence | This is the historical base PDF, **not** in itself a certified consolidated effective 2026 edition |
| Consolidated amendment context | [Consolidated text with amendments as of 22 April 2024](https://sudact.ru/law/reshenie-komissii-tamozhennogo-soiuza-ot-09122011-n_3/tr-ts-0222011/statia-4/4.4/); [alternative consolidated representation](https://prg.kz/document/?doc_id=31106872) | These third-party reproductions identify the 2024 amendment date / consolidated legal text | Not a substitute for official EEC amendment-chain verification and original downloaded-byte receipt |
| October 2026 legal act | [Official EAEU legal portal, College order No. 163 of 27 Oct 2026](https://docs.eaeunion.org/documents/464/10993/) | Order **approves a draft Council decision**; order published 30 Oct 2026, in force 30 Oct 2026 | Entry into force of the *order to submit a draft* does **not** mean the proposed TR TS changes are enacted |
| Draft content | [EAEU-hosted annex to order 163](https://docs.eaeunion.org/upload/iblock/002/t13r7jbh6h0foswmr8stfofregftqcg5/Rasporyazhenie-Kollegii-_-163-ot-27-oktyabrya-2026-g.pdf) | Draft changes 4.4 points 14–16, including more detailed exceptions and thresholds; unsigned draft Council decision itself specifies entry into force 360 days after eventual publication | **Not effective law on the evidence obtained.** Recheck Council adoption and effective date before calling any future version current |

**Research verification method:** inspected machine-readable official EEC PDF text and a rendered screenshot of original PDF page containing §4.4 labelling rules; EAEU official act metadata checked. The annex screenshot and a further original PDF page screenshot failed in the web reader. **No full PDF bytes were downloaded and independently SHA-256 verified.** Thus original-artifact verification required by DATA-CORPUS-V1 and SOURCE/TRUST **has not occurred**. No accepted legal-version receipt exists from this research alone.

**As-of conclusion, 2026-11-23:** the 2026 amendment is established as a **draft submitted to Council**. No final adopted Council amendment with verified effective date was established by this research. A later official act may change the result; do not extrapolate.

## 3. FACT — 15 listed component categories (current historical baseline)

This table transcribes the structure of article 4, §4.4, point 14 from the official historical text, **not** a release-ready classification of FoodIngredients. Machine codes are **proposed platform names** only, with no approval/activation.

| № | Regulatory component group (RU) | Proposed candidate code | Important semantic caveat |
| --- | --- | --- | --- |
| 1 | Арахис и продукты его переработки | `PEANUT` | Origin/derived forms require evidence |
| 2 | Аспартам и аспартам-ацесульфама соль | `ASPARTAME_PHENYLALANINE` | Phenylalanine-warning / disease contraindication, **not interchangeable with IgE allergen** |
| 3 | Горчица и продукты её переработки | `MUSTARD` | Exact source and formulation |
| 4 | Диоксид серы и сульфиты выше 10 мг/кг или 10 мг/л в пересчёте на SO₂ | `SULFITES_ABOVE_LIMIT` | **Quantitative, finished-product contextual threshold**; not a simple `FoodIngredient` yes/no |
| 5 | Злаки, содержащие глютен, и продукты их переработки | `GLUTEN_CEREALS` | Gluten/intolerance scope, not a universal allergy statement |
| 6 | Кунжут и продукты его переработки | `SESAME` | Exact source/form |
| 7 | Люпин и продукты его переработки | `LUPIN` | Exact source/form |
| 8 | Моллюски и продукты их переработки | `MOLLUSCS` | Distinguish crustaceans |
| 9 | Молоко и продукты его переработки (включая лактозу) | `MILK` | Dairy protein allergy and lactose intolerance must not be conflated |
| 10 | Орехи и продукты их переработки | `TREE_NUTS_GROUP` | Species coverage / grouped flag does not prove every tree-nut species |
| 11 | Ракообразные и продукты их переработки | `CRUSTACEANS` | Distinguish molluscs |
| 12 | Рыба и продукты её переработки | `FISH` | Historical text specifically excepts certain fish gelatin use; applicability must be reviewed |
| 13 | Сельдерей и продукты его переработки | `CELERY` | Exact source/form |
| 14 | Соя и продукты её переработки | `SOY` | Processing and any legally applicable exceptions require per-version evidence |
| 15 | Яйца и продукты их переработки | `EGG` | Exact source/form |

**Candidate codes are not an approved taxonomy registry.** In particular, aspartame/sulfites/gluten/lactose involve different mechanisms; the product cannot present all 15 as equivalent clinical allergens. Do not import candidate codes into current `allergen_codes`, whose current validation merely enforces normalized strings, not taxonomy authority.

## 4. Proposed decision — semantic model, not implementation authorization

1. **Regulatory flags rather than medical diagnosis:** use `EAEU_TR_TS_022_2011_ART_4_4_P14` as a *candidate source taxonomy identity*, with explicit consolidated edition and verified effective date to be chosen after checking the official amendment chain. The 15 proposed codes are **not yet accepted** canonical identifiers; the 2026 draft is not an active taxonomy version.
2. **Do not collapse safety concepts:** distinguish (a) listed **ingredient/component origin** flags, (b) quantitative/context-dependent thresholds and legal exceptions, (c) possible manufacturing **cross-contact**, and (d) individual household exclusions. A regulatory list is not a complete clinical allergens universe; a list match cannot claim absolute safety.
3. **Classify exact identity + form:** each approved attestation would bind exact `FoodIngredient` ID/canonical code/name/form, source and edition; a different processing form, raw/cooked form, recipe, retailer SKU, or brand must not inherit a conclusion without evidence of applicability.
4. **Fail closed:** missing or ambiguous source/form/threshold/exception = `UNKNOWN` / unreviewed. A candidate with zero codes is **not** `REVIEWED_EMPTY_SET` without an independent attestation explicitly scoped to the adopted taxonomy. Do not treat `unknown` as `no listed components`.
5. **New ingestion:** new FoodIngredient identities enter the complete audit backlog as `UNKNOWN` until approved source- and form-specific review. Do not auto-publish codes from a name, category, code prefix, LLM, retailer snippet, or generated lookup.
6. **No direct current-state migration:** existing `FoodIngredient.allergens_reviewed` and `allergen_codes` are observations. Changing their meaning, seed reconciliation, schema, or composition admission requires the parent contract and the remaining authority gates.

## 5. Decisions / evidence still required for TAXONOMY GATE closure

| Gate item | Closure evidence required | Status |
| --- | --- | --- |
| Applicable edition | Official signed text + amendment chain through 2026-11-23 (and later recheck at implementation time), adoption/effective dates, exclusions | **OPEN** |
| Exact taxonomy definition | Approved code vocabulary and version, whether regulatory warning/contraindication flags share or split namespaces, full rules for conditional thresholds/exceptions | **OPEN** |
| Form/scope policy | Reviewable mapping protocol for raw vs processed forms, product-vs-recipe scope, generic vs packaged SKU, cross-contact and unknown handling | **OPEN** |
| Official source-byte verification | Durable artifact locator, bytes/size/SHA-256, independently verified retrieval date and re-verification rule | **OPEN** (also SOURCE/TRUST dependency) |
| Independent approval | Explicit owner/qualified reviewer decision with attached evidence and canonical ADR/annex | **OPEN** |

**OPEN QUESTION:** Should the first classification be strictly the 15 regulated labelling categories (and separate warnings), or include additional safety exclusion categories in a *different* versioned taxonomy? This is a product/safety decision, not an automatic consequence of regulation.

**OPEN QUESTION:** Does any officially effective amendment after the verified 2024 consolidation change §4.4 by 23 November 2026? The October order is a proposal only; an official consolidated decision inventory is still required.

## 6. Acceptance and adversarial review criteria for this research PR

- All 15 regulatory groups correctly represented, without claiming all are identical clinical allergens.
- Explicit treatment for phenylalanine, quantitative sulphite threshold, fish gelatin exception, lactose, ingredient-level vs finished-product claims, and cross-contact.
- Official original/document metadata linked, amendment proposal correctly labelled **NOT EFFECTIVE**, no invented effective date and no unverified source-byte SHA.
- No blanket food-code assignment, no exact `FoodIngredient` admissions, no `REVIEWED_EMPTY_SET` promotion, no rights/clinical authority claim.
- No runtime/schema/seed/API/Planner/Shopping/Prep change; `AI_ENABLED=false` unchanged.
- **Hard NO_RUNTIME:** merging this research document does **not** close TAXONOMY GATE until the open items above are separately evidenced and explicitly owner-approved; neither SOURCE/TRUST nor LEGACY ADMISSION is closed. No publisher/migration/admission implementation may start while *any* of the three remains open.

## 7. Recommended next decision (not automatically approved)

Independently verify the official effective consolidated regulatory text and source bytes, challenge the 15-code candidate classification (especially warnings, thresholds and exceptions), then obtain explicit owner approval of an exact regulatory taxonomy version and scope. If corrections are needed, update this proposal and record the approved decision in repository docs. **Only then** consider TAXONOMY GATE CLOSED; full runtime remains NO_GO until all parent-contract gates close.

**Review outcome requested:** accept the research evidence as a *proposed baseline* or return for corrections; **do not** treat this PR as an approval of code mappings or data publication.
