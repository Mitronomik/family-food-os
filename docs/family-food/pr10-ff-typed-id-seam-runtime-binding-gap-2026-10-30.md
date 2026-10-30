# PR10-FF typed test-only ID implementation — source-binding preflight

> **2026-10-30 follow-up after merged #264:** The historical API-binding STOP described below was addressed **in code, not yet accepted as a verified Gate**: an explicit manifest loader with external raw SHA/source/coverage pins now provides the approved `recipe_version_key_for` without an extra production-facing write argument; the opt-in Recipe/seed pipeline is wired in draft [PR #263](https://github.com/Mitronomik/family-food-os/pull/263). This file preserves the original preflight rationale. Acceptance still requires exact-head QA, independent source/rights/lineage review and a separately approved *real* manifest and Planner proof. `PR10_FF_FIXTURE_REPRODUCIBLE=NOT_PROVEN`; no PR10 core runtime or release gate is unlocked.

**Status:** PARTIAL IMPLEMENTATION / BLOCKED ON ARCHITECTURE CONTRACT AMENDMENT — NOT REVIEW-READY FOR MERGE.
**Accepted starting base:** `main@b1d6f88d55485fd91f9e6f65a8fb535678f44ef1` (merged PR #262).
**Authorization:** owner explicitly authorized a separate bounded test-only identity seam implementation PR, **not** the later real two-process Planner fixture or PR10 Prep runtime.
**Canonical contract:** [merged typed-ID gate](pr10-ff-typed-test-identity-implementation-contract-2026-10-30.md).

## FACT — implemented and locally verified

- Standalone `app.services.pr10_ff_typed_ids` implements the approved fixed SHA-256 domain separator, canonical JSON envelope, v4-shaped bit layout and six closed semantic-key schemas.
- `ManifestPinnedFixtureIds` rejects IDs absent from a caller-provided *pre-frozen* allowlist, typed-key collisions, noncanonical Decimal, malformed source SHA, invalid original/correction predecessor and mutable input keys; a scoped ledger records allocated identities.
- Two approved deterministic UUID vectors match; 15 local pytest cases passed. This is **only a unit-level conformance proof**, not proof of the eventual manifest's independent provenance.
- There is **no** provider hookup, Recipe write, seed/API change, schema migration or Planner fixture in this partial PR. Normal `uuid4` production composition is byte-unchanged by construction.

## BLOCKER — an unlisted semantic binding boundary

The merged §3.1 contract requires `RECIPE_VERSION.key` to contain:
`publication_process_sha256` (independently pinned before output),
`correction_revision_sha256` (the actual reviewed artifact's raw SHA-256), and
`predecessor_version_key` (the predecessor's full *semantic* key, not its run-local UUID).

Current `FoodRecipeCatalogueService._new_detail(scope, recipe, seed, number, previous_id, now)`
receives `TrustedRecipeVersionSeed` and a UUID predecessor, **not** the frozen correction artifact content SHA or a prior typed predecessor key. `dc4_a3._publish_one` has the authoritative correction artifact in the seed-layer call, but forwards only `successor_seed.version` to `catalogue.append_trusted_version_in_scope`. The original v1 and reviewed v2 share accepted source-record fields. Their differing `change_note`/Steps are **not a substitute** for the pinned correction-artifact SHA, nor is a DB-dependent Step/process hash valid input.

The accepted §4.1 signature matrix permits only a new optional `id_provider.id_for(kind,key)` dependency on existing functions, **not** a new source/correction semantic-context argument or a second provider method. Consequently, this code cannot safely construct all required v2 keys from existing method inputs. Installing the provider via call-order UUID queues, `uuid5`, global monkeypatching, source relabeling or fake correction digests would violate §3.1 and is rejected.

**Disposition:** `NO_GO_TEST_ONLY_ID_SEAM_UNPROVEN` for the end-to-end API/seed bridge. A merged docs gate + owner authorization to implement *its accepted surface* does not authorize expanding the implementation contract. This draft deliberately **does not** wire any of the 22 composer sites while this gap is unresolved.

## Proposed bounded follow-up decision — NOT APPROVED

Independently review and explicitly authorize one precise way to carry verified publication context from the trusted seed layer to the already approved `id_for(kind,key)` resolver, including DC4-A3 v2 correction artifact SHA and semantic predecessor lineage. Candidate options:

1. Additional **keyword-only fixture publication-context argument** on the necessary Recipe write boundaries, with a complete amended call-site/signature matrix and normal-path regression; or
2. Extend the opt-in provider protocol with a **manifest-bound, source-validated key resolution method** supplied by a test-only driver. This is still a material amendment to the accepted provider interface and must fail closed without external pinned witnesses.

Do not select either alternative by guess, and do not use an unreviewed constant or file-read from the application service. A small docs-only amendment should identify which exact interface is minimal, preserve DC4-A3 `EXACT_REPLAY`, preallocate no output events, and define tests before the remaining runtime implementation is resumed.

## Remaining work after a separate owner decision

- Propagate the explicitly chosen optional dependency through all 12 seed modules / 22 catalogue composer sites.
- Verify source/revision/rights/FK identity with actual fresh & replay, normal default-`uuid4` tests, conditional R3-A/B and DC4-A3 v1→v2 append.
- Follow with a **separate** two-process, two-fresh-SQLite real Planner/UoW 3-member / 7-day / 21-MealEvent / 42 exact-Decimal-Serving fixture-proof task. Never use this PR's standalone UUID tests as an A-fixture PASS.

**Standing gates unchanged:** `NO_GO_TO_PR10_CORE_RUNTIME`, `PR10_FF_FIXTURE_REPRODUCIBLE=NOT_PROVEN`, `APPROVED_IMMEDIATE=0`, `SAFE_BATCH_READY=false`, `PORTION_RELEASE_READY=NOT_PROVEN`. No D3, Gate2, Prep/Freezer, Shopping/PDF or product release changes.
