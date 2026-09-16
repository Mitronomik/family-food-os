# FamilyFoodOS — Master Roadmap Addendum, 2026-09-16

**Status:** canonical addendum to `master-roadmap.md` and the 2026-09-13 addendum
**Authority:** later explicit user-approved product/data decision
**Sequence effect:** Recipe Assembly research is removed as a blocking prerequisite for Planning Core; the Recipe Constructor remains a separately deliverable product capability.

## 1. Purpose

This addendum records two explicit decisions:

1. the currently supplied technical datasets/corpora are external bootstrap/evidence artifacts and are not the architecture or product model of FamilyFoodOS;
2. deterministic Recipe Construction remains desirable, but constructed recipes are validated through deterministic checks plus external web corroboration rather than mandatory personal kitchen execution.

Where this addendum conflicts with earlier roadmap, assembly, state or curation wording, this addendum supersedes that wording. Historical research/evidence remains valid as history and must not be rewritten to imply a different decision at the time.

## 2. External dataset independence

### DECISION

FamilyFoodOS is not built around any particular technical dataset, seed corpus, source collection, file layout, record count or source-specific identifier scheme.

The current ingredient, nutrition, recipe and related corpora are **replaceable external artifacts** used for bootstrap, curation, development, regression, migration and fixture evidence. They may populate canonical platform models only through the project-owned normalization/validation/publication boundaries.

Therefore:

- dataset row shapes do not define domain entities;
- source-specific IDs do not become platform identity unless explicitly normalized into a platform-owned contract;
- current corpus counts are not permanent product limits;
- a source collection may be replaced by another conforming source without redesigning Household, FoodIngredient, RecipeVersion, Nutrition, MealPlan, Planner, Shopping or Prep contracts;
- source quirks must not leak into Planner or consumer UX as hidden invariants;
- fixture counts such as `30 recipes` or `80+ FoodIngredient` are milestone test/data thresholds, not architectural cardinalities;
- source provenance, rights, uncertainty and immutable publication history remain required even though a source corpus is replaceable.

The service owns its canonical models and contracts. External datasets provide evidence/data for those contracts; they do not own the service architecture.

## 3. Recipe Constructor remains deterministic

Recipe Constructor / Recipe Assembly remains a product capability.

Its core contract remains:

```text
versioned RecipeTemplate / rules
+ canonical FoodIngredient
+ exact quantity rules
+ deterministic constraints
+ composition / nutrition contracts
→ Constructed Recipe Candidate
```

The constructor must work with `AI_ENABLED=false`. AI may assist parsing, matching, explanation or candidate discovery, but may not become the authority for ingredient quantities, nutrition, mass, allergens, cost, availability, storage or publication status.

The constructor must produce a reproducible trace containing the template/rule versions, selected FoodIngredient identities, exact quantities, substitutions/optional choices, rejected alternatives and validation results.

## 4. Constructed recipe validation model

Mandatory personal cooking by the project owner is **not** a publication prerequisite and is **not** a Planning Core gate.

A constructed recipe follows this validation path:

```text
Constructed Recipe Candidate
→ deterministic structural/data validation
→ external recipe discovery
→ normalized evidence extraction
→ similarity/corroboration comparison
→ publication decision
```

### 4.1 Deterministic validation

Before web corroboration, the candidate must pass project-owned checks for at least:

- resolvable canonical ingredients;
- valid units and exact authoritative quantities where required;
- no impossible/invalid numeric ranges;
- nutrition calculation under the active deterministic contract;
- serving/yield consistency to the extent authoritative data exists;
- Russian display requirements;
- hard household/allergen/exclusion safety constraints where applicable;
- reproducible constructor trace.

Unknown critical facts remain unknown and cannot be invented merely to obtain publication.

### 4.2 Web corroboration

External culinary sites are used as **validation evidence**, not as a runtime dependency of Planner and not automatically as the source text of the FamilyFoodOS recipe.

Corroboration compares normalized facts rather than copying prose. Comparison should cover:

1. recipe/dish identity;
2. required/main ingredient set;
3. normalized ingredient ratios/gram ranges;
4. servings or yield where available and comparable;
5. key cooking method/process/order where materially relevant;
6. material contradictions, missing required components or implausible quantities.

Default publication policy requires support from **at least two independent relevant external recipes**. A single source may satisfy corroboration only under an explicitly reviewed high-trust source policy; this is an exception, not the default.

Search-result count or title similarity alone is not evidence. Sources must be sufficiently independent and relevant after normalization.

### 4.3 Rights and provenance

Web corroboration does not grant permission to copy external recipe prose, photographs or copyrighted presentation.

Retain evidence sufficient for audit, for example:

