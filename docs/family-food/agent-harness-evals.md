# Agent harness evaluation matrix

**Purpose:** repeatable routing and boundary checks, not product authorization.
**Audit:** 2026-09-06. Hypothetical implementation prompts below assume a separate
bounded authorization; they do not start PR6 or authorize PR7+.

Every case starts with root AGENTS and current focus. “Broad docs” means documents
needed by the subject, not a mandatory whole-repository preload. Verification
tiers refer to [verification-policy.md](verification-policy.md).

| Case and representative prompt | PR delivery | UI Skill | Broad canonical docs expected | Scoped AGENTS expected | Verification | Stop point |
| --- | --- | --- | --- | --- | --- | --- |
| Read-only PR review: “Review this backend PR for regressions; do not edit or deliver changes.” | MUST NOT | No | Relevant context contract; architecture only for a disputed boundary, no automatic Manual/Roadmap/Git reference | backend, app; persistence if touched; docs if inspecting changed docs | Read-only evidence; targeted checks for concrete concerns | Findings/evidence; no edits, commit, push or merge |
| Docs closure PR: “Record the approved milestone closure in docs/state and deliver a PR; do not start the next milestone.” | SHOULD | No | Manual + Roadmap and owning closure contract because authorization/status is involved | docs, state; decisions/history only if touched | Docs/state links, status, diff and staged scope; reuse unchanged accepted runtime evidence | Published closure PR ready for final review; no next milestone |
| Local backend/domain PR: “Implement this already-authorized validation correction with focused tests and deliver a PR.” | SHOULD | No | Relevant bounded-context contract; no full Manual/Roadmap/Git preload | backend, app; others only if touched | Local domain/service: focused and affected context | Published PR ready for final review |
| Persistence/migration PR: “Implement this approved additive schema/UoW change and deliver a PR.” | SHOULD | No | Architecture persistence/migration contract and relevant context; migration strategy references for schema impact; Roadmap only for gate questions | backend, app, persistence; docs if changed | Persistence tier: fresh/upgrade, failure paths; full backend + launcher when shared compatibility can change | PR ready only with required strong gate; stop for final review |
| Architecture analysis: “Compare persistence-boundary options against the approved architecture; recommend a decision without editing.” | MUST NOT | No | Manual, Roadmap, architecture, migration strategy and relevant ADRs | docs; decisions when reading ADRs; backend/app/persistence if inspecting implementation | Read-only evidence, distinguish facts/assumptions/decision needed | Analysis/proposal; no silent architecture change or implementation |
| Data curation PR: “Curate the explicitly approved recipe corpus from verifiable sources and deliver a PR without runtime changes.” | SHOULD | No | Data-ingestion, accepted corpus/rights/provenance contract; Manual/Roadmap for gate or substantial research | Actual corpus directory ancestors; docs and decisions if applicable; backend only if data there | Data tier: bounds, provenance/rights, resolution, units, sanity; idempotency if import involved | Published PR or explicit data-authority/rights blocker; no invented facts |
| Read-only UI/UX audit: “Audit current screens for mobile usability and accessibility; report findings only.” | MUST NOT | May (appropriate for this prompt) | Relevant current UI/architecture contract; existing UI policy/Skill may request Manual/ADRs pending P2 | frontend, src; docs for policy; decisions if consulted | Read-only UI evidence, no build/regression by default | Findings and proposed bounded fixes; no edits/PR |
| Frontend implementation PR: “Implement the already-approved accessible error state and deliver a PR.” | SHOULD | Yes for UI changes | Relevant UI/API contract; current UI policy/Skill routing pending P2, no unrelated broad docs | frontend, src; docs when changed | Frontend tests + type/build + changed route/workflow smoke; backend only for changed/dependent shared contracts | Published PR ready for final review; no unauthorized consumer milestone |

## Negative and conflict probes

- A read-only request mentioning “PR” must not trigger delivery. A later explicit
  request to implement findings and deliver a PR should trigger it.
- A local update with no requested delivery does not gain authorization to push
  solely from the Skill description; apply the explicit task and root scope.
