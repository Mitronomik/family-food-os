# ADR 0033 — Early Consumer PWA development for member food exclusions

## Status

Owner approved 2026-11-26 (Option B). Normative only after independent review
and merge of this governance changeset. Baseline: `main@e7cd319d238a4a759ed6a594623079123f255fbf`,
with PR #309 merged. This is a sequencing exception, not a gate pass.

## Context

The non-medical member exclusion product decision and persistence contract
have been implemented through PRs #303–309. The read-only canonical food
catalogue and Household-scoped exclusion GET/PUT API are available. The
existing `frontend/` is transitional vanilla TypeScript; there is no target
consumer PWA yet. The Master Roadmap normally puts PR11 and PR12 after
technical Gate 2. The selector has no dependency on Prep, PDF or composed
meal admission, so a bounded early UI can test the accepted API without
misrepresenting those capabilities.

## Decision

Permit exactly one early, internal development vertical slice: the minimal
target Next.js/TypeScript responsive Web/PWA shell, existing Household/member
read views, and individual “Не используем” editor. Use the migration-plan
location `frontend-next/` during coexistence; it is the sole target consumer
application and will replace the legacy frontend through the existing migration
process. Do not add consumer routes to the legacy frontend or create a separate
prototype application. Use the existing API, backend source of truth and
local/synthetic fixtures, with no new backend code or data migration.

The owner authorizes the necessary minimal Next.js/React/TypeScript foundation
and a reproducible dependency lockfile, package build/test tooling and
accessibility/responsive styles for this slice. Select compatible supported
versions with documented reasoning and exact lockfile; no unrelated design
system, heavy test stack, deployment infrastructure or service worker caching
of personal data. Keep the shell private, development-only and loopback/local
by default; never expose unauthenticated backend endpoints to shared networks.
No public deployment, real-family testing, account onboarding or claims of
consumer release readiness.

The UI slice is bounded by the accepted exclusion contract and owner task:
member isolation; Russian search/aliases and names; inactive retained IDs;
expected-set CAS; in-memory drafts, explicit save, dirty navigation protection;
race-safe load/search/save; 404/409/422/503/network recovery without blind
overwrite; no raw IDs, medical fields, telemetry or persistent personal cache.
Unknown or non-Russian catalogue display data must be handled explicitly,
not translated or fabricated by the client. Saving affects future generation,
not previously persisted weeks. ABA and shared-deployment authorization remain
limitations. No changes to Planner, Shopping, Nutrition, Prep, PDF or schema.

Verify the target frontend build/typecheck/lint, focused frontend tests,
keyboard/focus and actual responsive widths 375/390/430/768/1024/1440 px,
desktop/mobile screenshots from the running interface, relevant backend API
regressions with AI disabled, and green exact-head CI before owner acceptance.
A missing tool/evidence is reported as a blocker, not a pass.

## Alternatives

- Wait for Gate 2: preserves original sequence but unnecessarily delays
  interaction feedback on already accepted preference APIs.
- Add the editor to the legacy shell: rejected as duplicate migration work.
- Selected: the narrow early target-shell slice, then return to backend.

## Consequences and preservation

This supersedes only the timing prohibition in the Master Roadmap §§5, 6
(Gate 2/PR11), 14 and related migration/ADR/UI instructions for this specific
slice. ADR 0029/0030 target and legacy separation remain intact. No milestone
is marked complete, no acceptance predicate is reduced, no Prep source gate,
Gate 2, Gate 3, Data Readiness, safe-batch release or shared deployment gate
is waived. No further consumer functionality may start under this exception.

After independent review and owner merge of the governance PR, the approved
runtime slice may proceed as a separate bounded PR. After that slice is
accepted, stop UI expansion and resume the canonical backend roadmap:
remaining PR10 source/authority and Prep work, PR10-PDF and Gate 2. Only
after Gate 2 may remaining PR11/PR12 and subsequent consumer milestones
resume under their normal authorizations. Early shell/editor evidence may be
reused but does not by itself satisfy PR11 or PR12. The original milestone
order otherwise remains unchanged.

References: [Master Roadmap](../family-food/master-roadmap.md),
[Migration Plan](../family-food/migration-plan.md),
[Architecture](../family-food/architecture.md),
[ADR 0030](0030-family-food-hosted-product-target.md),
[exclusion implementation contract](../family-food/household-member-ingredient-exclusions-implementation-contract-2026-11-25.md).
