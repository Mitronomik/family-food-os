# PR4-DATA2 — corrected Russia/SPB technical recipe corpus

PR4-DATA2 — READY FOR REVIEW, not ACCEPTED or COMPLETE (`2026-09-05`).

Issue #12; existing branch `data/pr4-data2-russia-spb-recuration` and
[PR #13](https://github.com/Mitronomik/family-food-os/pull/13).
Exact base: `26af749be0f6446de1d88cad2e2e03158a9830a0` (merged governance #9,
historical PR4-DATA #8 and localization #11). This direction-consumables
correction begins at reviewed head `66a30403e3463248bb9b66e5a40920ef3fb136b5`.
The delivered head is recorded exactly in PR #13 after push, not as a
self-referential commit hash in its own contents.

Final: **30 recipes**, **28 retained / 2 replaced in this correction pass**;
relative to historical PR4: **3 retained / 27 replaced**. Both forbidden ICN
cards remain absent. **225 source-audit rows / 189 selected rows** (185 required,
3 source-explicit optional, 1 conditional); exact **81 existing FoodIngredient**
union within **80..120**, zero new codes and zero unresolved required rows.
**86 source-backed equipment rows / 34 normalized codes**.

Canonical PR4 meal types: **breakfast 3 / main 5 / side 5 / salad 6 /
sandwich 1 / other 10**. Separate curation roles: **BREAKFAST 3 / MAIN_DISH 5 /
SIDE_DISH 11 / SOUP 2 / DESSERT 3 / SNACK 4 / CONDIMENT 1 / SANDWICH 1**.
**8 meal anchors**, **3 soups/substantial one-bowl meals**, **11 pure sides**;
six primary-protein families: **DAIRY 1 / EGG 2 / FISH 2 / LEGUME_TOFU 1 /
MEAT 1 / POULTRY 1** among anchors.

All 30 actual sources were audited beyond ingredient lists: **281 consumable
audit rows**. At the reviewed head, **9 recipes / 19 direction-only edible
rows** included two required unquantified pan-release sprays. Honey Lime
Chicken and Local Harvest Bake were replaced, not silently edited. The final
corpus has **9 recipes / 24 direction-only edible rows**, all explicitly
resolved; **zero unresolved required direction consumables**. Process water
discarded after preparation is excluded from those direction-only edible
counts; selected retained water is not.

**83 non-water purchase forms: 3 RU_MASS_MARKET / 80 RU_AVAILABLE /
0 SPECIALTY_OR_UNCLEAR**. Chain coverage: **70 one-chain / 10 two-chain /
3 three-chain** forms. All five baseline chains assessed; Lenta concentration
remains a limitation. Matrix: **187 raw / 179 unique observations,
142 AVAILABLE / 37 UNCERTAIN** (includes rejected research).
Compatibility is not momentary store stock.

All final sources have nine reviewed consistency dimensions, including
direction-only consumables; missing that ninth dimension fails closed. Exact
artifacts/hashes, attribution and notices remain under the approved narrow
direct-FNS project risk posture, including the ONIE-attributed deviled eggs.
No unresolved selected-source rights blocker; no blanket public-domain or
unrestricted commercial/derivative rights claim.

Verification: final DATA2 validator **PASS**; focused DATA2 **164 passed in
3.40s**; historical PR4-DATA/FoodIngredient affected suite **82 passed in 1.71s**;
Ruff format **2 files already formatted**, Ruff check **All checks passed!**;
`git diff --check` **PASS**. Five final artifacts reproduce byte-for-byte from
reviewed source/form/consumable inputs. Final staged scope audit **PASS**: 24
authorized text files, no runtime/database/binary or unrelated files. Full runtime suite
and PR4 production seed execution are excluded from this isolated curation operation.

Historical `data/curation/pr4/`, global seeds (183 ingredients / 172 aliases /
183 profiles), PR4 runtime, migrations/API/frontend and local development DB
remain unchanged. PR #10 remains at `cd2285802c94735e0c9015042f9f4c0b52d68b85`;
it may consume DATA2 only after ACCEPT + merge. No RetailSKU/retailer production,
Nutrition, Pantry, Planner, Shopping, Auth/PostgreSQL or AI work. PR5 unauthorized.
Next action: project final review, not autonomous merge.

## Durable evidence and regeneration

- `source-consistency-audit.json`: independent reviewed facts for the final 30;
  name, servings, ingredient concepts, meal role, diversity, times, equipment,
  limitations and direction-only consumables. It is the human review input,
  not a generated copy of recipe-corpus.json.
- `direction-consumables-audit-a.json` and `direction-consumables-audit-b.json`:
  complete reviewed-head source audit, preserving the two rejected spray defects.
- `direction-consumables-audit.json`: final 30, 281 rows. Every selected food
  position is cross-linked to exact source quantity; optional/alternative
  decisions, discarded process water and non-food disposables remain explicit.
  Ingredient lists, numbered directions, preparation notes, footnotes,
  recipe-specific tips, alternative methods and supporting instructions are
  independently marked reviewed or not present/not used.
- `consumables-anchor-alternatives.json` and
  `consumables-replacement-candidates.json`: new source/hash/notice reviews,
  selected no-fat sandwich and deviled-egg method, and tested rejection reasons.
- `draft-ingredient-coverage.json`: 225 source rows including optional,
  alternative and process-water rows; 189 selected rows rebuild the CSV.
  No invented units, grams, yields, seasonings or cooking steps.
- `draft-purchase-form-review.json`: 83 actual non-water purchase concepts/forms,
  source matching, five-chain review and one-based observation references.
- `research-consumables-market.json`: newly checked whole-wheat bread and
  fresh cauliflower evidence; the earlier correction research remains auditable.
- `source-downloads.json`: 26 reviewed downloaded documents across research
  history, not a final-recipe count. No source images or binaries committed.
- Generated final outputs: `recipe-corpus.json`, `ingredient-coverage.csv`,
  `mvp0-food-ingredient-codes.txt`, `purchase-form-review.json`,
  `retailer-evidence-matrix.json`. `--final-corpus` and `--final-evidence`
  on `scripts/validate_pr4_data2.py` serialize them deterministically; the
  normal validator byte-compares them to reviewed inputs, without production seed.
- `pr4-meal-type-contract.json`: verbatim, hash-pinned PR #10 MealTypeCode AST
  excerpt plus full source-blob identity; compared with the reviewed Git object
  when available. No production import or enum expansion.
- `replacement-decisions.json`: historical slot decisions and exact keep/replace
  partitions for both correction passes. Fixture replacements are not
  nutrition-equivalent household substitutions.
- Earlier `correction-source-audit.json`, `correction-anchor-candidates.json`,
  `recipe-review-metadata.json` and equipment snapshots retain historical
  reviews; the final independent source/consumable audits control final metadata.

See [review-report.md](review-report.md) for all 30 recipe summaries,
replacements, anchors, source collections, direction-only food resolutions,
equipment codes, limitations and one-chain forms. Mechanical validators cannot
prove an invented human review; actual primary sources and hashes remain essential.

## Market and rights boundaries

The [clarified market method](market-methodology.md) is unchanged. The historical
96 source-text risk rows remain classified as 77 PURCHASE_FORM_CRITICAL and
19 PREPARATION_ONLY_OR_NOT_RETAIL_FORM. Cutting/mincing are preparation, not new
retail products; canned/dry, required frozen/fresh, sodium and dairy-fat forms
remain material. Official neutral catalogues plus official SPB/LO chain presence,
or indexed current official pages, qualify. Wrong-city pages, expired flyers
and wrong forms do not. Browser blocks are not product absence.

Direct-FNS hosting is the accepted bounded project risk posture, not evidence
that all contributors are government employees or that commercial reuse is
unrestricted. Attribution includes ONIE Project, universities/extension and
NVCSS. Team Nutrition's copying statement is not an unlimited commercial grant.
No photos, logos or nutrition panels are imported. Absence of a restrictive
notice is not itself an affirmative rights grant.

## Source corrections and limits

Honey Lime Chicken and Local Harvest Bake cannot be retained by inventing a
spray quantity or assuming grease is optional. The new WIC sandwich instead
uses an explicit source nonstick/no-butter method; its oil method is not selected.
Heavenly Deviled Eggs uses the source's exact 1/8 tsp each salt/pepper alternative
to mustard. Neither recipe needs new FoodIngredient codes. Deviled eggs is a
snack, not an inflated anchor; the sandwich is the replacement anchor.

Apple Carrot Soup contains pork. Spanish Frittata's breakfast occasion is curator
metadata, not an invented source statement, and its yield/time tension remains.
The spinach/cauliflower smoothie says exactly `1 cup milk`; selected 1% is a
reviewed member of generic milk. Overnight Oats' named apple/cinnamon/yogurt
choices are selected optional foods. Extra liquid, alternate toppings, serving
suggestions and variant-specific saute oil have explicit source-backed decisions,
not silent deletions. Repeated selected food uses are not double-counted.

Cooked pasta remains cooked volume; juice keeps its source quantity without
invented yields. Null times remain unknown. Process water is not silently added
to consumed mass; conditional retained saute water is selected as quantified.
Measured fish-coating butter is not additional spray. Equipment must be explicitly
named and operationally used; the WIC nonstick pan and egg-piping zipper bag are
source-backed, not inferred. This is a diverse technical fixture, not a
nutrition-certified, taste-tested or nutritionally balanced weekly plan.

## Historical correction context

The earlier four-blocker review at `36c0cb82680fbc8a57ab4a78a41f363f3420d39d`
exposed Local Harvest's false pork/main claim, incompatible meal vocabulary,
side-heavy selection and the below-floor union. The correction delivered at
`66a30403e3463248bb9b66e5a40920ef3fb136b5` replaced five recipes and introduced
source-backed role/protein, pinned PR4 vocabulary and diversity/80..120 guards.
That was not acceptance: the later consumables review found required spray
outside ingredient lists. Its prior corpus/equipment/market aggregates are
superseded by the final counts above. Local Harvest is historically a vegetable
side, never a pork main, and is now absent for the separate spray-quantity defect.
The original `data/curation/pr4/` evidence remains immutable.