- If the Skill is absent/not selected, root still prohibits direct main push,
  autonomous self-merge, unauthorized next milestone and silent architecture/
  authoritative-data changes.
- A task cannot bypass accepted corpus bounds, migration authority, provenance
  or acceptance by describing a change as a routine fix. Surface the conflict.
- UI Skill/policy priority prose cannot place workflow advice above explicit user
  instructions or hard project constraints; root supplies current semantics.

## Evaluation method and results

Static review checks metadata, available instruction paths, relevant document
routing, tier selection and stop boundaries against all eight prompts above.
The eight static cases pass: read-only and execution triggers are distinguished,
persistence retains its strong gate, and no route grants future product scope.
This is a semantic specification review, not proof of live model selection.

For future live evaluation, start a fresh read-only Codex session at repository
root and, separately, at a relevant nested directory. Ask it to report active
instruction sources, selected Skills, relevant references, verification tier
and stop point for a representative prompt. Keep execution hypothetical: prohibit
edits, commits, network publication and implementation. Inspect actual tool/source
loading as well as its self-report; record host/version, working directory, prompt,
observations and limitations. Do not treat a model's claimed loading as trace proof.

Live evaluation evidence for this audit is recorded below before PR delivery.

### 2026-09-06 observed evidence

- Host: Codex desktop on macOS; local `codex-cli 0.142.3`; working directory:
  repository root. A representative read-only PR-review routing probe was
  attempted with `codex --ask-for-approval never exec --ignore-user-config
  --ephemeral --sandbox read-only --json` and an explicit prohibition on edits,
  publication, external connectors and performing the hypothetical review.
- The correctly formed invocation exited 1 before model execution: state DB
  initialization attempted a read-only database write, and in-process app-server
  initialization failed with `Operation not permitted (os error 1)` in the host
  sandbox. An initial invocation placed `--ignore-user-config` before `exec`;
  CLI help identified that option-placement error and it was corrected.
- Live model-trigger/instruction-loading evaluation **did not run**. No inferred
  Skill activation or model pass is claimed. Further nested invocations and
  sandbox relaxation were not needed for this documentation task; the matrix
  remains available for future/manual evaluation.
- Static semantic routing review: **8/8 cases pass** as specification checks.
  `quick_validate.py` reports **Skill is valid!** for `family-food-pr-delivery`.
- Static instruction-debt audit: **PASS**. Active backend AGENTS have zero matches
  for `ImportSource`, `ImportDraft`, `ProductionBatch`, `StockMovement`, `AuditLog`,
  order-status/skin-condition rules or the stale PR2-B no-food-tables restriction.
  Root/Manual use the ordinary scope-first path and conditional broad references.
  Root persistently contains all four hard Git/product/data boundaries.
- Scope/content audit: **15 files**, all docs/instructions/state; **40 relative
  Markdown link targets resolve**. The **899 tracked files outside this allowlist
  are byte-identical** to starting main `abcb1ca8d464477baed72cdf8e06a0d126b5e743`.
  Runtime, schema, migrations, data, dependencies, CI and frontend are unchanged.
  Roadmap sections outside §16 reading navigation are byte-identical. PR5 remains
  COMPLETE, PR6 AUTHORIZED / NOT STARTED, PR7+ unauthorized.

| Persistent instruction | Before bytes | After bytes |
| --- | ---: | ---: |
| Root AGENTS | 10,600 | 6,136 |
| Backend AGENTS | 1,157 | 863 |
| App AGENTS | 1,739 | 1,152 |
| Persistence AGENTS | 867 | 793 |
| Docs AGENTS | 3,577 | 1,110 |
| Total | 17,940 | 10,054 |

Root is 42.1% smaller; the five files together are 44.0% smaller. Semantic
preservation via the disposition ledger is the acceptance gate, not byte count.
Backend/full regression was intentionally not run for byte-unchanged runtime.

`git diff --check`, `git diff --cached --check` and the explicit 15-file staged
scope/content audit: **PASS**. No runtime test pass is inferred from these checks.
