# R3-D — final DC3 batch Contract Gate

Accepted base: `1c82f34b960621aed3e1c43780270f8048edfe0f`
Issue: #157
Status: `PREFLIGHT_FROZEN_FOR_GATE`

This package is evidence only. It publishes no runtime data.

## Frozen outcome

The gate freezes **10** source-backed RecipeVersions from the already retained
`RU_MR_2_4_0162_19` bundle:

- 6 meat-free MAIN candidates;
- 2 chicken MAIN candidates;
- 2 differentiated beef MAIN candidates;
- 0 fish additions.

Projected exact-energy Planner-supported catalogue:

```text
41 current
+10 R3-D
=51
```

The lower DATA-CORPUS-V1 baseline is crossed with a one-recipe buffer. R3-D is
therefore the **last planned DC3 expansion batch** before DC4.

## Product result

Current MAIN concentration is 12 exact `BEEF_CATEGORY_1_RAW` + 9 fish + 2
chicken = 23 MAIN. The projected R3-D mix becomes:

- 14 beef;
- 9 fish;
- 4 chicken;
- 6 meat-free;
- 33 MAIN total.

Thus beef/fish concentration moves from `21/23` to `23/33`.

The hard exact-`MILK_2_5` breakfast path is **not improved** by R3-D. The gate
reviewed retained School2022/MR candidates and found no additional source-clean
in-scope breakfast-compatible candidate that could be published without hiding
process/quantity defects. The accepted unaffected set therefore remains 3,
capacity 9. This is retained as an explicit limitation, not converted into a
false PASS.

## Files

- `frozen-batch.json` — exact selected set, ingredient mappings, identity-only
  ledger, process binding and future transaction contract.
- `candidate-audit.json` — selected/deferred/rejected candidate evidence.
- `summary.json` — current/projected catalogue and resilience arithmetic.
- `source-verification.json` — durable MR source receipt plus the retained
  School2022 gap-audit receipt.

Canonical decision document:

`docs/family-food/r3d-final-dc3-batch-gate.md`

Validator:

`scripts/validate_r3d_final_dc3_gate.py`

## Reproduction

Repository-contained verification:

```bash
python scripts/validate_r3d_final_dc3_gate.py --json
```

Optional reproduction of the rejected School2022 milk-free-breakfast audit:

```bash
python scripts/validate_r3d_final_dc3_gate.py \
  --school-archive "$R3D_SCHOOL_ARCHIVE" \
  --json
```

The selected R3-D recipes do **not** depend on the private School2022 archive.
They use the committed MR bundle.

## Stop rule

After a successful separately authorized R3-D runtime and post-runtime
reconciliation, the next planned operation is DC4 corpus readiness audit + Gate1
consumption.

No R3-E/R3-F expansion batch is authorized merely to increase catalogue size.
