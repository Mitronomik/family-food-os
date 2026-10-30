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

## 5. Independent reviewer P1/P2 corrections delivered by PR #263

**Evidence/limitations:** focused [GitHub Action run 41048238795](https://github.com/Mitronomik/family-food-os/actions/runs/41048238795) on runtime HEAD `a243287b242b4cb273b9431892e19858647dbdb5` reports **34/34 passed** plus Ruff lint/format SUCCESS; broader exact-head CI must be checked separately. This is a QA proof of the seam, **not** owner acceptance of a forward real-Planner fixture.

| Reviewer finding | Concrete resolution | Adversarial / positive witness |
| --- | --- | --- |
| P1: `EXACT_REPLAY` checked source but not UUID | `FoodRecipeCatalogueService._assert_fixture_replay` validates existing Recipe, RecipeVersion, RecipeIngredient and RecipeStep IDs and positions against the pre-frozen typed manifest in both trusted-seed preflight and reconciliation. DC4-A3 current v2 now preflights the corrected successor before nutrition `EXACT_REPLAY`. The no-provider normal `uuid4` path remains unchanged | Test forged repository readbacks with matching instruction text but foreign Step UUID; no modification of immutable SQLite rows or weaker source matching |
| P1: 12/22 static inventory insufficient | `test_pr10_ff_full_trusted_chain.py` builds QA-only pre-run input from the existing verified source loaders (not DB/Planner output), asserting **51 unique v1 recipes, seven accepted v2 revisions and 12 stage membership entries**. Then executes actual `seed_dc4_a3_russian_step_corrections` with one provider against disposable SQLite, checks 51 persisted recipes, 7 x 2-version histories, runs the entire chain again with `EXACT_REPLAY` and rejects a forged v2 Step ID | Real source loader → real seed/composer/service/UoW + repeated run. QA-only self-pinned hash is deliberately **NOT** the separately reviewer-frozen forward fixture |
| P2: persisted predecessor metadata incomplete | `_fixture_persisted_seed` reconstructs the *complete* trusted v1 version from actual rows, including verification/source-output, all ordered ingredients, Steps and equipment. The existing provider confirms the exact frozen predecessor projection and predicted UUID in the same caller-owned UoW; v2 may change only reviewed Steps and change note | Fake repository readback with altered `source_output_text` rejects a v2 append; no partial successor |
| P2: surplus allowlist entries | `_expected_recipe_allowlist` requires exact set equality for all reachable `RECIPE`, `RECIPE_VERSION`, `RECIPE_INGREDIENT`, `RECIPE_STEP` keys from the approved publication records. Duplicate/unreachable Versions, extra Recipes and missing Steps reject before provider construction | Negative manifest tests for extra Version, extra Recipe and missing Step |

**Immutable-row adversarial strategy:** the real SQLite schema prevents direct updates to RecipeStep and version metadata; the negative QA cases explicitly substitute an untrusted `SqlAlchemyRecipeVersionRepository` readback and require the service to reject it. The legitimate database is never modified for the test. Reviewer should independently validate this boundary, not mistake a forged read result for an actual sanctioned DB mutation.

**Still unproven and separately gated:** an externally owner-approved actual full fixture manifest; two fresh independent Python/SQLite real `PlannerService.generate_authoritative` persisted readbacks with 3 members / 7 days / 21 MealEvents / 42 exact Decimal Servings. `PR10_FF_FIXTURE_REPRODUCIBLE=NOT_PROVEN`, `NO_GO_TO_PR10_CORE_RUNTIME`, `APPROVED_IMMEDIATE=0`, `SAFE_BATCH_READY=false`, `PORTION_RELEASE_READY=NOT_PROVEN`. No automatic merge.

## 6. Follow-up independent review — P1 partial Recipe UUID and P2 providerless DC4-A3

**Reviewed baseline:** `089862b6f898c2d332b5ab1df93e6ac5c5ac8ea2`; corrections delivered in the **same** draft PR #263, no new contract or production data/schema/Planner changes. **Verified corrected runtime:** `96ccff16fae3fda2af101b4618346fef27c5111e`, [focused CI 41053340733](https://github.com/Mitronomik/family-food-os/actions/runs/41053340733): **36 passed**, Ruff lint PASS and Ruff format PASS (10 files already formatted).

| Finding | Code resolution | Focused regression witness |
| --- | --- | --- |
| P1 — existing Recipe has ordinary UUID but no versions | The opt-in Recipe catalogue verifies `recipe.id == id_provider.id_for("RECIPE", {"canonical_code": recipe.canonical_code})` before any RecipeVersion allocation. Enforcement covers existing Recipe in `reconcile_seed_in_scope`, `append_trusted_version_in_scope`, shared `_new_detail` and trusted-seed preflight. Without a provider, the helper is a no-op | `test_mixed_provider_partial_recipe_rejects_all_fixture_write_paths` persists a real random-UUID Recipe with zero versions, exercises all opt-in entrypoints and verifies no Version writes; the providerless append still succeeds independently |
| P2 — correction successor preflight accidentally on normal path | DC4-A3 existing-v2 branch short-circuits its extra corrected successor preflight **only if the catalogue has an explicitly injected fixture provider**. No additional DC4-A3 function parameters and no change to default source, rights, nutrition or replay handling | `test_a3_providerless_replay_does_not_preflight_corrected_successor` executes real default fresh then repeat, fails if a corrected v2 is additionally preflighted, and checks `EXACT_REPLAY` plus unchanged SQLite dump |

**Evidence classification:** the two findings are *addressed in code and focused QA*. Full exact-HEAD CI and independent Architecture/Domain/QA approval remain separate from this technical verification. No claim of an independently frozen real Planner input manifest, two-process authoritative Planner proof, D3, Prep, Gate2, safe batch or release readiness. `PR10_FF_FIXTURE_REPRODUCIBLE=NOT_PROVEN`; `NO_GO_TO_PR10_CORE_RUNTIME`; `APPROVED_IMMEDIATE=0`; `SAFE_BATCH_READY=false`; `PORTION_RELEASE_READY=NOT_PROVEN`.
