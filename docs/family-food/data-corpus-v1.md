# FamilyFoodOS — DATA-CORPUS-V1 Contract

**Status:** canonical data-corpus contract
**Decision date:** 2026-09-19
**Authority:** later explicit user-approved product/data decision
**Execution issue:** #67 — `DATA-CORPUS-V1 — reusable authoritative food and recipe corpus`

## 1. Purpose

FamilyFoodOS will not build data only to satisfy an individual delivery gate.

The service needs a reusable authoritative food and recipe corpus for its ordinary
runtime. Gate fixtures consume verified subsets of that corpus.

The direction is:

```text
authoritative food sources
→ FoodIngredient / Nutrition / NutrientVector / Composition
→ authoritative recipe source corpus
→ ingredient resolution
→ deterministic recipe nutrition
→ published RecipeVersion catalogue
→ Planner / Shopping / Prep / consumer gates
```

The corpus is platform data. It is not Household-owned data and it is not a
special Gate1 fixture dataset.

## 2. Relationship to existing architecture

This contract does **not** create a new domain model.

Existing canonical concepts remain authoritative:

- `FoodIngredient` is the sole platform food identity;
- `FoodNutritionProfile` / NutrientVector own direct nutrition truth under the
  current Nutrition contract;
- Composition owns reusable exact food composition when applicable;
- Recipe source-corpus records preserve source truth;
- `RecipeVersion` owns published immutable recipe truth;
- Planner consumes published canonical truth and does not depend on source
  dataset row shapes.

External datasets remain replaceable bootstrap/evidence artifacts. Their:

- row schemas;
- source-specific IDs;
- file layouts;
- record counts;
- naming quirks

must not become hidden domain, Planner, Shopping or UI invariants.

## 3. Product objective

DATA-CORPUS-V1 should establish a production-quality baseline that can support
Gate1 and later product gates without creating one-off authoritative records for
each gate.

The intended baseline is:

- `50–80+` verified usable RecipeVersions suitable for realistic household
  weeks;
- `100%` required FoodIngredient resolution across the active recipe corpus;
- authoritative nutrition provenance for every required production profile;
- exact enough food/form identity for current raw/input/cooked semantics;
- reasonable breakfast/main/other recipe variety;
- Russian display readiness;
- progress toward the broader MVP target of approximately `250–350`
  FoodIngredient.

The `250–350` range is a product target, not an artificial publication quota.
Coverage and quality control acceptance. A smaller exact catalogue that fully
covers the active corpus is preferable to padding with unused or weakly sourced
foods; expansion continues as recipe/product demand justifies it.

## 4. Core invariants

DATA-CORPUS-V1 inherits all current project invariants.

### 4.1 Deterministic core

The full runtime remains valid with:

```text
AI_ENABLED=false
```

LLM output is never authoritative:

- kcal;
- protein/fat/carbohydrates;
- micronutrients;
- ingredient quantity;
- mass conversion;
- serving mass;
- allergens;
- price;
- availability;
- storage duration.

### 4.2 Food identity is semantic

A name match is not sufficient evidence.

Raw/input/cooked forms, edible basis and materially different food forms are not
interchangeable. If two forms cannot truthfully share one authoritative
nutrition/composition contract, they are different FoodIngredient.

Brand, package size or cutting style alone do not require a new FoodIngredient
unless they change authoritative food truth.

### 4.3 Unknown is not zero

Missing nutrient, mass, yield or retention evidence remains unknown.

The corpus must never convert:

- missing → zero;
- estimate → exact;
- convenient substitution → accepted identity;
- raw mass → cooked mass;
- source-declared recipe total → canonical calculated total

without an explicitly approved contract and evidence.

### 4.4 One calculation authority path

For each food version, current composition rules still select one authoritative
calculation path.

Do not arbitrarily merge nutrient values from unrelated sources into an
apparently exact profile.

### 4.5 Immutable publication

Published profile/vector/composition/RecipeVersion history is append-only under
the existing versioning contracts. Later corrections append new accepted truth;
they do not silently rewrite old authoritative snapshots.

## 5. Source hierarchy

Source acceptance is based on exact semantics, provenance, rights/use scope and
versionability, not merely on reputation or numerical completeness.

### Tier A — official / primary exact composition authority

Preferred for exact food/form facts when the source provides:

- identifiable food record;
- compatible food/form semantics;
- mass/nutrient basis;
- source version/date;
- reviewable provenance;
- acceptable retained-use scope.

For Russian-specific foods, the preferred authority candidate is material from
ФГБУН «ФИЦ питания и биотехнологии», including the 2024 reference
«Химический состав российских пищевых продуктов» and the official food
composition database.

