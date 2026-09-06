# FamilyFoodOS — Agent Git / Pull Request Reference

**Status:** canonical human/reference specification for bounded repository PRs.
**Use:** unusual workflow questions, blocker handling and human review. This is
not mandatory reading for every repository task.

## Navigation and ownership

[Root AGENTS](../../AGENTS.md) owns persistent authority, Git and scope boundaries.
[family-food-pr-delivery](../../.agents/skills/family-food-pr-delivery/SKILL.md)
provides the normal executable workflow. The
[verification policy](verification-policy.md) selects sufficient checks;
[agent harness](agent-harness.md) defines routing and the task/DoD contract.
This reference supplies details as needed rather than a second execution script.

## Branch, publication and review semantics

A feature branch normally starts from current accepted `main`; an explicit task
may specify a different base. Record its exact SHA. One PR has one bounded goal.
Preserve unrelated worktree changes and user commits. A push does not create a
PR: explicitly create/update the PR into `main` unless another target is approved.

Routine authorized implementation, correction, commit/push and PR metadata work
is self-service. The user need not drive ordinary Git mechanics. Follow root
boundaries: no direct main push, autonomous self-merge, unauthorized shared-history
rewrite or next-milestone start. Merge is a separate action requiring explicit
post-review authorization; the PR delivery Skill never handles it.

Use the same feature branch/PR for requested task-local corrections. Ordinary
correction commits are acceptable; there is no requirement to rewrite pushed
history into one commit. Create a new PR only if the current one cannot safely
continue or a separately authorized scope requires it.

## Local defects versus decisions

Implementation/test/lint/format defects, missing tests, authorized migration
registration, transaction cleanup, staging mistakes and PR metadata may be fixed
autonomously inside the task. Reverify the affected surface under the policy.

Stop if the proposed remedy changes an accepted architecture/ADR, milestone order,
scope, migration authority, authoritative data/approved corpus, rights/licensing,
medical boundary or acceptance criterion without explicit authorization. Do not
invent facts, bypass tests or resolve canonical conflicts by guessing. A future
Retail, AI, Auth, PostgreSQL or consumer milestone is not an implementation fix.

For a consequential blocker report:

- FACT: observed behavior and applicable contract/evidence;
- ASSUMPTION, if any;
- BLOCKER: why the authorized outcome cannot be completed as specified;
- OPTIONS and RECOMMENDED DECISION, with consequences.

Complete unaffected authorized work first. Prepare a concrete reviewable result
before asking for the final consequential approval. Do not implement an option
that requires a new project decision before that decision is authorized.

## Staging and verification detail

Before commit, inspect the staged diff and at minimum:

```text
git status --short
git diff --check
git diff --cached --check
git diff --cached --stat
```

Use explicit paths or a fully reviewed staged diff. Exclude local databases,
`.env`, credentials, private personal/health records, environments, editor junk,
unrelated user edits and generated artifacts outside the task. Check staged
content, not only filenames. Equivalent API tooling is acceptable.

The task and verification policy determine focused tests, integration, migration,
UoW failure paths, data/import idempotency, frontend type/build/smoke or broader
backend/launcher gates. Report exact environment restrictions and authorized
alternatives; never turn unavailable evidence into a pass.

## Human PR contract

Lead with the concrete problem and resulting behavior. Include, as applicable:

- Goal, Scope and Non-goals;
- architecture constraints/impact;
- data model, migrations, backend, API and frontend impact;
- executed checks and exact results, or reused evidence with its revision;
- acceptance criteria and whether each is satisfied;
- risks/limitations and follow-up;
- final review status.

Use N/A for required fields that do not apply. Scale explanation to the change
and respect an existing PR template. Preserve actual newlines when submitting
bodies; when using `gh`, prefer a file supplied through `--body-file` for multiline
text. Correct task-local title/body omissions without requesting fresh approval.

## State and completion

`IN PROGRESS`, `READY FOR REVIEW` and `COMPLETE` describe different states.
Implementation agents may record readiness after required evidence is complete;
commit/push/PR creation alone cannot mark a milestone COMPLETE. Completion
requires accepted review/merge evidence under that milestone's contract.

A supporting governance/curation PR does not acquire a product milestone number
or advance the next product milestone. Update only relevant execution state and
link to durable decisions. Readiness never authorizes future scope.

The final report includes base branch/SHA, feature branch/head SHA, PR URL/number,
changed scope/outcome, exact verification results, migration/data/seed evidence
where relevant, risks/limitations, current state and confirmation that forbidden
future scope did not start. Finish with the task-specific line
`READY FOR <TASK> FINAL REVIEW` and stop, or report a concrete blocker.
