# First five source-native profile payloads

Base: `a9472c2a0bb0534b70b41c541aa0ac9b4cb26ba0` (PR73 merged).
User authorized first importable batch preparation, separate source-native
carbohydrate semantics and isolated verification. No production write authorized.

## Outcome and task contract

Goal: prepare actual source-native numeric profiles and test whether the existing
profile/vector/ATOMIC path can accept them without inventing values.
Scope: five previously reviewed book2002 profiles, all twelve fields each.
Non-goals: changing runtime schema, registry, Planner, seed or source-use authority.
Source quantities/prices/availability and additional book columns are outside this
bounded profile batch. The full corpus programme is not capped at five foods.

The local build produced five profiles and60 source observations:45 positive,
15 below detection; zero missing in this particular twelve-field subset. Other
book columns are not thereby complete. Every amount retains its exact source
value, unit, state, definition, locator and PDF fingerprint. Book-native
carbohydrates are retained with `unspecified_with_book_general_method`, never
mapped silently to CHOAVL/CHOCDF or backfilled from USDA.

**Result: candidate payload prepared; production-profile import BLOCKED.**
Current FoodNutritionProfile requires numeric energy/protein/fat/carbohydrate,
including NOT NULL persisted fields. All five lack a compatible legacy
carbohydrate projection; sugar also lacks exact protein/fat amounts. Real domain
construction rejects them before any database write. Sparse vectors do not solve
the mandatory owning profile. No fresh/replay/rollback database success is claimed.

## Identity plan

SUGAR, CARROT, CABBAGE_GREEN, BEET are existing canonical candidates. Their IDs
must be resolved from the target repository, not copied from source IDs. Identity
reuse is not yet accepted nutrient equivalence. Existing current USDA profiles
must remain unchanged.

The existing RICE_WHITE means long-grain white rice. The source's generic polished
rice does not establish long-grain identity. `RICE_POLISHED_DRY` is a proposed new
form code, not a created runtime ingredient. Do not duplicate the other four
identities merely to use an importer that only supports newly created foods.

## Reproduce

```sh
python3 scripts/build_dc2_profile_payload.py --corpus /path/to/corpus-v03 --output /path/outside/repository/new-empty-directory
python3 scripts/test_dc2_profile_payload.py
```

The output must be outside this public repository, in a new empty directory.
It contains profiles.json, domain-probe.json, summary.json, receipt.json and
checksums.json. Source snapshot and original packages are never overwritten.
Rebuild to another empty directory and compare files byte-for-byte.
`input-lock.json` pins the reviewed source rows, PDF, form plan, seed and exact
profile implementation. A source/runtime change requires a reviewed lock update.

The numeric package remains local pending the source-use disposition below;
repository stores reproducible tooling, metadata and compatibility evidence.
This distribution choice does not declare factual extraction unlawful.

## Dictionary

Profile ID: stable staging ID, not FoodNutritionProfile UUID. `profile_uuid=null`
means not published. `observations` retains all source fields, including values
unusable in canonical calculations. Each source cell contains `published_value`,
`value`, `state`, `unit`, definition code and detection limit. Only positive
reviewed values have numeric strings; below detection retains literal0 and
value null. `canonical_nutrient_code=null` and `planner_usable=false` prevent
source-native observations from becoming accepted canonical nutrient values.
`provenance` retains review IDs, paired page locators, source definition references
and PDF checksum. Amounts use Decimal in validation; no LLM-derived numbers.

`domain-probe.json` records actual constructor rejection and unsupported legacy
fields. Ephemeral fixture UUIDs are only used inside the probe and never persisted.
Summary counts source observation coverage separately from canonical readiness.

## Verification / acceptance

Ten offline tests cover source-state integrity, nonfinite/negative amounts,
legacy carbohydrate rejection, missing sugar macros, changed inputs and safe
output handling. Two full builds produced byte-identical results. Independent
architecture audit confirmed the profile-owner and registry constraints.

Prepared payload acceptance is met. Successful isolated domain import is not met;
it must follow the explicit contract decision in
[profile compatibility proposal](profile-compatibility-proposal.md).
Existing sparse-vector APIs accept only registered components and do not authorize
new method semantics. Source reuse remains separately unresolved in
[source use](source-use-review.json).

Rollback: no production changes to undo. Preserve local package and original
sources. Remove only this optional preparation tooling if its PR is reverted.
