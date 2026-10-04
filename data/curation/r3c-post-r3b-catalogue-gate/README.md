# R3-C — post-R3B catalogue Contract Gate

Accepted base: `90c4f0ebab693b01ec5b4cf7b93b67feeaf0ddb4`
Issue: `#153`
Status: `FROZEN_FOR_GATE_REVIEW`

This package is evidence only. It freezes the next DC3 publication unit after merged PR #152. It publishes **nothing** at runtime.

## Findings

- accepted R3-B exact-energy catalogue: 33 recipes;
- exact-energy meal types: 17 breakfast / 15 main / 1 sandwich;
- breakfast-compatible pool: 18;
- hard `MILK_2_5`: 3 unaffected breakfast-compatible recipes, capacity 9;
- DATA-CORPUS-V1 baseline `50–80+` remains open;
- R3-C freezes **8 MAIN recipes**, not 10–12, because the next closest source cards contain unresolved process placement, unquantified process inputs or source/process fat conflicts.

Future R3-C runtime would project 41 exact-energy recipes: 17 breakfast / 23 main / 1 sandwich. That still leaves a gap of 9 to the lower `50` baseline, so DC4 remains blocked.

## Durable source

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`
SHA-256 `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`
bytes `206692075`

School2022 PDF inside archive:

`corpus-work/packages/school2022/raw/source.pdf`
SHA-256 `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`
bytes `4102547`

The archive was independently materialized from the project Library and hashed again on 2026-10-04.

## Files

- `frozen-batch.json` — exact selected/deferred set, ingredients, source hashes, household/process review, consumer steps and future transaction/acceptance contract.
- `summary.json` — current and projected catalogue/readiness counts.

No migration, schema, Planner or Nutrition-authority change is authorized.


## Reproducible verification

The gate is validated by the committed read-only validator:

`scripts/validate_r3c_post_r3b_gate.py`.

Repository-only checks are reproducible without private source bytes:

```bash
python scripts/validate_r3c_post_r3b_gate.py --repo-only --json
```

For the full provenance check, first materialize the durable Library archive to
an operator-controlled local path, then run:

```bash
export R3C_SOURCE_ARCHIVE=/path/to/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip
python scripts/validate_r3c_post_r3b_gate.py \
  --source-archive "$R3C_SOURCE_ARCHIVE" \
  --json
```

The full check deterministically recomputes the ZIP and embedded PDF hashes,
all **32/32** frozen source hashes (card/process/output/ENERGY reconciliation),
all 51 selected source ingredient rows, selected/deferred disjointness, Russian
consumer-step policy, current catalogue arithmetic, exclusion resilience and the
post-R3-C projection.

The retained command/result receipt is `verification.json`. Repo-only mode
explicitly reports source archive verification as not run; it never converts a
missing private archive into a PASS.