Research performed 2026-09-19 confirmed that the official site exposes a food
database and describes the 2024 reference edition. The public pages/reference
also retain rights notices rather than presenting an obvious open bulk-data
licence.

**Decision:** FIC is an authority candidate, not automatic permission to bulk-copy
the complete database. Before large-scale retention/publication from FIC, a
rights/use decision must be recorded. Bounded exact facts may be retained only
when their permitted factual-use scope has been reviewed.

### Tier B — open official/government authority

Official composition sources with clear reuse terms may be used as a scalable
baseline when food/form semantics match.

USDA FoodData Central is an accepted candidate in this tier because USDA states
that FDC data are public domain and published under CC0, and it provides
downloadable releases/API access.

Open licensing does not relax semantic identity. A USDA food may populate a
FamilyFoodOS food only when the exact intended form/profile semantics are
compatible.

### Tier C — exact product authority

Manufacturer/official label data may establish nutrition for the exact branded
or declared product it describes.

It does not establish a generic category profile by default.

Examples:

- one exact branded milk → that exact product/form evidence;
- one retailer/private-label cottage cheese → not automatically generic
  `COTTAGE_CHEESE_9`.

### Tier D — corroboration / discovery only

These may assist search, matching or review but are not generic production
authority by default:

- retailer pages;
- mirrors/transcriptions;
- community recipes;
- search snippets;
- secondary nutrition tables;
- unsourced spreadsheets;
- LLM-generated values.

They may become retained evidence only under a separately reviewed source policy.

### 5.1 Durable retrieval of external source artifacts

A hash without a retrievable artifact is insufficient durable evidence.

When a raw source artifact is required to reproduce, audit or extend an accepted
curation/publication result but is intentionally not committed to the public
repository, the owning evidence package must record at least:

- stable project artifact identifier and exact filename;
- byte size and cryptographic SHA-256;
- source/rights classification;
- a **durable private storage locator** that is not a chat attachment or temporary
  authenticated URL;
- the authorized retrieval method/access boundary;
- the date of the latest successful independent retrieval + hash verification;
- the repository package/contract that depends on the artifact.

A temporary authenticated URL may be used to supply CI or a manual rebuild, but it
must not be the only durable locator.

A Contract Gate or data-publication PR is not review-ready when a source artifact
needed for independent reproduction cannot be retrieved from its recorded durable
location and verified against its pinned hash.

The public repository should retain manifests, hashes, provenance and bounded
reviewed derivatives when rights permit; this rule does **not** require publishing
large or restricted raw source bytes.

## 6. Recipe-source authority

The existing Russian normative recipe-corpus decision remains active.

Source acquisition and production publication remain separate:

```text
SourceDocument
→ SourceCard
→ SourceVariant
→ raw source ingredient/process facts

then

review / resolution
→ FoodIngredient mapping
→ exact mass/form validation
→ deterministic Nutrition
→ RecipeVersion publication
```

Presence in a source corpus never means automatic publication.

For every published recipe:

- select an exact source card/variant;
- preserve source identity/version/date;
- preserve exact authoritative ingredient quantities and mass-state semantics;
- map all required source ingredients to canonical FoodIngredient;
- retain technology/process facts required to execute/identify the recipe;
- retain output/yield facts where source-supported;
- leave unsupported yield/retention unknown;
- calculate FamilyFoodOS nutrition deterministically.

Source-declared recipe nutrition remains reference/cross-check evidence unless a
current canonical contract explicitly grants it calculation authority.

## 7. Normalized publication contract — atomic food

Every production atomic food/profile in a DATA-CORPUS-V1 publication batch must
be traceable to the following minimum information, whether persisted directly or
reconstructable from the accepted package and current domain records:

### Identity

- FamilyFoodOS FoodIngredient ID/code;
- Russian canonical display name;
- category;
- relevant form/state semantics;
- aliases used for resolution, where accepted.

### Source

- source authority;
- project source code;
- exact source record/food identity;
- source release/version/date;
- retrieval/capture date;
- source URL or stable publication reference;
- parser/curation package version where applicable.

### Provenance integrity

- retained raw/source snapshot fingerprint when legally and operationally
  appropriate;
- expected source hash/package hash;
- deterministic mapping from source record → FoodIngredient/profile;
- reviewer/publication disposition.

### Nutrition semantics

- profile mass basis;
- nutrient definitions/source nutrient IDs;
- canonical units;
- Decimal values or explicit unknown;
- source-reported zero distinguished from missing;
- uncertainty/estimation state;
- current direct-profile authority decision.

### Rights/use

