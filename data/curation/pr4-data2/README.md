# PR4-DATA2 — corrected Russia/SPB technical recipe corpus

PR4-DATA2 — READY FOR REVIEW, not ACCEPTED or COMPLETE (`2026-09-05`).

Issue #12; existing branch `data/pr4-data2-russia-spb-recuration` and
[PR #13](https://github.com/Mitronomik/family-food-os/pull/13).
Exact base: `26af749be0f6446de1d88cad2e2e03158a9830a0` (merged governance #9,
historical PR4-DATA #8 and localization #11). Correction begins at reviewed head
`36c0cb82680fbc8a57ab4a78a41f363f3420d39d`; delivered head is the current branch
HEAD, recorded exactly in PR #13 after push, not a self-referential commit hash.

Final: **30 recipes**, **25 retained / 5 replaced in this correction pass**;
relative to historical PR4: **5 retained / 25 replaced**. Both forbidden ICN
cards are absent. **226 source-audit rows / 195 selected rows** (190 required,
4 source-explicit optional, 1 conditional); exact **82 existing FoodIngredient**
union within **80..120**, zero new codes and zero unresolved required rows.
**88 source-backed equipment rows / 32 normalized codes**.

Canonical PR4 meal types: **breakfast 3 / main 6 / side 6 / salad 6 /
sandwich 0 / other 9**. Separate curation roles: **BREAKFAST 3 / MAIN_DISH 6 /
SIDE_DISH 12 / SOUP 2 / DESSERT 3 / SNACK 3 / CONDIMENT 1**.
**8 meal anchors**, **3 soups/substantial one-bowl meals**, **12 pure sides**;
five primary-protein families: **EGG 2 / FISH 2 / LEGUME_TOFU 1 / MEAT 1 /
POULTRY 2** among anchors. Local Harvest is a vegetable side, never a pork main.

**85 non-water purchase forms: 3 RU_MASS_MARKET / 82 RU_AVAILABLE /
0 SPECIALTY_OR_UNCLEAR**. Chain coverage: 71 one-chain, 11 two-chain,
3 three-chain forms. All five baseline chains assessed; Lenta concentration
remains a limitation. Matrix: 185 raw / 177 unique observations, 140 AVAILABLE /
37 UNCERTAIN (includes rejected research). Compatibility is not momentary stock.

All final sources re-audited for name, servings, ingredient concepts, meal role,
diversity, times, equipment and limitations. Exact artifacts/hashes, attribution
and notices retained under the approved narrow direct-FNS project risk posture.
No unresolved selected-source rights blocker; no blanket public-domain or
unrestricted commercial/derivative rights claim.

Verification: final DATA2 validator **PASS**; focused DATA2 **104 passed in 2.54s**;
historical PR4-DATA/FoodIngredient affected suite **82 passed in 2.43s**;
Ruff format **2 files already formatted**, Ruff check **All checks passed!**;
`git diff --check` and staged scope audit **PASS**. Five final artifacts reproduce
byte-for-byte from reviewed source/form inputs. Full runtime suite and PR4
production seed execution are excluded from this isolated curation operation.

Historical `data/curation/pr4/`, global seeds (183 ingredients / 172 aliases /
183 profiles), PR4 runtime, migrations/API/frontend and local development DB
remain unchanged. PR #10 remains at `cd2285802c94735e0c9015042f9f4c0b52d68b85`;
it may consume DATA2 only after ACCEPT + merge. No RetailSKU/retailer production,
Nutrition, Pantry, Planner, Shopping, Auth/PostgreSQL or AI work. PR5 unauthorized.
Next action: project final review, not autonomous merge.

## Durable evidence and regeneration

- `source-consistency-audit.json`: independent reviewed facts for the final 30;
  contains exact source times, role rationale, selection limitations, notices,
  attribution and ordered explicit equipment. This is the human review input,
  not a generated copy of recipe-corpus.json.
- `correction-source-audit.json`: adversarial source audit of all reviewed-head
  30, including the five now removed; `correction-anchor-candidates.json` holds
  five new actual-source reviews and rejected candidate reasons.
- `draft-ingredient-coverage.json`: 226 source rows, including source-explicit
  optional/alternative omissions and discarded process water; no invented units,
  grams, yields, seasonings or cooking steps. Selected rows rebuild the CSV.
- `draft-purchase-form-review.json`: 85 actual purchase concepts/forms, exact
  source matching, five-chain review and one-based observation references.
- `research-correction-market.json`: new primary retailer/form/region evidence,
  excluded wrong forms/cities and independent new-source notice/hash review.
- `source-downloads.json`: 24 reviewed downloaded documents across research
  history; not a final-recipe count. Retained five card hashes also appear in
  `source-equipment-audit.json`. No source images or binaries are committed.
- Generated final outputs: `recipe-corpus.json`, `ingredient-coverage.csv`,
  `mvp0-food-ingredient-codes.txt`, `purchase-form-review.json`,
  `retailer-evidence-matrix.json`. `--final-corpus` and `--final-evidence` on
  `scripts/validate_pr4_data2.py` serialize these deterministically; the normal
  validator byte-compares them to reviewed inputs. It never runs production seed.
- `pr4-meal-type-contract.json`: verbatim, hash-pinned PR #10 MealTypeCode AST
  excerpt plus full source-blob identity; compared to the reviewed Git object
  when available. No production import or enum expansion.
- `replacement-decisions.json`: all historical slot decisions plus the exact
  correction-pass keep/replacement partition and reasons. Slot replacements are
  fixture selection, not nutrition-equivalent household substitutions.
- Older candidate reviews and `recipe-review-metadata.json` are historical
  review snapshots, not current final metadata. The final independent source
  audit takes precedence; historical `data/curation/pr4/` is untouched.

See [review-report.md](review-report.md) for derived per-recipe counts, all
replacements, anchors, source collections, limitations, equipment codes and
one-chain forms. Structural tests cannot prove an invented human review; actual
primary sources and hashes remain necessary review evidence.

## Market and rights boundaries

The [clarified market method](market-methodology.md) is unchanged. All historical
96 source-text risk rows remain classified as 77 PURCHASE_FORM_CRITICAL and
19 PREPARATION_ONLY_OR_NOT_RETAIL_FORM. Cutting/mincing are preparation, not new
retail products; canned/dry, required frozen/fresh, sodium and dairy-fat forms
remain material. Official neutral catalogue evidence plus official SPB/LO chain
presence, or current indexed official pages, qualifies. Wrong-city pages,
expired flyers and wrong forms do not. Browser blocks are not product absence.

Direct-FNS sources are reviewed under the already-approved project risk
classification, not treated as federally authored solely because of hosting.
Third-party contributor attributions are retained, including university/extension
and NVCSS sources. Team Nutrition's copying statement is not expanded into an
unlimited commercial grant. No photographs, logos or nutrition panels imported.

## Source corrections and limits

Local Harvest now has only vegetable-side claims. Apple Carrot Soup correctly
discloses pork. Corn pancakes were removed instead of relabelled as breakfast.
Spanish Frittata is a substantial egg/potato entree; breakfast is a curator
occasion, not an invented source statement. Its source yield/time tension stays
visible. WIC smoothie source says exactly `1 cup milk`; selected 1% is a reviewed
member of generic milk. Overnight Oats' named apple/cinnamon/yogurt options are
selected optional rows, not falsely required foods. Simple Green Smoothie uses
the source-explicit single frozen-fruit choice, frozen strawberry, and is a
snack, not an anchor. Optional dash seasonings in Orange Pork Chops are omitted.

Cooked pasta remains cooked volume; prepared juice keeps its source volume,
without invented raw yields. Null times stay unknown. Measured coating butter
is not an invented spray quantity. Equipment must be explicitly named and used
operationally; a plate explicitly used to invert the frittata is included, but
serving-only utensils and inferred tools are not. Every other source limitation
is preserved in the final audit and report. This is a diverse technical fixture,
not a nutrition-certified, taste-tested or nutritionally balanced weekly plan.
