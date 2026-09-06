# FamilyFoodOS agent harness

**Status:** canonical instruction-routing design; governance, not a product milestone.
**Decision date:** 2026-09-06.

## Instruction homes

| Layer | Responsibility | When to load |
| --- | --- | --- |
| Root `AGENTS.md` | Persistent invariants, authority/conflicts and routing | Every repository task |
| `state/current-focus.md` | Current authorization and immediate work | Every repository task |
| Scoped `AGENTS.md` | Compatible directory-local invariants | Directories inspected/changed by the task |
| Skills | Repeatable specialized execution | Match requested workflow; name/description first, body when selected |
| Canonical docs / references | Detailed durable knowledge | Relevant subject only |
| Bounded task prompt | Current outcome, scope, acceptance and DoD | Current task |
| `state/handoff.md` | Continuation context | Continuing previous work only |

Ordinary reading is root → current focus → applicable scoped AGENTS → relevant
canonical docs → relevant code → relevant tests. Operating Manual, Master Roadmap
and broader architecture references are loaded for authorization/gates,
product/architecture decisions, cross-context design, conflicts or substantial
research. A normal local correction does not require their full preload.

These are semantic routing rules, not assumptions about one agent's loader.
Inspect applicable nested AGENTS even if the host only discovered ancestors of
its initial working directory. Explicit user instructions define the task;
canonical truth changes only when explicitly authorized. Ordinary conflicts
must be surfaced. Root authority semantics also govern older Skill/policy priority
lists; Skills never override the user or hard project constraints.

## Minimal Skill catalog

[family-food-pr-delivery](../../.agents/skills/family-food-pr-delivery/SKILL.md)
handles an already-authorized implementation, fix, update or curation that delivers
a PR. Read-only analysis/review and merging are excluded. Its body contains the
normal execution loop; optional detail links directly to existing canonical
references. No duplicate reference directory, scripts or vendor/model setting is
needed for this small workflow.

The existing [family-food-ui](../../.agents/skills/family-food-ui/SKILL.md) can
support UI audits and implementation. UI audit does not activate PR delivery;
UI implementation with PR delivery uses both as applicable. No nutrition, pantry,
recipe, shopping, planner or migration Skills are introduced. Root Git/product/
data boundaries remain active even if Skill selection fails.

## Task contract and Definition of Done

Every implementation task still specifies Context, Goal, Scope, Non-goals,
architecture constraints, data model/API/UI impact, tests, acceptance criteria,
risks/limitations, follow-up and required final report. Use N/A when irrelevant.
State task-specific decisions and link to stable constraints; do not paste the
whole permanent project contract into every task. A task must not silently
redefine authoritative data, architecture or gates.

Review-ready means the bounded outcome exists, relevant code/tests were inspected,
required [verification](verification-policy.md) passes, acceptance is checked,
staged scope is audited, relevant docs/state are current, and the feature branch
and PR are published when requested. Report exact base/head, scope, evidence and
limitations. Stop for final review. A product milestone is COMPLETE only with its
accepted closure/merge evidence and owning roadmap DoD. A passing component suite
never substitutes for a required end-to-end gate fixture.

## Audit rationale and evidence

The 2026-09-06 audit was informed by then-current official OpenAI guidance:

- [AGENTS discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md):
  account for instruction discovery and scoped sources.
