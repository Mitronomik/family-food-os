# Handoff

Updated: `2026-09-12`

PR #28 (PR6-RU-FOOD-DATA) is **MERGED / delivered**. GitHub merged state and
fetched `origin/main` both resolve to `4180297d47d68a0e0d9efbe7a7a27f3900c4f388`.
Current authorized operation: **PR6-DATA-B2-B2-REDESIGNED**, branch
`codex/pr6-data-b2-b2-redesigned`. Migration remains `0029_food_composition_core`.

[The bounded evidence package](../data/curation/pr6-data-b2-b2-redesigned/README.md)
contains 37 unique target decisions, all 46 uses, source extracts, full immutable
parent/revision/assessment comparisons and complete readiness before/after.
The measured baseline is 185 foods / 30 current recipes / 189 rows.

Implemented on disposable databases: two immutable smoothie v2 remaps; exact
149 g unthawed strawberry cup evidence; frozen cauliflower remains mass-blocked
because source portion specifies 1-inch pieces absent from the recipe. Fresh
cauliflower remains unchanged. Three profile promotions: mayonnaise 173594,
oats 173904, tomato 170457, all SR 2018-04; PEACH 2709249 DEFER for unapproved
FNDDS mappings/default policy. Existing Russian food names remain unchanged.

New publications: 3 profiles / 100 positive normalized values / 3 seals /
3 ATOMIC compositions, 2 recipes / 13 ingredient rows, 3 mass evidence records,
20 assessments. Only 3 old profile markers and 7 old assessment markers retire.
All other historical facts remain identical. Each promoted food lacked a
composition on main (PR28 NOT_READY); its first ATOMIC publication is v1.
The task's conditional existing-v1 → new-v2 rule is verified with synthetic
fixtures. All 185 old seals and 60 actual old compositions remain readable/replayable.

The explicit `app.seed.b2b2` command is the populated-0029 data upgrade, using
one project UoW, pinned hashes and full before/after receipt. No schema migration
0030 or historical migration edit. Fresh databases use the accepted seed chain
then this same command. Rerun only the new reconciliation after profile changes;
historical B1/B2-A loaders deliberately remain pinned to old authority. Failed
publication rolls back; successful operational rollback uses the prior backup.

Full readiness: 66/21/37/65 → 71/23/35/60 exact/no-conversion/review/blocked.
Seven row statuses improve; all ten row-report changes are explained. Overnight
oats becomes CONDITIONAL; 29 recipes remain INCOMPLETE. Three estimate usages
are independently superseded; all original estimated evidence stays historical
and the remaining 40 usages are non-executable. APPLE, five deferred forms and
three yield cases remain blocked. No new foods or estimate policy.

Verification: focused 27 passed; source replay and existing B2-A, VECTOR-A/B,
Composition and RU audits pass; Ruff/format and 3-file runtime mypy pass.
Full backend + launcher regression with AI_ENABLED=false: **3826 passed in 649.81s**,
zero skips. All required checks pass.
See [progress](progress.md) for exact commands. **REVIEW-READY in
[PR #29](https://github.com/Mitronomik/family-food-os/pull/29)**, opened into main.
Implementation commit: `d0a238ce32193d5884d61ee384d5eb7f242bcaed`.
This delivery receipt changes state only; tested runtime/data/test bytes are unchanged.
Unrelated `.DS_Store` stays excluded.

**PR6 — NOT COMPLETE.** Stop for final review without merging. Do not start PR6-CLOSE automatically. After
reviewed merge it is a separate review/gate, not assumed milestone completion.
