# FamilyFoodOS — Agent Git / Pull Request Workflow

**Status:** canonical execution workflow for repository agents  
**Scope:** implementation, data, documentation and bounded correction work performed through Codex or another repository agent.

## 1. Purpose

Repository agents are expected to complete routine implementation mechanics autonomously inside an explicitly authorized bounded task.

The normal execution loop is:

```text
read contracts
→ inspect current code/tests/state
→ implement bounded task
→ run focused verification
→ fix implementation defects
→ rerun verification
→ run full required regression / lint / diff checks
→ audit scope and staged files
→ commit
→ push feature branch
→ create or update Pull Request into main
→ stop for project final review
```

The user should not have to manually drive ordinary `git add`, `git status`, `git commit`, `git push` or PR creation steps when the agent has the repository tools and the task is otherwise unblocked.

## 2. Default autonomy

Within an authorized task, an agent MAY autonomously:

- inspect repository-local contracts, code and tests;
- edit files inside the approved scope;
- add or strengthen tests required by the task;
- run focused tests repeatedly;
- run full regression, lint, formatting, build and static checks required by the repository;
- fix defects caused or exposed by the current bounded change;
- repeat `fix → verify` until the branch is clean;
- update execution state and handoff documentation required by the task;
- stage only intended files;
- exclude local databases, credentials, generated junk and other forbidden artifacts;
- create one or more ordinary commits on the feature branch;
- push the feature branch to `origin`;
- create a Pull Request from that feature branch into `main`;
- update the same Pull Request with additional correction commits;
- populate or correct the PR title/body so it satisfies the repository PR contract.

No additional user confirmation is required for those routine actions when they stay inside the already-approved scope and do not cross a stop condition below.

## 3. Hard branch boundary

Agents MUST NOT push implementation work directly to `main`.

Required flow:

```text
main
  ↓ branch from current accepted base
feature branch
  ↓ commit(s)
origin/feature-branch
  ↓ Pull Request
main
```

A Git push does not itself create a PR. The agent must explicitly create or update the Pull Request after pushing the branch when PR creation is part of the task.

The feature branch should have one clear bounded goal and should normally be based on the current accepted `main` unless the task explicitly authorizes another base.

## 4. Merge boundary

Routine implementation autonomy ends at review-ready PR state.

An agent MUST NOT merge its own Pull Request into `main` unless the user or current project orchestration explicitly authorizes that merge after final review / merge-gate approval.

Default stop point:

```text
implementation complete
→ branch pushed
→ PR created/updated
→ READY FOR <MILESTONE> FINAL REVIEW
→ STOP
```

Starting the next milestone before the current milestone is accepted and merged is forbidden unless the roadmap explicitly allows parallel work.

## 5. Problems the agent should fix autonomously

The agent should normally fix these without escalating:

- failing tests caused by the current implementation;
- lint/format/static-analysis failures;
- migration registration omissions inside the authorized migration;
- missing bounded-context tests required by acceptance criteria;
- transaction cleanup bugs inside the current context;
- incorrect staged-file selection;
- accidental inclusion of local development artifacts;
- stale task-local state text that must be updated by the current task;
- PR metadata that does not follow the repository contract;
- implementation details that can be corrected without changing approved architecture, data authority, roadmap, scope or product semantics.

The agent should keep correcting and re-verifying until the branch reaches a clean review-ready state.

## 6. Mandatory stop / escalation conditions

The agent MUST stop and return a concrete blocker instead of silently changing project truth when resolution requires any of the following:

- changing the canonical Master Roadmap or milestone order;
- changing an accepted architecture contract or ADR;
- expanding into another bounded context or future milestone;
- weakening or redefining an approved acceptance criterion;
- weakening, deleting or bypassing tests merely to make the branch green;
- inventing authoritative nutrition, recipe, quantity, allergen, price, availability, storage or other source-of-truth data;
- changing the approved recipe/data corpus because implementation is inconvenient;
- exceeding an explicitly approved data/scope bound where no later decision authorizes it;
- introducing a new technology or dependency that materially changes architecture;
- changing migration strategy or persistence authority;
- introducing Retail, AI, Auth, PostgreSQL or other gated scope before authorization;
- resolving a conflict between canonical sources by guessing;
- making a product, medical, licensing/rights or data-authority decision that is not already settled by repository contracts;
- force-pushing or rewriting shared history where this was not explicitly authorized;
- merging the PR without explicit merge authorization.

