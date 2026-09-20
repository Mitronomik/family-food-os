# Proposed DC2 profile compatibility change — decision required

Status: proposed; not an implemented migration or accepted runtime contract.

## Concrete conflict

The data contract permits Decimal or explicit unknown. Current
`backend/app/domain/food_ingredients.py:FoodNutritionProfile` and persisted
profile columns require numeric kcal/protein/fat/carbohydrates. The accepted
Nutrition contract assigns legacy carbohydrate a definition incompatible with
the book's source-native available carbohydrate. All5 candidate profiles fail;
sugar additionally has below-detection protein/fat. The build probes actual
constructor validation; no database import has occurred.

Changing this contract is consequential: it affects calculations and persistence,
not only import parsing. Root AGENTS requires an explicit schema strategy;
DATA-CORPUS roadmap §10 requires a separate architecture/migration decision when
a publication batch reveals a genuine schema limitation. Reserved migration0033
must not be consumed opportunistically.

## Recommended design for a separate bounded implementation

1. Permit explicit unknown macro amounts on a new immutable profile version.
   Preserve all existing profiles and their values without rewriting history.
   Representation must distinguish missing, below detection, method-incompatible
   and usable exact values; source observations retain the original literals.
2. Make the sealed canonical vector authoritative for requested nutrients.
   A requested unavailable macro returns an explicit unavailable result before
   arithmetic. Do not let None flow through Decimal operations, default to0,
   or silently switch to another profile/source.
3. Preserve book-native carbohydrate as a separate observation with its method
   and source version. The user's approval to retain this observation does not
   establish equivalence with existing targets or by-difference carbohydrate.
   A future registered source-native component needs a versioned definition and
   compatibility matrix before becoming usable in nutrient calculations.
4. Add a bounded profile publication service using existing UoW, profile
   repository, sealed vector and ATOMIC composition repositories. Resolve
   existing identities; create only the reviewed new rice form. Attach profiles
   as non-current and preserve existing current profiles. Existing
   attach_nutrition_profile clears current and is unsuitable without adjustment.
5. Design an explicit additive migration with repository's custom runner after
   migration ordering review. No new migration number is selected here. If
   SQLite needs a table rebuild, retain foreign keys/history and prove backup,
   transaction and rollback safety before implementation acceptance.

## Acceptance and tests for that implementation

- Existing complete-profile calculations remain byte/Decimal equivalent.
- Missing and below-detection macros persist and round-trip without numeric0.
- Unsupported carbohydrate method cannot satisfy a canonical carbohydrate request.
- Fresh import creates exact profile/vector/ATOMIC versions for allowed records.
- Replay inserts zero records and leaves current profiles unchanged.
- Same provenance with changed values/observations fails with no partial writes.
- Failure between vector values and seal rolls back all new rows.
- Changing current profile does not change older pinned ATOMIC composition.
- Unknown macro prevents full nutrition-dependent use with a clear reason;
  no claim that schema representability alone makes recipes Planner-ready.
- Existing household scopes and all affected nutrition/composition regressions pass.

Rights approval remains independent: changing model representation cannot grant
source reuse. Alternative: keep current model and leave this five-profile batch
blocked until exact compatible Russian source profiles are obtained. Never fill
its mandatory fields with unrelated USDA values under a Russian source label.

## Proposed decision for the user

Approve this separate profile-unknown/compatibility implementation, preserving
current profiles and holding production publication until source reuse and exact
component mappings are resolved. Approval would authorize code and schema
preparation in an isolated checkout, not deployment or unreviewed merge.
