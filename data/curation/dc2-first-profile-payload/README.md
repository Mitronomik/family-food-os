# First five source-native profile payloads

Base: `a9472c2a0bb0534b70b41c541aa0ac9b4cb26ba0` (PR73 merged).
On 2026-09-20 the user explicitly authorized correction of all PR74 blockers
and completion of this bounded five-profile preparation/evidence review.
This does not approve the proposed profile/schema design, merge, source reuse,
a migration or production publication.

## Outcome and task contract

Goal: prepare actual source-native numeric profiles and test whether the existing
profile/vector/ATOMIC path can accept them without inventing values.
Scope: five previously reviewed book2002 profiles, all twelve fields each.
Non-goals: changing runtime schema, registry, Planner, seed or source-use authority.
Source quantities/prices/availability and additional book columns are outside this
bounded profile batch. The full corpus programme is not capped at five foods.

Accepted repository metadata independently identifies the same five reviewed
Book2002 records and their 60 field states: 45 `published_positive` and 15
`below_detection`; zero missing in this twelve-field subset. Other book columns
are not thereby complete. The external numeric corpus can be used by the builder
to preserve exact source values, units, states, definitions, locators and PDF
fingerprints, but those numeric values are intentionally not retained in this
public repository while reuse scope remains unresolved. Book-native carbohydrates
remain source-native and are never mapped silently to CHOAVL/CHOCDF or backfilled
from USDA.

**Result: preparation tooling/metadata is reviewable; production-profile import
BLOCKED.** Current `FoodNutritionProfile` requires numeric
energy/protein/fat/carbohydrate. All five selected records retain a
method-incompatible source-native carbohydrate; the accepted source-state metadata
also marks sugar protein/fat below detection. The current domain constructor is
therefore incompatible with the proposed legacy profile projection before any
database write. Sparse vectors do not solve the mandatory owning profile.
No fresh/replay/rollback database success is claimed.

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
`input-lock.json` pins the external source rows/PDF and every repository dependency
used by the identity/domain probe. A source/runtime change requires a reviewed
lock update. `verification-receipt.json` is numeric-free and ties current accepted
source-state metadata, dependency hashes, identity plan, rights status and domain
blockers to this repository revision.

The numeric package remains external pending the source-use disposition below;
repository stores reproducible tooling and nonnumeric compatibility evidence.
No external A/B output hashes were retained in repository-accessible evidence,
so the earlier operator-reported byte-identical full-build result is explicitly
**not** used as merge acceptance evidence. A future full rebuild may establish
that evidence when the operator-managed corpus is available. This distribution
choice does not declare factual extraction unlawful.

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

Repository CI runs the committed metadata validator plus 17 offline tests.
Coverage includes source-state integrity, nonfinite/negative amounts, legacy
carbohydrate rejection, missing sugar macros, dependency locks, identity-plan
drift, rights promotion, false import/readiness claims, verification-receipt
drift and safe output handling. The numeric-free receipt derives the
5-profile/60-observation/45-positive/15-below-detection scope from accepted
profile-review metadata and records five domain blockers with zero DB writes.
External full-build A/B hashes are unavailable and are not acceptance evidence.

Preparation tooling/metadata acceptance is met. Successful isolated domain import is not met;
it must follow the explicit contract decision in
[profile compatibility proposal](profile-compatibility-proposal.md).
Existing sparse-vector APIs accept only registered components and do not authorize
new method semantics. Source reuse remains separately unresolved in
[source use](source-use-review.json).

Rollback: no production changes to undo. Preserve local package and original
sources. Remove only this optional preparation tooling if its PR is reverted.
