# DC2 profile compatibility change — staged implementation contract

Status: storage is accepted in merged PR76 at
`011f4b74abd29f7b5ec77ab0f15998f781f43c43`. Step 2 implements the
versioned nutrient registry/adapters. Transactional publication and production
food publication remain later separate steps of the approved sequence.

## Concrete conflict

The data contract permits Decimal or explicit unknown. Before this bounded
storage slice, accepted `main` required numeric kcal/protein/fat/carbohydrates
in `FoodNutritionProfile` and persisted profile columns. The accepted
Nutrition contract assigns legacy carbohydrate a definition incompatible with
the book's source-native available carbohydrate. All5 candidate profiles fail;
sugar additionally has below-detection protein/fat. The build probes actual
constructor validation; no database import has occurred.

Changing this contract is consequential: it affects calculations and persistence,
not only import parsing. Root AGENTS requires an explicit schema strategy;
DATA-CORPUS roadmap §10 requires a separate architecture/migration decision when
a publication batch reveals a genuine schema limitation. Reserved migration0033
must not be consumed opportunistically.

## Staged design

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
5. Storage step: migration `0034_partial_nutrition_profiles` uses the existing
   custom runner's foreign-key rebuild mode, preserves dependent identities and
   the accepted Composition trigger, and proves backup/restore plus rollback.
   Reserved `0033_recipe_template_catalogue` remains unused.

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

## Current decision boundary

The user approved the implementation sequence beginning with partial-profile
storage. This bounded slice permits explicit unknown legacy macro storage,
immutable source-observation state and migration `0034`, while preserving all
existing current profiles and holding production publication.

The remaining items are intentionally staged. Step 2 provides a versioned
registry and method adapters without publishing product values. Step 3 is the
next bounded operation: transactional profile/vector/ATOMIC publication.
Book2002 source-use approval and actual production food publication remain
independent gates.
