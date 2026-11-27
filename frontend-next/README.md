# Internal Consumer PWA slice

ADR 0033 only. No public deployment, real family data, Auth or Gate 2 claim.
Use the existing migrated **synthetic** backend on loopback port 8000 and run
the frontend on loopback port 3100. The Household API has no list/discovery
endpoint; the developer must supply an existing synthetic Household UUID via
`http://127.0.0.1:3100/?household=<synthetic-uuid>`. No UUID entry is exposed
in the UI. No backend changes. No service worker or personal data caching.

Commands: `npm install`, `npm run typecheck`, `npm run lint`,
`npm test`, `npm run build`, `npm run dev`. The dependency lockfile must be
generated and reviewed with actual npm registry access before acceptance.
Node 22 is the intended runtime. Next 15 / React 19 / TypeScript 5 are the
minimal target stack; verify exact package availability/security before merge.

The editor retains drafts per member in memory and disables member switching
during a save/refresh. Conflict/uncertain commit requires explicit readback and
user review before retry; no automatic write. Search debounce 300 ms and
abort/sequence guards. Existing exclusions without readable catalogue metadata
remain selected. No medical data, no localStorage, no telemetry. Set CAS ABA
and shared authorization remain unresolved.

Acceptance still requires actual browser screenshots and responsive checks at
375/390/430/768/1024/1440 px, keyboard smoke, API/race integration tests and
exact-head CI; unit model tests alone do not prove the full flow.