- [Skill disclosure](https://learn.chatgpt.com/docs/build-skills): concise matching
  metadata selects a body, with further resources loaded as needed.
- [Model guidance](https://developers.openai.com/api/docs/guides/latest-model):
  inspect instruction conflicts, support autonomous follow-through and calibrate
  verification to the task.

These sources informed a repository design decision. They do not override
FamilyFoodOS authority, require GPT-6 Astra, prescribe a provider, or authorize
AI runtime. The harness remains usable by future models and other agents.
Behavioral expectations and evaluation limits are in
[agent-harness-evals.md](agent-harness-evals.md).

## Rule disposition ledger

This ledger classifies removed/compressed instructions from the pre-audit root
(sections 1–20) and scoped files. MOVE means the rule is retained at the linked
home, including where that home already contained it; it does not mean deletion
of product truth. KEEP preserves the invariant while removing repetition.

| Former rule group | Classification | Active home / disposition |
| --- | --- | --- |
| Root 1 reading / document catalog | KEEP IN AGENTS; MOVE TO CANONICAL REFERENCE | Root task routing; this document and Manual for broad navigation; universal preload deleted |
| Root 2 legacy reuse/removal | KEEP IN AGENTS | Root migration invariant; Manual §14 / architecture for examples |
| Root 3 authority list | KEEP IN AGENTS | Root explicit task versus durable truth semantics replace ambiguous rank list |
| Root 4, 7, 20 core loop / consumer detail / quality | KEEP IN AGENTS; MOVE TO CANONICAL REFERENCE | Root mobile-first/minimal effort; Manual §§3–5, 21–22 and Roadmap for loop and quality detail |
| Root 5–6 deterministic core/backend ownership | KEEP IN AGENTS; MOVE TO CANONICAL REFERENCE | Root critical facts/layers; architecture for transaction/versioning/reuse detail |
| Root 8, 14 provenance / ingestion / nutrition safety | KEEP IN AGENTS; MOVE TO CANONICAL REFERENCE | Root trust/medical boundaries; Manual §§6–7, architecture and data-ingestion for pipeline detail |
| Root 9 Planner mechanics | MOVE TO CANONICAL REFERENCE | Manual §8 and architecture §6.6: baseline, justification, trace |
| Root 10 Shopping/Retail mechanics | MOVE TO CANONICAL REFERENCE | Manual §§9–10, architecture §§6.8/6.11, Roadmap: generic-first, separate SKU, researched connectors |
| Root 11 Git hard boundaries | KEEP IN AGENTS | Root scope/delivery; never depend on Skill activation |
| Root 11 execution/staging/PR mechanics | MOVE TO SKILL; MOVE TO CANONICAL REFERENCE | PR delivery Skill; Git/PR human reference for unusual cases and complete PR fields |
| Root 11 task template | MOVE TO TASK PROMPT | Current bounded task supplies fields; required structure/DoD retained here and Manual §17 |
| Root 12 testing | KEEP IN AGENTS; MOVE TO CANONICAL REFERENCE | Root proportional/truthful principle; verification-policy matrix |
| Root 13 schema/data preservation | KEEP IN AGENTS | Root; persistence AGENTS and architecture migration authority |
| Root 15 security | KEEP IN AGENTS | Root public-repository exclusion rule; scoped log/data rules |
| Root 16 agent roles | MOVE TO CANONICAL REFERENCE | Manual §15 retains bounded roles and one architecture orchestrator |
| Root 17 docs/state | KEEP IN AGENTS | Root durability; Manual §19; scoped docs/state contracts |
| Root 18 scoped legacy rules | KEEP IN AGENTS | Root compatible scoped instructions and legacy-only semantics |
| Root 19 sequence/gates | KEEP IN AGENTS; MOVE TO CANONICAL REFERENCE | Root authorization boundary; current focus and unchanged Roadmap order/gates |
| Backend universal ImportSource/ImportDraft, ProductionBatch/StockMovement, order status/AuditLog workflow and skin/client-note semantics | LEGACY / DELETE | Removed as universal rules; legacy code/tests remain byte-unchanged; generic privacy/transactions/Decimal/testing retained in backend AGENTS |
| App inherited calculation list | LEGACY / DELETE; KEEP IN AGENTS | Remove universal cosmetic workflows; preserve layers, business-rule ownership, SQLAlchemy exclusion and errors/tests |
| Persistence PR2-B no-food-tables sentence | LEGACY / DELETE | Completed-slice restriction removed; Core/UoW/SQLite authority stays in persistence AGENTS |
| Docs Restore/D4/D5 lifecycle/ADR map, compulsory lifecycle read/archive/ledger procedure | LEGACY / DELETE; MOVE TO CANONICAL REFERENCE | Remove universal activation; deeper decisions/history AGENTS and historical docs retain relevant archaeology; preserve provenance without mandatory duplicate archives |
| Manual / Roadmap duplicate read waterfall | MOVE TO CANONICAL REFERENCE | Replace with root task routing; Roadmap edit is navigation only, no product order/gate/status change |

## Deferred P2 before PR11

Shorten `family-food-ui`, sharpen its description, remove its duplicated broad
reading waterfall, keep optional Impeccable/reference detail behind progressive
disclosure, and reconcile `docs/ui-skill-policy.md` authority wording with root.
The UI files are unchanged here; their guidance remains subordinate to root's
explicit authority semantics. This is not a PR6 dependency. A global
`~/.codex/AGENTS.md` audit is separate work only if requested.