For a blocker, report:

```text
FACT
ASSUMPTION (if any)
BLOCKER
OPTIONS
RECOMMENDED DECISION
```

Do not implement one of the options until the decision is authorized when the choice is architectural/product/data-authority significant.

## 7. Verification before commit/push

Before final commit/push, the agent must run the checks required by the current task and repository contracts. Depending on scope these include:

- focused unit/integration tests;
- migration fresh/upgrade tests;
- transaction/UoW failure-path tests;
- seed/import idempotency;
- frontend type/build checks;
- full backend/launcher regression;
- Ruff or other lint/format checks;
- `git diff --check`;
- staged-file / scope audit.

If a required check cannot run because of an environment restriction, report the exact restriction and use an authorized equivalent rerun when available. Do not represent an unexecuted check as passed.

## 8. Staging safety

Before committing, inspect staged files explicitly.

Never commit:

- local SQLite/development databases;
- `.env` files;
- credentials/tokens/secrets;
- local virtual environments;
- editor/system junk;
- real user personal or health-related data;
- unrelated worktree changes;
- generated artifacts not required by the task.

Prefer explicit paths or a reviewed staged diff over broad staging when the worktree contains unrelated or local-only files.

Required minimum pre-commit audit:

```text
git status --short
git diff --cached --check
git diff --cached --stat
```

Equivalent repository tooling is acceptable when the agent is operating through an API rather than a shell.

## 9. Commit and PR discipline

Commits should be coherent and describe the bounded change. Correction commits are allowed; rewriting already-pushed history is not required merely to make a single commit.

The PR must target `main` unless the task explicitly specifies another base.

Every implementation PR must include, as applicable:

- Goal;
- Scope;
- Non-goals;
- Architecture impact / constraints;
- Data model changes;
- Migration impact;
- Backend changes;
- API changes;
- Frontend changes;
- tests / verification evidence;
- acceptance criteria;
- risks / known limitations;
- follow-up;
- final review status.

Use `N/A` rather than omitting a required section that does not apply.

## 10. Review / correction loop

After the PR is created, project review may find additional defects.

Normal correction loop:

```text
review finding
→ agent fixes on same feature branch
→ focused verification
→ required regression/lint/diff checks
→ commit
→ push same branch
→ existing PR updates automatically
→ final review repeats
```

Do not open a new PR for ordinary correction commits to the same bounded task unless the existing PR cannot safely be continued.

## 11. State semantics

Implementation state must distinguish execution from acceptance:

```text
IN PROGRESS
READY FOR REVIEW
COMPLETE
```

The implementation agent may set the current milestone to `READY FOR REVIEW` once its acceptance evidence is complete.

It must not mark the milestone `COMPLETE` merely because code was committed or a PR was opened. `COMPLETE` requires the project's accepted closure/merge evidence under the relevant milestone contract.

## 12. Final agent report

When the branch/PR is ready, return at minimum:

- base branch and base SHA;
- feature branch and head SHA;
- PR URL/number;
- implementation summary;
- exact changed scope;
- tests/checks and exact results;
- migration/data/seed evidence where relevant;
- known limitations;
- explicit confirmation that no forbidden future scope was started;
- repository state status;
- one final readiness line:

```text
READY FOR <MILESTONE> FINAL REVIEW
```

or a concrete blocker.

## 13. Governing principle

Agent autonomy is for execution mechanics and bounded implementation quality, not for silently changing product truth.

```text
implementation problem
→ agent fixes autonomously

architecture / roadmap / scope / authoritative-data decision
→ agent stops and escalates
```

This keeps repository work efficient while preserving user control over consequential project decisions and keeping `main` review-gated and working.
