# FamilyFoodOS verification policy

**Status:** canonical verification selection for repository changes.

Select checks by changed behavior and risk, not file count or habit. Explicit
acceptance/milestone requirements still apply; this matrix does not waive them.
For mixed changes use the union of relevant tiers. Documentation about persistence
is docs-only when runtime/schema remain unchanged. Record the chosen tier and
why any broader check is necessary. Every domain change needs meaningful tests.

| Tier / changed surface | Required or typical evidence |
| --- | --- |
| Docs/state/instructions only | `git diff --check`, staged scope audit including `git diff --cached --check`, relevant links, status and stale-state checks. No full backend regression by default. |
| Local domain/service | Focused tests for changed behavior and affected bounded-context tests. Entire legacy regression only when risk/surface justifies it. |
| API/shared composition/cross-context contract | Focused behavior/API tests, affected context/integration tests; broader composition/startup regression when the changed surface can affect it. |
| Persistence/migration/UoW/startup | Focused domain/application/persistence tests; fresh/upgrade migration tests for schema changes; transaction/UoW failure paths where relevant. Full backend **and launcher** regression before review-ready when shared persistence/startup compatibility can be affected. |
| Frontend | Affected frontend tests plus type/build checks; focused route/workflow smoke for user-visible behavior changes. Backend regression only when this task also changes or depends on changed backend/shared contracts. |
| Data curation/import | Validate the bounded corpus, provenance/rights, source resolution, units/quantities and applicable sanity checks; import validation/idempotency when import behavior is involved. Add domain/API/persistence tiers only when those surfaces change. Never substitute invented facts or alter accepted corpus limits to pass. |
| Read-only review/analysis | Inspect evidence and relevant contracts. Targeted read-only verification may resolve concrete concerns; no automatic full regression or mutation/delivery workflow. |

## Repetition and truthful evidence

After sufficient required verification passes, proceed to scope audit and
delivery. Repeat affected checks or broaden when runtime changes again, after a
failure and fix, or when a concrete unresolved concern justifies it. Repeat
relevant docs/static checks after documentation corrections; documentation-only
publication commits do not invalidate previously verified byte-identical runtime.
Do not repeat broad checks merely because they exist.

Record executed commands, results and relevant tested revision. Distinguish
new runs from reused accepted evidence, and explain why reused evidence covers
the unchanged surface. Never claim an unexecuted check passed. For unavailable
checks report the exact reason and any authorized equivalent. A missing required
gate remains a limitation/blocker, not an implicit pass. Do not delete/weaken tests
or acceptance criteria to hide baseline or task failures.

The inherited `scripts/check_documentation_lifecycle.py` belongs to explicitly
scoped CosmeticWorkshopOS lifecycle investigations, not the default FamilyFoodOS
docs gate. Current status checks use current focus, the Master Roadmap and the
relevant FamilyFoodOS canonical contracts.
