# PR6-DATA-B2-B2-REDESIGNED

Bounded production re-curation from fetched main
`4180297d47d68a0e0d9efbe7a7a27f3900c4f388` (PR #28 MERGED).
**PR6 remains NOT COMPLETE.** No automatic PR6-CLOSE or later milestone.

## Reviewed universe and decisions

The complete accepted seed was reproduced at migration
`0029_food_composition_core`: **185 foods**, 30 current recipes / 189 rows.
B2-B1 identities were re-resolved by recipe code, current version and position:
**37 target rows / 23 recipes / 19 original foods; 46 current uses / 25 recipes**.
All 37 appear exactly once in `row-resolution.json.rows`; the complete impact
universe is separately retained, including nine non-target uses. UUIDs are local
persistence identities, never curation keys. The two remaps change current version
identities; both original and resulting audit keys are recorded.

| Candidate | Final decision | Complete current uses | Authority / boundary |
| --- | --- | ---: | --- |
| MAYONNAISE_LOW_FAT → 173594 | PROMOTE | 2 | SR 2018-04 light mayonnaise. B2-B1 FNDDS synonym/input evidence identifies the generic low-fat/light category; no FNDDS nutrients are imported. Source fiber zero remains unknown. |
| OATS_ROLLED → 173904 | PROMOTE | 3 | SR regular/quick dry unfortified oats; source attributes explicitly include old-fashioned/rolled oats. All three selected recipe branches fit. |
| TOMATO → 170457 | PROMOTE | 3 | SR red ripe raw year-round average; all selected uses are generic fresh tomato. No cultivar-specific profile or canned alternative is substituted. |
| PEACH → 2709249 | DEFER | 2 | No approved Survey (FNDDS) registry mappings or generic/default selection policy. The generic label and yellow-peach input do not authorize a new default policy. |

`profile-decisions.json` records the twelve gates and all-use review references.
The bounded importer has its own three-ID allowlist. Neither historical
`nutrient_vector_backfill_v1.py` nor the RU two-ID importer is modified or generalized.
Imported values are **37 + 31 + 32 = 100** positive exact compatible observations
under the existing 51-code registry/mappings. All 112 reported zeros in these
three extracts remain `UNRESOLVED_ZERO`; absence/incompatibility also remains
unknown. In particular new mayonnaise fiber is `None`, not authoritative zero.
Nutrition v1 is a projection of this same source/profile authority.

None of these candidate foods has Composition v1 on actual main: PR28 marked
them NOT_READY and did not publish their compositions. The task's v2 requirement
is conditional on an existing v1. Each promotion therefore creates its **first
ATOMIC v1**. No fictional historical composition is backfilled. A separate
synthetic adversarial test proves that when an old v1 exists, appending v2 pins
the replacement and replays old v1 through its original sealed vector. All **60
actual pre-existing compositions** replay identically.

## Recipe form and exact mass review

The accepted original saved HTML bytes for both smoothies were reopened and
SHA-256 matched. The original source URL, source ID/hash version, verified-at,
servings, metadata, quantities/units, optional flags, source amount/preparation
text, order, steps and equipment are retained. Only position 6 changes its food
binding; new v2 identities, parent reference, creation timestamps and Russian
revision note are appended. All 13 rows of those two new versions receive
explicit assessments; unrelated rows retain their decisions unless independently
reviewed for the OATS profile replacement in this same operation.

- `SNAP2_SIMPLE_GREEN_SMOOTHIE:v1:6` → v2 frozen unsweetened strawberry.
  The accepted all-one-fruit strawberry branch remains frozen when measured.
  Exact same-ID SR 168173 portion **82603**, `cup, unthawed`, is 149 g per
  source cup (the existing recipe convention normalizes that cup to 240 ml).
  Thawed fruit, package weight, fresh strawberries and other FDC IDs are not used.
- `WIC2_SPINACH_CAULIFLOWER_SMOOTHIE:v1:6` → v2 frozen cauliflower.
  Same-ID SR 170398 portion **86575** requires 1-inch pieces; the recipe does
  not specify this size. Package mass and the unselected riced/steamed alternatives
  cannot fill the gap. The row remains BLOCKED / exact mass required.
- `WIC1_BEYOND_BASIC_GRILLED_CHEESE` retains fresh CAULIFLOWER.

The independently reviewed new profile authorities also permit exact SR
173594 tablespoon **92896** (15 g / source tablespoon normalized to 15 ml),
and SR 173904 cup **93454** (81 g / source cup normalized to 240 ml).
These are three separately appended exact evidence records including strawberry;
no existing evidence is relabelled. The oat two non-target uses and mayonnaise
one target use independently supersede three historical estimate bindings.
Their old estimated evidence/assessments remain available and non-authoritative.
The **other 40 current estimate usages remain non-executable**. No estimate
policy, density, universal piece mass, cross-food portion or 1 ml = 1 g fallback exists.

## Full readiness delta

`implementation-evidence.json` contains complete before/after reports for all
189 rows, ten row-level changes with review references, and recipe-level status
deltas. The unchanged rows are present too; counts are derived from the reports.

| Assessment | Before | After |
| --- | ---: | ---: |
| APPROVED_EXACT | 66 | 71 |
| APPROVED_NO_CONVERSION | 21 | 23 |
| REVIEW_REQUIRED_ESTIMATE | 37 | 35 |
| BLOCKED | 65 | 60 |

Seven rows improve status: strawberry; mayonnaise g and tablespoon uses; tomato
in tabbouleh; all three oat uses. Two tomato rows retain mass ambiguity after
profile review (finely chopped vs unqualified chopped/sliced portion, and pieces
without size). Frozen cauliflower replaces its form blocker with measure ambiguity.
`WIC1_OVERNIGHT_OATS_CINNAMON_APPLE` becomes CONDITIONAL after exact oat mass;
29 recipes remain INCOMPLETE. Zero recipes are COMPLETE/COMPLETE_WITH_WARNINGS.
Nutrition estimation-state warnings remain explicit; food-data readiness does
not certify consumer, kitchen or milestone readiness.

The five PR28-DEFER forms are absent from production. All APPLE bindings/profile
remain unchanged; peeled-apple order and applesauce source choice remain open.
The three chicken/potato/squash yield cases retain `YIELD_EVIDENCE_REQUIRED` in
the row artifact and their existing blocking runtime assessments. No yield,
edible fraction, retention, transformation, composite or extra food is introduced.

## Existing deployment upgrade, transaction and recovery

**No schema migration 0030 is needed.** This is an explicit data upgrade on an
already populated 0029 database, not a fresh-seed-only patch. Existing schema,
triggers, migration lineage and backup inventories remain unchanged. Run the new
bounded operation against the configured database after taking the project's
normal pre-operation database backup:

```sh
# From backend/, with the intended database configured through DatabaseConfig:
AI_ENABLED=false python -m app.seed.b2b2
```

All input/payload hashes are pinned before opening the write scope. One project
SQLAlchemy Core UoW verifies the complete before state (including all current
uses of affected foods), exact PR28 frozen profile/vector/composition prerequisites,
and complete recipe parents. It appends all profiles, sparse values, seals last,
compositions, recipe versions, mass evidence and assessments. It then verifies
the complete after state and every new assessment/evidence before one commit.
No repository commits independently. There is no intermediate public authority.
Any missing, additional, stale or changed reviewed use fails closed and requires
re-curation, rather than skipping that row. A later unreviewed recipe version
also blocks the operation.

The immutable operation/source review references and the full after-state
comparison serve as its reproducible data receipt. A second command invocation
verifies that receipt, sealed vectors/compositions, exact mass contents and all
published/carry-forward assessments, then inserts **zero**. Mixed or conflicting
state is rejected. Failure after each of the six requested publication stages
rolls the complete transaction back; retry starts from the unchanged before state.
Native SQLite backup/restore preserves schema, rows, seals, composition replay
and readiness; a restored post-upgrade backup is also a verified no-op on rerun.
After a successful deployment, operational rollback restores the pre-operation
backup rather than deleting immutable history.

Fresh installations run the already accepted food/recipe → B1 → B2-A corrections
→ B2-A assessments → RU-food chain, then this same operation. Historical loaders
remain pinned to historical authority; do not re-run B1/B2-A as a replacement for
this upgrade after current profiles change. Re-run `app.seed.b2b2` instead.
The audit explicitly builds the accepted baseline first and upgrades that
populated database. Synthetic test records are excluded from production counts.

Only three historical profile `is_current` markers and seven historical
assessment `is_current` markers retire. Every other field in those historical
rows is identical. All old recipe versions, ingredients, steps and equipment,
all FoodIngredients, old evidence, 185 prior seals/value sets and 60 compositions
are preserved. PR28 evidence bytes remain unchanged. The vector read object
includes profile metadata, so its allowed retired `is_current` differs; the
actual sealed values/provenance/seal bytes do not.

## Reproduction and evidence boundaries

```sh
AI_ENABLED=false backend/.venv/bin/python scripts/audit_pr6_data_b2b2.py
AI_ENABLED=false backend/.venv/bin/python scripts/validate_pr6_data_b2b2_sources.py --archive /path/to/SR-RELEASE.zip
AI_ENABLED=false PYTHONPATH=backend:. backend/.venv/bin/python -m pytest -q backend/app/tests/test_pr6_data_b2b2.py
```

The source replay checks the complete five exact FDC food/nutrient/portion
inventories against all six pinned CSV member hashes in the official SR archive.
This task reopened a retained archive matching PR28/B2-B1; it does not claim a new
network download. Live retrieval of both original recipe URLs failed; the
hash-matching accepted local originals supplied those reviews. Of 25 recipe
source records in the impact universe, 22 accepted local originals were rehashed;
three retain explicitly labelled accepted hash-pinned B2-B1 evidence. Historical
source dates are not presented as new observations. Exact source extracts and
per-value source/mapping provenance are retained; no raw recipe documents,
photos/logos, private database or machine-specific source paths are committed.

Verification results and exact commands: [state/progress.md](../../../state/progress.md).
PR6-CLOSE is the next operation only after reviewed merge and separate authorization;
it is a review/gate, not an assumption that PR6 can close.
