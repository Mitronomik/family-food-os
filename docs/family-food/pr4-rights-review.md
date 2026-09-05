# PR4 correction pass — rights blocker

Reviewed: `2026-09-05`. Applies to PR [#10](https://github.com/Mitronomik/family-food-os/pull/10).
This is a research/acceptance record, not a legal opinion or a new licence.

## FACT

The accepted corpus contains 28 direct USDA FNS-hosted CACFP six-serving cards
and two ICN-hosted USDA Standardized Recipes Project 2024 six-serving cards.
Exact URLs and document hashes remain in
`data/curation/pr4/recipe-corpus.json` and
`data/seed/recipes/source-manifest.json`. No recipe has been replaced.

Primary evidence examined:

| Source / collection | Evidence | Supported conclusion and limit |
| --- | --- | --- |
| FNS CACFP Home Childcare: Breakfasts (3), Main Dishes (8), Side Dishes (11), Salads (3), Sandwiches (3) | [USDA Policies and Links, Digital Rights and Copyright / Links to Other Sites](https://www.usda.gov/about-usda/policies-and-links) | USDA describes most website information as public domain and permits copying/distribution of public-domain information, requesting attribution. It expressly allows exceptions for protected or personal-use material and requires examining external sites' terms. This qualified department-wide statement does not identify these 28 cards as federal-employee works or establish source-specific commercial derivative clearance. |
| ICN-hosted USDA Standardized Recipes Project 2024 (2) | [ICN Copy and Use Policy](https://theicn.org/icn-copy-and-use-policy/) | Free downloading and educational copying are permitted subject to conditions, including no printing for resale and retention of ICN/USDA identifiers. The reviewed grant does not establish commercial application/database redistribution or derivative rights. This is an evidence gap, not a determination that all such uses are forbidden. |

The official ICN [Vegetable Frittata Bites page](https://theicn.org/cnrb/recipes-for-homes/recipes-for-homes-main-dishes/vegetable-frittata-bites-usda-recipe-for-family-child-care-homes/)
and [Cauliflower Rice page](https://theicn.org/cnrb/recipes-for-homes/cauliflower-rice-usda-recipe-for-family-child-care-homes/)
identify the 2024 project and link the exact six-serving PDFs in the frozen
manifest. No recipe-specific commercial/derivative grant was found on these
pages. A generic site footer is not treated as ownership evidence for a card.

FNS recipe/policy page retrieval attempts failed in the research browser;
the USDA department policy above was readable. Searches for recipe-specific
permissions did not establish an additional applicable grant. This review
does not claim exhaustive discovery or that no permission exists elsewhere.
Policies on unrelated ICN publications were not applied to these cards.

The previous ARS evidence does not establish source authorship. USDA branding,
government hosting, free download, and absence of a third-party notice are not
substitutes for the missing evidence. The existing `REVIEWED` and
`SOURCE_VERIFIED` JSON flags are disputed implementation assertions, not
accepted rights clearance. Do not publish this seed as rights-cleared.

## Exact affected recipes

All six manifest collections remain uncleared for the intended reuse in this
review. Names below map one-to-one to the frozen source IDs and URLs.

- FNS Breakfasts (3): Southwest Tofu Scramble; Spiced Oatmeal; Strawberry
  Smoothie Bowl.
- FNS Main Dishes (8): Chicken Fajita; Honey Lime Chicken; Rice Vegetable
  Casserole; Vegetable Chili; Vegetable Frittata; Quiche with Self-Forming
  Crust; Ropa Vieja; Bean Burrito Bowl.
- FNS Side Dishes (11): Baked Sweet Potatoes and Apples; Corn and Edamame Blend;
  Local Harvest Bake; Orange Glazed Carrots; Pizza Green Beans; Sautéed Spinach
  and Tomatoes; Spanish Rice; Tabbouleh; Corn Pudding; Creamy Coleslaw; Green
  Beans with Potatoes and Smoked Turkey.
- FNS Salads (3): Carrot Raisin Salad; Macaroni Salad; Marinated Black Bean Salad.
- FNS Sandwiches (3): Tuna Salad Sandwich; Tuscan Grill Cheese Sandwich; Asian
  Tuna Burger.
- ICN 2024 (2): Vegetable Frittata Bites
  (`CACFP6-VEGETABLE-FRITTATA-BITES`); Cauliflower Rice
  (`CACFP6-CAULIFLOWER-RICE`).

## BLOCKER

Outcome B of the correction request applies: the current 30-card corpus cannot
be defensibly cleared using the evidence obtained. The two ICN cards alone
prevent complete clearance; the 28 FNS cards also lack the required specific
evidence. Implementation stopped before changing loader rights validation,
manifest flags/bases, generator, equipment or tests. The hard-coded ARS URL and
zero equipment remain known defects, not accepted outcomes.

## OPTIONS

1. Obtain source/collection-specific written clearance from the responsible
   FNS/ICN rights holders, identifying the exact cards and covering public
   repository/app redistribution, normalized structured data, retained or
   adapted directions, derivatives and commercial use. Clarify attribution
   and separate images/logos/third-party exclusions.
2. Make an explicit project decision to replace uncleared sources with a
   demonstrably reusable corpus, then repeat coverage and source review.
   No replacement is authorized by this record.

## RECOMMENDED DECISION

Preserve the accepted corpus and seek written clearance under option 1 before
resuming implementation. No permission request has been sent. An authorized
rights decision and supporting evidence are required; do not weaken the rights
gate or relabel the existing assertions as a successful review.

## Synchronization and verification boundary

- Original PR4 base: `704c588387a28e18ac1aa947ded398f168875ea0`.
- Reviewed implementation head: `e3b31e9ef5e7ad30c252cb59a9edac8056efbe74`.
- Fetched main: `4a8b0a20f7793b890efa37741f035eb120909bc7`, including governance
  PR #9. The merged workflow was read before merging.
- Clean non-rewriting merge: `ac28dd4a3e972d943c53bd8d61cc6892dfb2e24b`.
  No conflicts; only governance documents arrived from main.
- This correction adds documentation only after that merge. The commit
  containing this record is the blocker-report head; its exact SHA is recorded
  in PR #10 and the final agent report, avoiding a self-referential commit SHA.
- Read-only JSON recount: 30 Recipes / 30 v1 payloads / 365 ingredient lines /
  315 steps / 0 equipment rows; 119 distinct ingredient codes. Equipment codes:
  none. No ingredients, steps, source identities or quantities were changed.
- Seed twice, focused PR4, FoodIngredient regressions and full backend/launcher
  regression were not rerun: Outcome B stopped the correction before runtime
  changes or corrected seed acceptance. Earlier `80 passed` / `2819 passed`
  and seed-run results are historical, not evidence of this correction passing.
- Ruff format/check: N/A; no Python files changed in the synchronization or
  blocker report. Diff checks and staged-scope audit are recorded at handoff.
- The ignored stale `.local/family_food.sqlite` is untouched and excluded.
- Lifecycle label remains **PR4 — READY FOR REVIEW** as requested, with
  **CHANGES REQUIRED / RIGHTS BLOCKED** as the review result. This is not final
  acceptance or COMPLETE. PR5 remains unauthorized; PR #10 must not be merged.
