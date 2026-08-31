# Implementation plan

Status: **CURRENT**
Updated: `2026-08-31`

The exact pre-CR-013 plan is preserved in `docs/history/d4-pre-decision/implementation-plan.md` from base `dc2301f7d4e101ad0fba851325dae9274f02da0c`.

## Current FamilyFoodOS delivery direction

ADR 0030 defines the target consumer product as a hosted responsive Web/PWA.
ADR 0031 retires the inherited macOS consumer `.app`, ZIP and D5 package
rehearsal path. Source-run backend, launcher, SQLite and Restore remain
transitional development/migration scaffolding. Hosted infrastructure remains
separately gated.

## Historical inherited lifecycle evidence

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED
CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — PILOT OPERATOR-ASSISTED PATH AUTHORIZED — FULL D5 PASS NOT CLAIMED
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
CR-016 — ACCEPTED DECISION — IMPLEMENTATION REJECTED BY HUMAN FINDER REHEARSAL
CR-017 — ACCEPTED — SINGLE-CLIENT OPERATOR-ASSISTED INSTALL/UPDATE CONTRACT
D5 pilot deployment — OPERATOR-ASSISTED PATH AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — CR-016 FAIL RECORDED; OPERATOR-ASSISTED REHEARSAL NOT STARTED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015/CR-016/CR-017
Product release readiness — NOT CLAIMED
```

Historical D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.
Historical D5 decision: `docs/decisions/0021-d5-remote-install-rehearsal-contract.md`.
Current delivery decisions: ADR 0030 and ADR 0031.

## Historical D4 programme

### D4-A — Version identity and compatibility preflight

**DONE — MERGED AND EXACT-HEAD VERIFIED**.

Implemented scope:

- one canonical repository version source at `backend/VERSION`;
- dynamic backend package metadata plus generated macOS package projections;
- package-version projection verifier;
- source/package effective runtime version resolver;
- backend Settings/status projection of that same effective value;
- read-only ordinary-startup compatibility wrapper reusing `app.db.migration_lineage`;
- fail-closed existing newer/unsupported/unreadable lineage before backup/migration;
- first-run classification only when the canonical DB path is genuinely absent;
- focused D4-A backend and package tests.

Intentionally unchanged:

- D4-A originally left supported-older migration execution unchanged; the closed D4-B slice now owns staged execution after preflight;
- D4-A itself introduced no UpdateLog; D4-B now owns the durable external UpdateLog;
- no frontend update presentation or new Finder error category exists;
- no protected Restore production file changes.

D4-A, D4-B, D4-C and D4-D are closed. D4 is complete.

### D4-B — Safe migration execution and durable UpdateLog

**DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED**.

Implemented D4-B architecture from ADR 0020:

```text
verified consistent before_migration backup
→ consistent runner-owned migration stage
→ migrate only stage
→ verify source/target lineage and canonical stability
→ atomic canonical publication
→ post-commit canonical verification
→ durable external UpdateLog
```

Implemented scope:

- external atomic `update-journal.json` with `started/completed/failed`;
- conservative reconciliation of interrupted `started` records;
- verified automatic backup as a hard staging prerequisite;
- stage created through the accepted SQLite Online Backup primitive, never raw file copy;
- migrations execute only against the stage;
- exact target lineage + SQLite structural verification before commit;
- same-directory atomic `os.replace` commit after canonical-change/sidecar guards;
- post-commit failures remain distinct from pre-commit migration failure;
- deterministic stage ownership validation before interrupted-artifact cleanup;
- no D4-C frontend or packaged failure-UX work.

D4-B closure remains satisfied. D4-C is also merged, verified and lifecycle-closed.

### D4-C — User-facing update status and packaged failure UX

**DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED**.

Verified PR head `ba577f1151e041c11019525862d9bb76eeb1404e` and merged head `3d69df192b5bdff9c7df067d8c8fde40154ebac9` are content-identical. Level-5 runs `31747841343` and `31749503618` passed the full regression, lifecycle, frontend, real package and exact-package D4-C smoke.

### D4-D — Exact-package update verification and lifecycle closure

**DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED**.

Exact current main `ec88b09193c8ed041e17daef3e3ffc0193d1b559` passed final D4-D run `31751386881` with the complete D4 package safety matrix. D4 is lifecycle-closed. No D5 or release work is authorized by this closure.

## Historical D5 — Remote install checklist

**RETIRED AS A FAMILYFOODOS FORWARD PATH** under ADR 0031.

The first clean-Mac rehearsal correctly exposed the native application lifecycle product defect. CR-015 repaired that blocker, but the earlier human failure is not converted into a PASS retroactively. This remains historical source-product evidence; FamilyFoodOS will not run the fresh package rehearsal because the consumer package is retired.

## Historical D5 blocker — Native macOS application lifecycle

**DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED** under CR-015 / ADR 0022.

Verified implementation head `d7f95141e5f41c7a806c3fafb71e942fe5892dd8` merged as `c38940349a80d345f3e833b61e4bf4e5e761c0eb` with `0` changed files. External run `31780899805` passed the full Python regression (`2692 passed, 1 skipped`) and a real macOS exact-package lifecycle path: LaunchServices first start → synthetic backup/client/component/recipe → application Quit Apple event → no packaged processes/occupied ports → LaunchServices restart → persistence → second application-level Quit. Exact tested ZIP SHA-256: `85f993a93082c4b3a36771318cf8c0c3abf02be56b1374a32a62d1a6b9279ee6`.

The native AppKit executable owns only macOS application lifecycle; the existing packaged helper/Python launcher remains the runtime owner. No business logic, database, Restore or D4 update semantics moved into native code. A shutdown timeout fails closed by cancelling Quit rather than killing the runtime owner and risking an orphan backend.

## Current release boundary

The inherited consumer package and its D5 release path are retired. Product
release readiness remains **NOT CLAIMED**. No hosted infrastructure, signing,
notarization, DMG/PKG, App Store, public release hosting, release channel,
auto-update/download, MDM/remote-management integration or Phase 12 work is
authorized by ADR 0031.


## Historical CR-017 — Single-client operator-assisted pilot path

**PREVIOUSLY AUTHORIZED — NOT IMPLEMENTED — NOW RETIRED BY ADR 0031**.

CR-016's downloaded `.command` model failed the mandatory clean-Mac Finder handoff and is not mergeable. CR-017 replaces only that bootstrap mechanism with a support-operator Terminal workflow for one known client.

Implementation may add one operator-owned install/update script plus focused tests/documentation. It must verify package SHA-256 and staged app identity before quarantine removal, install under the user application directory without `sudo`, preserve the previous app during updates, use ordinary macOS Quit semantics, and leave all database/update safety to D4.

The rehearsal was never completed and is no longer a FamilyFoodOS gate. Public/self-service desktop distribution, Developer ID/notarization, Phase 12 and release readiness remain outside this stage.
