# PR #196 original synthetic Gate2 fixture receipt — evidence archive

**Status:** archived synthetic QA evidence only. It is **not** production catalogue data, a Planner output for a real Household, Prep eligibility, Gate2 success, or release authorization.

## Immutable source

- Original GitHub PR: [#196](https://github.com/Mitronomik/family-food-os/pull/196)
- GitHub Actions run: [38059374826](https://github.com/Mitronomik/family-food-os/actions/runs/38059374826)
- Source artifact ID: `11672432141`, `pr10-meta-synthetic-fixture-receipt` ZIP
- ZIP member: `pr10-meta-fixture-receipt.json`
- Repository archive (complete raw JSON bytes): [pr196-original-synthetic-fixture-receipt.json](pr196-original-synthetic-fixture-receipt.json)
- Raw uncompressed size: **110511 bytes**
- Raw JSON SHA-256: `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec`
- Git blob SHA-1 (for byte-identical repository copy): `e82f147be4f7d1c67fe298ce973a968223910d03`
- Original Actions artifact expiry (as reported by GitHub on 2026-10-29): `2026-11-09T14:24:01Z`
- Archive publication: PR [#248](https://github.com/Mitronomik/family-food-os/pull/248), docs-only branch `docs/pr10-core-option-a-stable-fixture-gate`

A byte-for-byte matching copy was placed in the PR branch directly from the original conversation attachment, after checking original file size and SHA-256. The uploaded GitHub blob was fetched back and its **SHA-256 independently recomputed** from the downloaded repository content; it matches the source above. No field was rewritten, and no source UUID was remapped. This archive will remain on the PR branch after the original Actions artifact expires; long-term availability on `main` depends on a separately authorized merge.

## Reviewer verification

From a checkout of the PR branch:

```bash
sha256sum docs/family-food/evidence/pr196-original-synthetic-fixture-receipt.json
# 6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec

wc -c < docs/family-food/evidence/pr196-original-synthetic-fixture-receipt.json
# 110511

git hash-object docs/family-food/evidence/pr196-original-synthetic-fixture-receipt.json
# e82f147be4f7d1c67fe298ce973a968223910d03
```

The JSON schema is `PR10_META_GATE2_FIXTURE_PINS_V1`, scope `SYNTHETIC_FRESH_SQLITE_PERSISTED_DIAGNOSTIC_ONLY`, and `gate_decision=BLOCKED`. Counts **3 members / 21 events / 42 Servings** are structural evidence, not a reproducibility or Prep PASS.

Reviewers must still independently recompute the UUID-independent historical comparison digest from this archive (**`731ef32e7137740ed5b46a6044a85d8b2f818a847fdc039842460d442df5aeb6`**) and verify original-source/right/Step identity before accepting the Option A contract. The existing per-run UUID-bearing Planner semantic digest is **not** portable. The [Implementation Contract Gate](../pr10-core-option-a-stable-fixture-implementation-contract-2026-10-27.md) documents remaining Planner input parity, seed ID factory, and Gate2/D3 blocks.

## Preservation / limitations

This repository file is a historical snapshot of **synthetic** test data; it is not auto-published into any platform table and must not be used to bypass `PlannerService.generate_authoritative`. The recorded randomized UUIDs serve only to validate the **historical** receipt; fresh persisted RecipeVersions, MealEvents, Members and Steps require independent current-binding checks. No production code or migration is modified by archiving this file.
