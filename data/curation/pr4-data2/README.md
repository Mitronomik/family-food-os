# PR4-DATA2 — Russia/SPB technical recipe corpus

Status: **READY FOR REVIEW**, not ACCEPTED or COMPLETE.
Reviewed: `2026-09-05`.
[Issue #12](https://github.com/Mitronomik/family-food-os/issues/12) ·
[existing PR #13](https://github.com/Mitronomik/family-food-os/pull/13).
Branch: `data/pr4-data2-russia-spb-recuration`.
Exact starting main: `26af749be0f6446de1d88cad2e2e03158a9830a0`.
PR #9 governance and PR #11 localization policy are included in that base.

This directory now contains an explicitly versioned successor to
`data/curation/pr4/`. The historical corpus remains byte-unchanged.
The initial regional-browser blocker is **superseded** by the
[Orchestrator clarification](https://github.com/Mitronomik/family-food-os/issues/12#issuecomment-5550629546).
Market compatibility is representation in ordinary SPB/LO retail, not an
assertion of momentary store stock.

Do not consume this successor in PR #10 until DATA2 receives ACCEPT and is
merged. No production Recipe, RecipeVersion, RecipeIngredient or equipment
rows are created by this operation. PR5 remains unauthorized.

## Exact result

| Measure | Result |
| --- | ---: |
| Final recipes | 30 |
| Original sources retained / replaced | 5 / 25 |
| Mandatory-excluded ICN cards in successor | 0 |
| Complete source audit rows, including unselected alternatives/optional notes | 223 |
| Selected ingredient-coverage rows | 193 |
| Selected required / optional / conditional rows | 191 / 1 / 1 |
| Exact selected global FoodIngredient union | 79 (limit 120) |
| New FoodIngredients / unresolved required code rows | 0 / 0 |
| Existing global catalogue / aliases / nutrition profiles | 183 / 172 / 183, unchanged |
| Reviewed non-water purchase forms | 82 |
| Purchase forms RU_MASS_MARKET / RU_AVAILABLE / SPECIALTY_OR_UNCLEAR | 3 / 79 / 0 |
| Source-backed equipment rows / unique normalized equipment codes | 96 / 33 |

Counts are curation evidence, **not PR4 runtime seed counts**. The old fixture
remains 30 sources / 363 coverage rows / 119 codes. No old evidence was silently
overwritten. Both ICN sources are absent from the successor:
`CACFP6-VEGETABLE-FRITTATA-BITES` and `CACFP6-CAULIFLOWER-RICE`.

The final descriptive meal grouping is 4 mains, 3 breakfasts, 2 soups,
15 sides, 3 desserts, 2 snacks and 1 condiment. It includes pork, poultry, fish,
eggs, grains, leafy/root vegetables and fruit, with skillet, oven, microwave,
rice-cooker, simmering, blending and uncooked methods. These categories are
curatorial judgments, not nutrition certification. This is a technical slice,
not a balanced weekly plan, a taste-tested menu or a launch-size catalogue.

## Durable evidence and how to consume it

- `recipe-corpus.json`: final 30 source IDs, URLs, names, servings, document
  hashes, narrow reviewed rights bases, equipment order/evidence, source times,
  meal/diversity assessments, selection decisions and per-recipe market counts.
- `ingredient-coverage.csv`: all 193 **selected** ingredient rows, retaining
  source wording and existing codes; no invented grams or yield conversions.
- `draft-ingredient-coverage.json`: despite its historical filename, the
  frozen source audit behind the final CSV. It retains all 223 source rows,
  including omitted optional choices, alternatives, preparation aids and source
  limitations. The validator rebuilds the CSV from these explicit selections.
- `mvp0-food-ingredient-codes.txt`: exact sorted 79-code selected union.
- `purchase-form-review.json`: one reviewed record per selected CSV food row,
  joined to the actual source purchase form and a full five-chain assessment.
- `draft-purchase-form-review.json`: reviewed human form-matching inputs,
  preserving exact chosen members, applicability and evidence references.
- `retailer-evidence-matrix.json`: deduplicated research observations plus
  final source forms; raw IDs remain aliases for audit. Research observations
  are not blanket clearance of all recipes sharing a canonical code.
- `replacement-decisions.json` and [review-report.md](review-report.md):
  all 25 slot replacements, reasons, complete 30-recipe summary and exact
  one-retailer-only forms. A slot replacement is not a nutrition-equivalent
  household substitution.
- `source-downloads.json`: 19 downloaded new-source documents covering all
  25 new recipes. Retained five PDF hashes are in `source-equipment-audit.json`.
  PDF/HTML artifacts were reviewed locally; no source binaries/images are
  committed. Browser-saved HTML hashes identify the saved artifact, not a
  claimed byte-identical upstream HTTP response.
- `recipe-review-metadata.json`: reviewed metadata for all 25 new sources.
  `source-equipment-audit.json` preserves the complete historical 30-card audit.
- `research-candidates.json`, `original-corpus-market-review.json`,
  `candidate-review-v2.json` through `v5` and retailer research files preserve
  exact historical source facts, unsuccessful candidates and excluded matches.

## Market method and limitations

Read [market-methodology.md](market-methodology.md).
All 96 historical source-text/form-risk rows were preserved and reclassified:
77 PURCHASE_FORM_CRITICAL, 19 PREPARATION_ONLY_OR_NOT_RETAIL_FORM.
The complete original 30-card / 363-row audit is broader than those 96 flags.
After source-specific updates, 6 original cards have complete market evidence,
but one is mandatory-excluded ICN; only 5 are eligible keepers.

Current official neutral product/category pages qualify with current official
SPB/LO chain presence; indexed official product wording qualifies when the live
page is unavailable. Explicitly other-city pages, expired flyers and wrong forms
do not qualify. Slicing/mincing/peeling are not new retail products. Canned/dry,
specified dairy fat, sodium restrictions, frozen/fresh when required and other
material forms remain separately reviewed. No CAPTCHA or TLS control was bypassed.

Evidence totals are 172 raw observations, 166 unique code/chain/URL records,
129 AVAILABLE and 37 UNCERTAIN; six duplicate aliases are retained.
AVAILABLE unique observations by panel chain: Пятёрочка 3, Перекрёсток 0,
Лента 113, О'КЕЙ 0, Магнит 13. Zero qualifying observations is **not absence**.
These totals include rejected-candidate research, not just final ingredients.

The final 82 forms have 72 one-chain, 7 two-chain and 3 three-chain reviews.
The exact one-chain forms are listed in the review report. Evidence concentration
in Lenta is a limitation: RU_AVAILABLE is not relabelled RU_MASS_MARKET.
All five chains were assessed; no final form relies on a specialist-only seller.
No prices, stock counts, fake SKU IDs, retailer connector or runtime dependency
were introduced. Later Retail must refresh evidence.

Examples of reviewable primary evidence are the
[Lenta SPB-serving vegetable catalogue](https://lenta.com/catalog/ovoshchi-146/),
[X5 delivery presence](https://rabota.x5.ru/dostavka/rabota-v-x5/) and
[Magnit SPB oat listing](https://magnit.ru/product/1000142900-khlopya_ovsyanye_magnit_ekstra_400g?shopCode=784430&shopType=1).
Exact product/form matches and dates, not these presence pages alone, determine
each classification.

## Rights/provenance result

All selected sources are directly FNS-hosted documents reviewed under the
**already-approved project risk posture**, with attribution and document hashes.
This is not a declaration that USDA branding or a government host proves public
domain, nor an assertion of unrestricted commercial/derivative licensing.

- Retained CACFP: 5 cards, exact card evidence and notice review.
- Team Nutrition Cooks!: 3 handouts; collection explicitly permits downloading
  and copying, without expanding that wording to an unlimited commercial grant.
- FNS-430 Harvest: 3 recipes; collection PDF and acknowledgments reviewed.
- WIC Works: 4 recipes; exact page and contributor/notice review.
- SNAP-Ed seasonal recipes: 13; each actual recipe section reviewed.
- SNAP-Ed educator card: 1; Montana State attribution preserved.
- FNS Food and Physical Activity Checklist: 1; actual original PDF reviewed.

No selected card carries an uncleared third-party restrictive notice found in
the reviewed document. No unresolved selected-source rights blocker remains.
Rejected ICN, inaccessible-origin and other unsuitable candidates remain
research only. No photos, logos, trademarks or source marketing prose are
imported as product assets.

## Source-quality and normalization boundaries

- Keep cooked macaroni volume as cooked volume, never the same amount of dry
  pasta. No unreviewed dry/cooked yield is created.
- Spinach/apple salad retains literal `2/3 package (10 ounces)`; DATA2 does not
  manufacture a package-to-gram conversion.
- Braised chicken lists quantified salt/pepper but omits their application in
  its directions. This source omission is explicitly preserved, not patched
  with an invented step.
- TNC pancake supplementary guidance permits extra oil only if needed, without
  a quantity; no additional mandatory ingredient or invented quantity is added.
- The standard roasted-carrot variant permits generic vegetable oil; selected
  olive oil is a member of that category, not a mandatory spicy-variant rule.
- Explicit source options and optional omissions are recorded. Required
  unquantified seasonings caused other candidates to be rejected.
- Equipment is explicit-source evidence. Corn/edamame uses the source's
  raw-sesame toasting alternative, so STOCK_POT is included. Serving-only
  utensils and disposable paper/foil are excluded. No tool is inferred merely
  from a chopping, mixing or grilling verb.
- Null source times remain unknown. Stage times are not silently summed into
  an invented active/preparation/total duration.

These limitations are visible handback requirements for later PR4 normalization,
not unresolved FoodIngredient codes or permission to invent production truth.

## Verification

`backend/.venv/bin/python scripts/validate_pr4_data2.py` checks the final
successor as well as research integrity. `--research` alone is not acceptance.
The validator rebuilds the selected coverage, exact union and form review
deterministically, validates reference/schema integrity and rejects missing
final artifacts. Offline tests cannot establish the truth of a fabricated
human review; primary-source evidence remains reviewable.

Exact final test/Ruff/diff results are recorded in [review-report.md](review-report.md)
and PR #13. Affected historical PR4-DATA/FoodIngredient regression was rerun:
**82 passed in 1.77s**. Full backend/launcher, seed execution and runtime
immutability suites are not run: issue #12 explicitly excludes a full runtime
suite for this isolated supporting curation operation. Existing seed tests
remain part of the affected regression above.

Scope: only DATA2 data/research, its offline validator/tests and execution state.
No global seed, historical fixture, PR4 runtime, migration, API, frontend,
nutrition, pantry, planner, shopping, retail production, Auth/PostgreSQL or AI
change. Ignored local development database is untouched. PR #10 is unchanged.
