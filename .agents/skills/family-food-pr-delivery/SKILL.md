---
name: family-food-pr-delivery
description: >
  Deliver an already-authorized FamilyFoodOS implementation, fix, update or
  content-curation PR with proportional verification and feature-branch
  commit/push. Use when repository changes and PR delivery are requested.
  Do not use for read-only analysis/review or for merging a PR.
---

# FamilyFoodOS PR delivery

Complete the approved bounded change through a review-ready PR. This workflow
does not grant scope or change project truth. Explicit user instructions and
hard project constraints govern; this Skill is execution guidance.

1. Follow root `AGENTS.md` routing: current focus, applicable scoped AGENTS,
   relevant canonical contracts, implementation and tests. Read handoff only
   for continuation. Establish the accepted base SHA, current branch/worktree
   state, authorization and task acceptance criteria before editing. Preserve
   unrelated user work and use the requested feature branch/base when specified.
2. Implement only the bounded task. Reuse compatible engineering patterns,
   inspect legacy assumptions, and update relevant durable docs/state. The
   task contract and DoD are in
   [agent-harness.md](../../../docs/family-food/agent-harness.md); consult them
   when preparing an incomplete task specification, not as a broad preload.
3. Select checks from
   [verification-policy.md](../../../docs/family-food/verification-policy.md)
   and the task's required evidence. Run them, fix task-local defects and rerun
   affected verification. Broaden only for changed risk/surface, a failure/fix
   or a concrete unresolved concern; stop repeating sufficient passing checks.
4. Review the diff and acceptance criteria. Stage only intended files. Run
   `git diff --check`, `git diff --cached --check` and inspect staged scope.
   Exclude secrets, private records, local databases/environments and unrelated
   artifacts. Commit a coherent change on the feature branch.
5. Push the feature branch; explicitly create/update its PR into the accepted
   target (normally `main`). A push alone is not PR delivery. Include outcome,
   scope/non-goals, architecture/data/API/UI/migration impact (or N/A), exact
   verification, acceptance, risks and follow-up. Use the detailed
   [Git/PR reference](../../../docs/family-food/agent-git-pr-workflow.md) for
   unusual mechanics, blocker format or complete human review/report fields.
6. Report base/head SHAs, branch, PR URL/number, changed scope, verification,
   limitations, state and the task's readiness line. Stop for final review.

Fix local implementation/test/lint/format, authorized migration-registration,
staging and PR-metadata defects autonomously. For requested review corrections,
continue the same branch/PR and reverify affected behavior. Do not make approval
a prerequisite for reversible local work already authorized; prepare the concrete
reviewable result before the final consequential user decision.

Never push work directly to `main`, autonomously merge the PR, rewrite shared
history without explicit authorization, or start a future milestone. Review-ready
does not mean COMPLETE. Stop and identify the conflicting contract/evidence when
resolution requires an unapproved architecture, roadmap, scope, migration,
data-authority/accepted-corpus or acceptance change. Do not invent authoritative
data or weaken tests to obtain green checks. Report tool/environment blockers
truthfully; never claim an unexecuted check or failed publication succeeded.
