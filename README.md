# FamilyFoodOS

FamilyFoodOS is a separate hosted Web/PWA product bootstrapped from the verified
engineering foundation of CosmeticWorkshopOS.

The source-run backend, launcher, SQLite workflow and inherited frontend remain
transitional migration scaffolding. The inherited macOS consumer `.app` / ZIP
surface is retired by ADR 0031 and is not a supported FamilyFoodOS build or
delivery path.

## Current FamilyFoodOS delivery direction

```text
Target consumer delivery — hosted responsive Web/PWA
Inherited macOS consumer package — RETIRED FROM ACTIVE FAMILYFOODOS
Hosted infrastructure — SEPARATELY GATED; NOT IMPLEMENTED BY PR1
```

See `docs/decisions/0030-family-food-hosted-product-target.md` and
`docs/decisions/0031-retire-inherited-macos-packaging.md`.

## Inherited source-product lifecycle evidence

The following closed CosmeticWorkshopOS lifecycle record remains historical
engineering provenance. It is not a current FamilyFoodOS implementation queue.

```text
PR #193 — MERGED — C4-III RESTORE LIFECYCLE CLOSURE
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

Normative lifecycle: `docs/current-lifecycle.md`.
Historical D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.
Historical D5 decision: `docs/decisions/0021-d5-remote-install-rehearsal-contract.md`.

The exact pre-CR-013 README is preserved in `docs/history/d4-pre-decision/README.md`.

## Historical D4-A closed baseline

D4-A establishes the pre-mutation safety gate without implementing D4-B migration execution:

- `backend/VERSION` is the one editable build-time product-version source;
- backend `pyproject.toml`, `Info.plist`, `package-runtime.json` and Settings/status are projections of that identity;
- packaged runtime resolves version from its validated manifest projection; source runtime resolves the repository source;
- ordinary startup classifies the canonical SQLite database read-only before directory creation, backup or migration;
- only an absent canonical DB is fresh;
- current lineage continues normally, supported older lineage keeps the existing backup-before-migration path, and newer/unsupported/unreadable lineage fails closed;
- no protected Restore production file changes.

D4-A, D4-B, D4-C and D4-D are closed historical source-product evidence.
ADR 0031 retires the D5 exact-package rehearsal from the FamilyFoodOS forward
path; Phase 12 and product release readiness remain gated.

D4-A closure evidence: verified PR head `f294b15365fcf651790e2dc5638ed1551f616c3d` merged as `89dd69dc1958e622146e01869cc34d4cd2ec859e`; exact merged-head verifier `31699624984` passed.

## Historical D4-A/B/C/D closed baseline

The current D4-B changeset replaces only the supported-older direct migration seam:

- `before_migration` backup remains the ADR 0015 SQLite Online Backup snapshot and is verified before staging;
- a runner-owned `.stage` snapshot is created beside the canonical DB with the same consistent SQLite primitive;
- migrations execute only against the stage;
- stage and target lineage are verified before atomic publication;
- the canonical DB is checked unchanged during staging and is replaced only at the commit point;
- durable `update-journal.json` lives outside the working DB and records `started/completed/failed`;
- interrupted `started` operations reconcile conservatively and never blindly resume a stage;
- stage cleanup requires deterministic operation ownership and removes runner-owned SQLite sidecars;
- D4-C is implemented separately as a read-only human-facing status projection plus bounded packaged failure presentation; D4-B remains the update authority.

D4-B closure evidence: verified PR head `8688fa3dba87205b4b4626ebab2902262fd4cd24`, PR-head Level-5 run `31716610699`; merged head `d60a3be993c76b59292cf27ee66bcbe856669fc4`, merged-head Level-5 run `31717705331`. Both exact-package runs passed and the verified PR head is content-identical to the merge commit.

## D4 final closure

D4 Update Safety is **DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED**.

Final D4-D evidence:

- exact tested main/head: `ec88b09193c8ed041e17daef3e3ffc0193d1b559`;
- final exact-package verifier run: `31751386881`;
- evidence artifact: `9201217317`;
- artifact digest: `sha256:0dc707f8823eb69934a5bc3b3b6824557533bafa3e1e86a7f13fc29c19a1af7d`;
- final report: `PASS — FULL AUTOMATED SMOKE PASSED`;
- one exact current-main `.app` was reused across the D4-C human-status/failure matrix and the accepted D4-B staging/interruption/newer-lineage matrix;
- isolated user-data remained outside the repository/package and the repository postflight was clean.

The historical D5 path did not complete. ADR 0031 retires it from the
FamilyFoodOS forward plan; signing/notarization/DMG/App Store/public desktop
release/auto-update, Phase 12 and product release readiness remain unauthorized
or not claimed.

## Inherited source-product invariants

The following list records the source baseline and is not the target
FamilyFoodOS delivery architecture.

- local-first on a MacBook without mandatory internet;
- user data separate from code/package;
- API-first backend even for local operation;
- critical calculations and mutations in backend domain services;
- recipe versions and first-class client recipes;
- lot/movement-based inventory;
- transactional production;
- import through draft/preview/validation/confirmation;
- backup before migration;
- nontechnical user-facing UI;
- no silent mutation of historical data.

## Development authority

Read `AGENTS.md`, the canonical FamilyFoodOS documents and ADRs 0030–0031 before
changing delivery architecture. Source-run development remains available; the
old D5 package path is historical and no macOS consumer package replacement is
authorized. Restore remains closed.


## Historical CR-017 pilot distribution boundary

The CR-016 self-running downloaded `.command` experiment failed the mandatory
human Finder rehearsal because Gatekeeper blocked the bootstrap before
execution. CR-017 then authorized only a single-client operator-assisted
install/update pilot. ADR 0031 retires that path from the current FamilyFoodOS
forward plan; this paragraph remains inherited source-product evidence only.
