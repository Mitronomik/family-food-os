# PR10-FF — test-only pinned publication manifest implementation contract

**Status:** implementation-specific evidence for draft [PR #263](https://github.com/Mitronomik/family-food-os/pull/263); **not** an independently owner-approved real fixture manifest or PR10 release approval.  
**Authority:** merged [#262 typed ID contract](pr10-ff-typed-test-identity-implementation-contract-2026-10-30.md) and [#264 publication-key amendment](pr10-ff-publication-key-binding-amendment-2026-10-30.md).

## 1. Explicit loader API and boundaries

Implementation module: `backend/app/services/pr10_ff_manifest_loader.py`. Public opt-in test-only function:

```python
load_pinned_publication_manifest(
    path: Path,
    *,
    expected_sha256: str,
    expected_source_commit: str,
    expected_stage_membership: Mapping[str, Sequence[str]],
    correction_path: Path | None = None,
    expected_correction_sha256: str | None = None,
    expected_correction_blob_sha1: str | None = None,
) -> PublicationManifestIds
```

**No default or environment discovery.** The SHA-256 of raw manifest bytes, source commit and *complete stage membership inventory* must come from independently reviewed/frozen evidence outside the manifest; the caller must not compute those expectations from the same file it intends to accept. If any differs, NO_GO before publication. For corrected versions, the caller also supplies independently pinned original raw correction JSON bytes' SHA-256 and Git blob SHA-1 and the exact path. Current accepted DC4-A3 artifact: Git blob `ec1f8fca9ff8d3c4ac844f6eab0c3411ece54c68`; SHA-256 `157f2ce76cc86baae2b288ce80da069154bc6d44ca1620b2b9f0c521b92e7759`.

The `PublicationManifestIds` constructor is sealed to the verified loader, not public direct construction. It extends the #262 `id_for(kind, key)` with **only** the #264-approved `recipe_version_key_for(*, canonical_code, seed, version_number, predecessor_id)`. Production-facing Recipe and seed callers receive only optional `id_provider=None`. No new domain model field or database schema is introduced.

## 2. Exact JSON payload contract

Input is one UTF-8 JSON object with **exactly** these top-level fields:

```json
{
  "schema_version": "PR10_FF_PUBLICATION_MANIFEST_V1",
  "policy": "PR10_FF_TYPED_ID_POLICY_V1",
  "namespace": "familyfoodos/pr10-ff/fixture-only/v1",
  "fixture_id": "PR10_FF_FORWARD_3M_7D_V1",
  "source_commit": "<40-hex pre-reviewed commit>",
  "review_reference": "<independent review or decision URI>",
  "approved_ids": [
    {"kind": "RECIPE", "key": {"canonical_code": "<code>"}},
    {"kind": "RECIPE_VERSION", "key": "<full closed #262 version key>"}
  ],
  "publications": [
    {
      "stage": "<reviewed trusted seed stage>",
      "canonical_code": "<code>",
      "version_number": 1,
      "version_key": "<same approved RECIPE_VERSION key>",
      "seed_projection": "<all TrustedRecipeVersionSeed fields>"
    }
  ],
  "stages": {
    "<reviewed stage>": ["<code>@1"]
  }
}
```

Angle-bracket fields above are **placeholders**, not an accepted actual manifest. The real `version_key` is a JSON object conforming to the six-kind schema in #262; the example uses a string placeholder solely to keep the illustration compact. The stage map is checked against independent `expected_stage_membership` and must exactly cover every listed published version, without extra rows or duplicate identities. Real forward corpus membership (including 12 seed stages and seven DC4-A3 v2) must be independently determined and accepted **before** a positive fixture run. No selected MealPlan may be used to backfill those inputs.

`approved_ids` comprises the complete closed typed keys for Recipe, RecipeVersion, RecipeIngredient, RecipeStep and, where applicable, synthetic Household and HouseholdMember. Every publication version key and its full recursive predecessor key must be present. Additional ID allocations missing from this allowlist are fail-closed, never silently `uuid4`. Key structures and digest/UUID version bits remain **exactly #262**.

`seed_projection` is the field-complete, recursively serialized `TrustedRecipeVersionSeed`: every dataclass field including source/rights/verification, nutrition-related source-output attributes, all ingredients and ordered Steps, timestamps, equipment and freezability/storage metadata. `Decimal` becomes finite normalized fixed-point string, enums their code strings, timezone-aware instants normalized UTC ISO 8601 `Z`, and `None` JSON null. Unknown/missing top-level seed fields, non-NFC strings, float values in source projections or mismatched actual seed inputs cannot produce an identity.

## 3. Frozen process SHA and correction bindings

The explicit source-independent ordered-Step process fingerprint used by this seam is:

```text
SHA256(
  UTF8(
    json.dumps(
      {"steps": [<full unmodified NFC instruction strings in source order>]},
      ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
  )
)
```

This `publication_process_sha256` is pinned per published v1/v2 version in the externally reviewed manifest and recomputed from `seed_projection.steps` at load; the current DB `process_hash` that includes random `RecipeStep.id` is *not* an input. Ingredient quantities/forms, rights and nutrition are checked **separately** through source-backed seed projections and live service/read-scope validation, never inferred from the process digest.

Corrected v2 requires `correction_revision_sha256` equal the external correction artifact's **raw bytes** SHA-256, exactly one reviewed correction row with same code, v1 old Steps equal the original frozen seed and current real predecessor, and v2 new Steps equal the candidate corrected seed. The predecessor UUID is used only to compare against the digest of its frozen **semantic version key**, then to load the actual predecessor from the same caller-owned UoW. Its run-local UUID is not part of any semantic key.

## 4. Immutability, provenance and acceptance limits

The loader validates and copies the complete JSON input into canonical typed key bytes and complete deterministic seed-projection bytes. Its lookup returns a new key mapping and never mutates the frozen index. It rechecks the raw file byte hashes during ID allocation, rejecting later file edits; it has no implicit global provider, `contextvar`, environment flag or production CLI path. `ManifestPinnedFixtureIds(approved)` alone is **not** a publication-capable provider. A provider cannot create source authority or grant rights merely because its local manifest is self-consistent.

**Current QA in PR #263:** synthetic source-manifest loader and actual disposable SQLite Recipe creation/append tests, negative bytes/lineage/Step/seed-field mutation tests and static 12-module/22-composer inventory checks. These demonstrate the algorithm and opt-in boundary, not an owner-accepted full real seed manifest. A separate real fixture proof must first pin independently reviewed actual full source/candidate/household/Planner input, then run two independent fresh SQLite/Python processes through unchanged `PlannerService.generate_authoritative` and persisted UoW readbacks with 3 members, 7 days, 21 source-bound MealEvents and 42 exact Decimal Servings.

**Unchanged gates:** `PR10_FF_FIXTURE_REPRODUCIBLE=NOT_PROVEN`; `NO_GO_TO_PR10_CORE_RUNTIME`; `APPROVED_IMMEDIATE=0`; `SAFE_BATCH_READY=false`; `PORTION_RELEASE_READY=NOT_PROVEN`. No Prep/Freezer, D3, Gate2 or safe-batch/portion release authority.