- source URL / source identity;
- retrieval timestamp;
- source/content fingerprint where practical;
- parser/extractor version;
- normalized comparable facts used by the validator;
- comparison result and issue codes;
- corroboration policy/version.

If an external recipe is separately imported as production recipe truth, it follows the normal source/rights/import publication contract. Corroboration alone does not convert external text into FamilyFoodOS-owned content.

## 5. Validation statuses

The earlier model in which default construction required `KITCHEN_VERIFIED` is superseded.

Canonical conceptual states are:

- `STRUCTURALLY_VALID` — project-owned deterministic checks pass;
- `WEB_CORROBORATED` — deterministic checks pass and external evidence satisfies the active corroboration policy;
- `REVIEW_REQUIRED` — evidence is insufficient/ambiguous or meaningful contradictions remain;
- `REJECTED` — deterministic or corroboration checks establish that the candidate should not be published;
- `KITCHEN_TESTED` — optional additional evidence from deliberate physical testing; never mandatory solely to unblock the roadmap;
- `USER_VALIDATED` — future product evidence accumulated from real household use/feedback; not an MVP prerequisite.

Exact persisted enum/table design is an implementation decision. These names define semantics, not mandatory SQL identifiers.

## 6. Runtime boundary

Web validation belongs to catalogue/curation/publication workflows.

It must **not** be part of ordinary Planner runtime:

```text
Catalogue / Constructor pipeline:
constructor → validate → web corroborate → publish immutable truth

Planner runtime:
published valid candidate → Planner → MealPlan
```

Therefore a temporary web outage, source-site outage or disabled AI must not prevent a Household from using already-published catalogue truth.

## 7. Roadmap sequencing decision

Recipe Assembly research performed in PR #31–#45 remains accepted historical evidence, including the fact that the earlier kitchen-evidence gate was blocked under its then-active policy.

That historical blocked state no longer blocks Planning Core after this decision.

The active software sequence is:

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE
→ PR7 MealPlan / Serving
→ PR8 Planner v0
→ GATE 1 — Planning Core
→ PR9 Shopping Engine
→ PR10 Prep / Freezer
→ PR10-PDF Backend Weekly PDF
```

Recipe Constructor / Assembly continues as a separately scoped capability and may be implemented in bounded PRs without forcing PR7/PR8 to wait for mandatory physical kitchen evidence.

PR7/PR8 may consume published immutable `RecipeVersion` truth and, when later available under the new validation contract, published/validated constructed recipe origins. Neither milestone may reinterpret unresolved/incomplete Nutrition facts as authoritative.

## 8. Effect on Gate 1 and fixture data

Gate 1 still requires a deterministic, traceable end-to-end planning path and sufficient fixture data to exercise it.

However:

- the fixture corpus may originate from the current technical dataset or another conforming external artifact;
- the service must not depend on that artifact's source-specific structure;
- `KITCHEN_TESTED` is not a Gate 1 requirement;
- constructed recipe candidates, if used as automatic Planner candidates, must satisfy the active deterministic + web corroboration publication policy;
- source-backed published RecipeVersions may be used according to their own provenance/validation status and the Nutrition contract;
- incomplete/blocked nutrition origins cannot be silently promoted merely to satisfy fixture counts.

If the available external data cannot supply enough valid candidates for a Gate 1 fixture, close the specific data gap through bounded curation/import/evidence work. Do not redesign the service around the dataset and do not invent missing truth.

## 9. Effect on previous canonical documents

This addendum supersedes only the conflicting parts of older documents:

- `master-roadmap.md`: Recipe Assembly A/B are no longer mandatory blockers before PR7/PR8;
- `master-roadmap-addendum-2026-09-13.md`: its PR7/PR8 product/security amendments remain, but the required order no longer begins with `RECIPE-ASSEMBLY-B`;
- `food-composition-and-assembly.md`: deterministic constructor/composition/mass/provenance rules remain, but mandatory kitchen verification for default constructed recipes is replaced by deterministic validation + web corroboration; physical kitchen testing becomes optional evidence;
- Assembly research packages PR #31–#45 remain immutable historical research and do not need to be rewritten;
- `data-ingestion.md`: RecipeCandidate/import validation remains compatible; web corroboration is an additional validation path for constructed candidates, not permission to copy external content.

All unaffected architecture, security, provenance, Russian-language, Nutrition, mass/form, Retail ordering and `AI_ENABLED=false` rules remain in force.

## 10. Next authorized operation

After this governance decision is reviewed/merged, the next software operation is:

`PR7-SUPPORT-MEAL-PATTERN-CATALOGUE`

It remains a bounded supporting operation before PR7/PR8 consume published MealPatternProgram truth.

No Retail, AI Gateway, Auth/shared deployment or unrelated catalogue expansion is authorized by this decision.
