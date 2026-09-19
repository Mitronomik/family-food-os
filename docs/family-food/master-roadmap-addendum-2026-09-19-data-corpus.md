# FamilyFoodOS — Master Roadmap Addendum, 2026-09-19 — DATA-CORPUS-V1

**Status:** canonical addendum to `master-roadmap.md` and later addenda
**Authority:** explicit user-approved product/data sequencing decision on 2026-09-19
**Execution issue:** #67 — `DATA-CORPUS-V1 — reusable authoritative food and recipe corpus`

## 1. Purpose

This addendum changes the sequencing of catalogue data work.

The user explicitly decided that FamilyFoodOS should not create food/nutrition
truth only to make Gate1 pass. The project will first establish a reusable
production-quality food + recipe corpus needed by the service itself, and Gate1
and later gates will consume subsets of that ordinary corpus.

The canonical data contract is:

[data-corpus-v1.md](data-corpus-v1.md).

## 2. What is superseded

The following current Gate1-only strategy is superseded:

- publish only the smallest specially selected eight-recipe Russian subset;
- add only the exact food/profile gaps needed by those eight recipes;
- treat broad catalogue work as out of scope solely because Gate1 needs fewer
  records.

Issue #64 and PR #66 remain historical evidence. Their minimal-eight strategy is
no longer the active data-sequencing contract.

PR #66 must not merge in its current form. Reusable fixture/provenance mechanics
may be recovered later after catalogue truth comes from accepted DATA-CORPUS-V1
publication batches.

## 3. What is not changed

This decision does not change the core architecture.

Still true:

- `FoodIngredient` is the sole canonical food identity;
- external datasets are replaceable bootstrap/evidence artifacts;
- Nutrition/Composition remain deterministic and versioned;
- raw/input/cooked food forms and masses are not interchangeable;
- unknown != zero;
- production recipes require provenance;
- AI is not authoritative data;
- Retail remains separate from generic food truth;
- no direct Planner dependency on an external dataset/source;
- current synchronous SQLAlchemy Core / project UoW / SQLite migration authority
  remain unchanged;
- migration `0033_recipe_template_catalogue` remains reserved;
- Gate1-CLOSE remains a separate review;
- PR9 remains NOT STARTED until Gate1-CLOSE.

## 4. DATA-CORPUS-V1 is a foundation program, not the later full Data Ingestion Platform

The existing roadmap intentionally deferred the generalized Data Ingestion
Platform. That remains correct.

DATA-CORPUS-V1 may use:

- controlled source snapshots;
- source-specific acquisition/extraction;
- curated CSV/XLSX/JSON;
- deterministic curation scripts;
- bounded internal import/data-upgrade jobs;
- validation/audit tooling;
- small production data publication PRs.

This does not authorize:

- arbitrary user URL/file ingestion;
- generalized crawling platform;
- review-queue product UI;
- retailer ingestion;
- continuous multi-source synchronization;
- AI-driven publication.

The later Data Program may automate maintenance of the accepted corpus without
redefining canonical product models.

## 5. New sequence before Gate1-CLOSE

The active sequence is now:

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         COMPLETE
→ PR7 MealPlan / Serving                     COMPLETE
→ PR8 Planner v0                             COMPLETE
→ Gate1-A audit/readiness baseline           COMPLETE
→ DATA-CORPUS-V1 / DC0 contract              ACTIVE
→ DC1 source authority + coverage inventory
→ DC2 food publication batches
→ DC3 recipe publication batches
→ DC4 corpus readiness audit + Gate1 consumption
→ GATE1-CLOSE — Planning Core
→ PR9 Shopping Engine
```

The earlier Gate1-A-E1 / minimal production repair sequence is superseded by this
program.

## 6. Baseline corpus outcome

The DATA-CORPUS-V1 baseline aims to provide:

- `50–80+` verified usable RecipeVersions;
- `100%` required FoodIngredient resolution across the active recipe corpus;
- authoritative production nutrition provenance for every required food/profile;
- realistic weekly variety;
- Russian display readiness;
- a FoodIngredient catalogue intentionally progressing toward the broader
  `250–350` MVP target.

Acceptance is coverage-first. The project must not add weak or unused foods only
to hit a number.

The `250–350` target remains the broader MVP catalogue direction. The active
corpus must be fully covered before gate consumption.

## 7. Source authority direction

For Russian-specific food composition, FGBUN/FIC Nutrition and Biotechnology
material is a preferred authority candidate when exact form/basis/version and
retained-use scope are reviewable.

The 2024 FIC reference/database is **not** treated as an automatically open
bulk-copy dataset. Bulk retention requires an explicit rights/use decision.

Official open datasets with clear reuse terms may provide scalable baseline
authority where exact semantics match. USDA FoodData Central is an accepted
candidate because it publishes its data as public domain / CC0.

Retailer pages and mirrors remain corroboration/discovery by default, not generic
production nutrition authority.

## 8. Gate1 relationship

Gate1 remains a product proof, not a corpus-size proof.

After DC4, Gate1 must select its recipe capacity from ordinary accepted production
catalogue truth.

Required Gate1 behavior remains:

- three materially different repository-backed fixture households;
- complete required week or explicit bounded infeasibility;
- individualized Servings;
- exclusions;
- deterministic trace/replay;
- current Planner constraints;
- no hidden estimate promotion.

The corpus may contain far more than the minimum Gate1 fixture set.

## 9. Gate2 and later relationship

Gate2, Shopping, Pantry, Prep and consumer flows should reuse the same canonical
FoodIngredient/RecipeVersion data.

No gate should create a parallel authoritative catalogue merely to satisfy its
fixture.

RetailSKU/price/availability remain later enrichment over FoodIngredient and do
not belong to DATA-CORPUS-V1.

## 10. Delivery discipline

DATA-CORPUS-V1 is delivered through small PRs:

- DC0 — docs/governance only;
- DC1 — curation/evidence only;
- DC2 — food publication batches;
- DC3 — recipe publication batches;
- DC4 — readiness/gate-consumption proof.

No single PR should import the whole catalogue.

If a publication batch reveals a genuine schema limitation, stop for a separate
architecture/migration decision before using a new migration number.

## 11. Relationship to existing Data Readiness wording

The roadmap statement that full ingestion automation must not block Planning/Core
remains true.

The user has nevertheless chosen to invest in reusable Data Readiness **earlier**
because the same authoritative corpus is needed by the product beyond Gate1.

This is a sequencing/product decision, not a claim that automation is required
for Gate1.

## 12. Stop rule

DC0 establishes the contract only.

After DC0 review/merge, the next authorized work is DC1 under Issue #67.

Do not start DC2 production publication, Gate1-CLOSE, PR9, Retail, AI or
Auth/PostgreSQL merely because the contract exists.
