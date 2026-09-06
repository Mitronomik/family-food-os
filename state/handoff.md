# Handoff

Updated: `2026-09-06`

## PR5 — Pantry — READY FOR REVIEW

- Starting merged `main`: `b7fb609fc28dc46fa5891fc677272b6d21b58b58`.
- Branch: `migration/pr5-pantry`; PR will be created after final regression.
- PR4 and its closure are merged; no PR4-CLOSE review is pending.
- Implementation contract: [Pantry core](../docs/family-food/pantry-core.md).
- Exact verification: [progress](progress.md#pr5-implementation-evidence).

Dedicated Household PantryItem and immutable PantryMovement are implemented with
canonical FoodIngredient units, exact Decimal current balance, transactional
ADD/CONSUMPTION/WASTE/ADJUSTMENT_IN/ADJUSTMENT_OUT, deterministic multi-item FEFO,
metadata-only PATCH and available/expiring queries. Eight thin HTTP route
capabilities use the Household boundary. Migration `0025_pantry` is additive;
custom SQLite migration authority and legacy schema/data are preserved.

Verification: 267 focused Pantry, 167 affected context/UoW, 142 migration
tests passed. Full backend + launcher: **3255 passed in 467.40s**, no skips.
Ruff and diff/staged scope audits pass. Commit/push/PR publication follows.
Do not merge autonomously.

Known limits: no Auth, conversions, inferred expiry or food-safety policy;
0.001 precision and max 999999999999.999 per item/command; no automatic retries
or resubmission idempotency. Details are in the Pantry contract.

Next gate: PR5 final project acceptance and separately authorized merge.
PR6 Nutrition and every later milestone remain unauthorized. Do not start them.