At minimum:

- `OPEN_REUSE`;
- `BOUNDED_FACTUAL_USE_REVIEWED`;
- `REFERENCE_ONLY`;
- `BLOCKED_PENDING_RIGHTS_REVIEW`;

or a later canonical equivalent.

Rights classification concerns retained source data. It does not replace food
identity or scientific/semantic review.

### Publication identity

- immutable FoodNutritionProfile identity/version;
- sealed NutrientVector identity;
- ATOMIC Composition version when current architecture requires it;
- current/non-current relationship without destructive history rewrite.

## 8. Normalized publication contract — recipe

Every production RecipeVersion published through the program must be traceable
to:

### Source identity

- source document/collection;
- card/recipe code;
- section identity where required;
- exact selected variant/column/branch;
- edition/version/date;
- source URL/reference;
- retained source-data hash.

### Ingredient truth

For every required ingredient row:

- exact source ingredient text/identity;
- selected source alternative if alternatives exist;
- FoodIngredient mapping;
- mapping disposition;
- input quantity;
- unit;
- recipe input mass when authoritative;
- food/mass state;
- estimate flag/review status.

No alternative is selected only because it is easier to resolve.

### Process/output truth

- source-backed technology/process steps needed by the published version;
- source-backed output/yield where available;
- explicit unknown where not available;
- no invented retention coefficients;
- no hidden raw/cooked equivalence.

### Nutrition

- deterministic FamilyFoodOS Nutrition calculation;
- profile/composition versions used;
- status/issues;
- comparison to source-declared nutrition only as review evidence.

### Publication

- immutable RecipeVersion;
- Russian display text;
- meal-type classification under current catalogue contract;
- provenance/rights status;
- verification status.

## 9. Coverage-driven selection

The program selects foods from recipe/product demand rather than downloading a
large nutrient database and declaring all rows part of the product.

The planning matrix is:

```text
recipe/source variant
→ source ingredient
→ accepted/existing mapping
→ canonical FoodIngredient
→ exact authoritative profile exists?
→ mass/form/process blockers
→ publication disposition
```

Recipe candidates are ranked for corpus-building by product usefulness and data
closure, including:

- ordinary Russian household relevance;
- breakfast/main/side/salad variety;
- overlap/reuse of canonical ingredients;
- source quality;
- exact quantity coverage;
- authoritative nutrition availability;
- low unresolved process ambiguity;
- ability to support future Shopping/Pantry/Prep demand.

This ranking is a curation tool, not a Planner runtime rule.

## 10. Execution phases

DATA-CORPUS-V1 is a bounded PR series, not one giant import.

### DC0 — Contract and governance

Owns:

- this canonical contract;
- roadmap sequencing update;
- state/handoff synchronization;
- source hierarchy;
- publication requirements.

No runtime, schema or production data change.

### DC1 — Source authority and coverage inventory

Build the actual demand/authority matrix.

Required outputs:

- initial `50–80+` recipe candidate set;
- exact source variants;
- deduplicated required FoodIngredient/form demand;
- existing accepted mappings reused;
- authoritative-source assignment for each demanded food;
- rights/use status;
- exact unresolved blocker list;
- proposed food publication batches;
- proposed recipe publication batches.

DC1 is evidence/curation. It must not invent missing values.

### DC2 — Food publication batches

Publish authoritative FoodIngredient/Nutrition/NutrientVector/ATOMIC
Composition truth in small reviewable batches.

Typical batch size:

```text
~25–60 exact food/forms
```

This is guidance, not a fixed gate. Evidence complexity controls batch size.

Expected architecture:

- reuse current models;
- reuse current project UoW/repositories/data-upgrade patterns;
- no generalized ingestion platform;
- no migration by default.

If current schema genuinely cannot represent required authoritative truth, stop
and request a separate architecture/migration decision before consuming any
migration number.

### DC3 — Recipe resolution/publication batches

Publish source-backed RecipeVersions in small batches, typically:

```text
~10–20 recipes
```

Each batch must be independently useful and reviewable.

Target baseline:

- `50–80+` verified usable recipes;
- complete required ingredient resolution;
- deterministic usable Nutrition;
- Russian display readiness;
- realistic weekly variety.

### DC4 — Corpus readiness audit and gate consumption

Run a corpus-wide readiness audit.

Then Gate1 selects fixture recipes from normal production catalogue truth.

Gate1 must not create a parallel gate-only nutrition authority layer.

A bounded correction discovered by the audit is permitted only through a separate
reviewed data batch.

## 11. Relationship to Gate1 and PR #66

