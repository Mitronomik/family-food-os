# Handoff

Updated: `2026-09-16`.

Accepted `main` after merged PR #44 is
`25a496977d19666f812f76792a68aee92732186e`.

PR #44 completed `RECIPE-ASSEMBLY-A-RECOVERY-B` and confirmed that no retained
source-only alternate removes the evidence type currently blocking the third
Recipe Assembly A family.

Assembly A remains 2/3 individually-ready families: `R1-21` and `R1-23`.
`family_count`, `optional_role`, and `verified_substitution` remain OPEN.
Operational status: `HUMAN_EVIDENCE_BLOCKED__2_OF_3`.

Accepted recovery order:

1. `USSR82-267 — Суп-пюре из моркови или репы` — preferred recovery candidate;
2. `R1-05 — Local Harvest Bake` — first fallback if measured 267 verification fails;
3. `USSR82-369 — Грибы в сметанном соусе` — second fallback.

No additional source-only recovery work for 267 is recommended.

The preferred next evidence path is the PR #43 protocol:

`data/curation/v22-13-267-kitchen-a/kitchen-verification-protocol.json`

It requires retained human measurements for the exact carrot branch, exact
turnip branch, the 20 g raw-rice garnish transformation, and service/evaluation
with and without the optional garnish. Repository agents may validate supplied
measurements but must not fabricate physical execution or measured values.

Next conditional action:

- measured PR #43 protocol evidence supplied → separately authorize `V22-13-267-KITCHEN-B`;
- measured 267 execution fails → separately authorize `R1-05-RECOVERY`;
- no measured evidence → remain BLOCKED.

`V22-13-267-PROFILE-B` remains deferred until the kitchen decision.
Assembly B, `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE`, PR7, PR8, Retail, AI and Auth
remain NOT STARTED / not automatically authorized.
