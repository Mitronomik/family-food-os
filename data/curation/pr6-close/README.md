# PR6-CLOSE evidence

Decision: **PR6 COMPLETE**; **PR6-CLOSE — COMPLETE**, submitted for human review.
The [canonical closure decision](../../../docs/family-food/pr6-closure.md) owns the
reviewed interpretation. Tests passing do not infer milestone completion.

- [closure-evidence.json](closure-evidence.json): current production measurements,
  all 40 non-executable estimate usages, nine rows for five deferred forms, three
  yield cases, immutable replay, member fixtures and legacy/normalized divergence.
- [recipe-readiness.json](recipe-readiness.json): all 30 current RecipeVersions and
  all 189 rows, required/optional distinctions and exact provenance.
- [food-readiness.json](food-readiness.json): all 82 required foods (optional uses
  also retained), 51-code sparse coverage, pinned composition and dated RU review.
- [blocker-register.json](blocker-register.json): explicitly reviewed criteria
  1–20, empty milestone blocker list and explicit compatibility limitations.
  This file is not generated from test status.
- [verification.json](verification.json): exact executed checks and retained logs.
- [checksums.json](checksums.json): SHA-256 of every other package file.

Reproduce the current measurement files offline, with backend dependencies:

```sh
AI_ENABLED=false backend/.venv/bin/python scripts/audit_pr6_close.py
```

`--write` regenerates only the three measured JSON files above. It never edits the
reviewed blocker decision, accepted seed truth or a user database. The script
requires the recorded origin/main and accepted merge/test trees; fetch first.
A moved main requires a new reviewed baseline, not editing expected counts to pass.
Run the commands in verification.json separately; historical upgrade audits retain
their historical populations and must not be presented as post-PR29 measurements.

Only temporary databases are seeded/upgraded by accepted loaders. The inspection
phase compares every table before/after to prove it does not mutate truth. It
reads all sealed vectors and replays every composition over all 51 registry codes.
Retained RecipeVersion input/config snapshots replay separately from current-profile
service lookups, consistent with the existing historical-replay contract.

The 185 legacy/normalized nutrient differences are accepted versioned compatibility:
all retain explicit source uncertainty, and normalized composition never substitutes
them for unknown. They do not authorize changing legacy zeros. The five deferred
forms, estimates, APPLE/FNDDS and yield gaps stay unresolved. Sparse sealed vectors
are not complete, RU_READY is not a kitchen certification, and no consumer-eligibility
policy or runtime enum is introduced. No automatic correction or next milestone.