The 2026-09-19 user decision supersedes the prior strategy of making Gate1 pass by
publishing only a specially selected eight-recipe Russian subset.

Issue #64 and PR #66 remain historical context/evidence.

PR #66 must **not** merge in its current form because its ten newly introduced
profiles were selected to close one fixture and include weaker authority than the
now-approved corpus strategy permits.

The reusable parts of #66, such as fixture structure, selected-source handling,
hash validation and deterministic Planner proof, may be reused later after the
underlying catalogue truth comes from accepted DATA-CORPUS-V1 batches.

Gate1-CLOSE remains a separate review after DC4.

PR9 remains NOT STARTED until Gate1-CLOSE.

## 12. Relationship to the future Data Ingestion Platform

DATA-CORPUS-V1 is **not** the generalized Data Ingestion Platform.

Allowed now:

- controlled source snapshots;
- bounded source-specific extraction;
- curated CSV/XLSX/JSON;
- deterministic conversion scripts;
- internal source-specific import jobs;
- validation/reporting tooling;
- publication batches.

Deferred unless separately authorized:

- arbitrary user URL/file ingestion;
- generic crawling framework;
- review-queue product UI;
- multi-source continuous refresh platform;
- retailer catalogue ingestion;
- generalized source-adapter framework;
- AI-driven publication.

The later Data Program may automate maintenance of this corpus. It must consume
the same canonical contracts rather than replacing them.

## 13. Verification

Follow `verification-policy.md`.

### DC0

Docs/state only:

- link/status consistency;
- diff checks;
- stale-state audit;
- no runtime claim.

### DC1

Curation/evidence:

- source existence;
- source/release identity;
- rights/use classification;
- duplicate/mapping audit;
- food/form semantics;
- quantity/mass-state checks;
- coverage calculations;
- explicit unresolved inventory.

### DC2

Data publication additionally verifies:

- profile/vector consistency;
- nutrient registry compatibility;
- FoodIngredient/profile ownership;
- ATOMIC composition binding;
- idempotent fresh database publication;
- rerun/conflict behavior;
- immutable history;
- affected Nutrition/Composition tests.

### DC3

Recipe publication additionally verifies:

- source variant integrity;
- ingredient-resolution completeness;
- quantity/unit/mass validity;
- RecipeVersion immutability/versioning;
- deterministic Nutrition calculation;
- relevant catalogue tests.

### DC4

Adds:

- full corpus readiness report;
- Gate1 Planner fixture tests;
- persisted complete weeks or explicit bounded infeasibility;
- individualized Servings;
- exclusions;
- deterministic trace/replay.

Broader regression is selected by changed surface/risk and explicit gate
requirements; it is not implied merely by row count.

## 14. DATA-CORPUS-V1 baseline acceptance

The baseline is ready when all of the following are true:

1. the source hierarchy and rights policy are durable repository truth;
2. the active recipe corpus has 100% required FoodIngredient resolution;
3. every required production nutrition profile has accepted authoritative
   provenance;
4. critical food/form semantics are exact under current calculation contracts;
5. `50–80+` recipes are source-backed, immutable and deterministically
   calculable;
6. the corpus provides realistic weekly variety;
7. no critical unknown is hidden as zero/default/estimate;
8. publication/import behavior used by the corpus is deterministic and
   idempotent;
9. source/version/rights evidence is reviewable;
10. the FoodIngredient catalogue intentionally progresses toward the broader
    `250–350` MVP target and fully covers the active recipe corpus;
11. Gate1 can select its fixture candidates from ordinary accepted production
    truth without a special nutrition/data exception.

## 15. Explicit non-goals

DATA-CORPUS-V1 does not authorize:

- RetailSKU or price/availability scraping;
- retailer integration;
- a generalized arbitrary-input ingestion platform;
- AI authority;
- Planner algorithm redesign;
- Auth/PostgreSQL work;
- frontend/admin catalogue UI;
- medical/clinical planning;
- silent cross-source nutrient synthesis;
- silent raw/cooked/form conversion;
- bulk retention from a source with unresolved reuse rights;
- one enormous PR containing the complete catalogue.

## 16. Working sequence

The approved sequence is:

```text
PR8 Planner v0                              COMPLETE
→ Gate1-A audit baseline                   COMPLETE
→ DATA-CORPUS-V1 / DC0                     ACTIVE
→ DC1 source authority + coverage matrix
→ DC2 food publication batches
→ DC3 recipe publication batches
→ DC4 corpus readiness audit + Gate1 consumption
→ GATE1-CLOSE
→ PR9 Shopping Engine
```

Gate1 is the first consumer of the reusable corpus, not the reason the corpus
exists.
