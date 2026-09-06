# AGENTS.md — FamilyFoodOS Agent Contract

FamilyFoodOS is bootstrapped from CosmeticWorkshopOS. Legacy code/history are
engineering provenance, not the food specification.

## Authority and conflicts

Explicit user-approved instructions define the requested task and outcome.
This contract and current canonical FamilyFoodOS documents define durable
project truth; a user may explicitly authorize changing that truth. An ordinary
task that accidentally conflicts with it is not such authorization: stop,
identify the conflicting rules and propose a resolution. Never silently change
architecture, roadmap, scope, authoritative data, accepted corpus, acceptance
criteria, migration strategy or another gated decision.

Within repository guidance, root invariants govern; scoped AGENTS add compatible
local rules. Canonical documents own their stated subjects; the Operating Manual
is the broad operational reference. Report unresolved canonical conflicts rather
than guessing. Skills provide workflow guidance and never override explicit user
instructions or hard constraints, including competing Skill/policy priority lists.
Legacy business rules apply only to explicitly scoped CosmeticWorkshopOS work.

## Read by task

Ordinary work starts with:

`AGENTS.md → state/current-focus.md → applicable scoped AGENTS.md → relevant canonical docs → relevant code → relevant tests`

Read `state/handoff.md` only when continuing previous work. Inspect nested
AGENTS for every directory in scope; do not preload unrelated directory rules.
Before coding, inspect behavior/tests, reusable patterns and legacy assumptions.

Load the [Operating Manual](docs/family-food/project-operating-manual.md),
[Master Roadmap](docs/family-food/master-roadmap.md) and relevant architecture
references for milestone authorization, gate interpretation, product/architecture
decisions, cross-context design, source-of-truth conflicts or substantial
research. Ordinary bounded corrections do not require this broad preload.
The detailed [Git/PR reference](docs/family-food/agent-git-pr-workflow.md) is for
unusual workflow questions and human review, not mandatory reading for every task.

For authorized implementation, fixes or content updates that deliver a PR, use
[family-food-pr-delivery](.agents/skills/family-food-pr-delivery/SKILL.md).
Read-only review excludes delivery. Task-contract/DoD requirements:
[agent-harness.md](docs/family-food/agent-harness.md).

## Product, architecture and data invariants

- The deterministic core works with `AI_ENABLED=false`. Critical nutrition,
  quantity, serving, allergen, cost/price, availability and storage facts are
  backend-owned and never invented by an LLM. Nutrition is deterministic and
  versioned; uncertainty must be explicit.
- Production recipes retain verifiable provenance. Untrusted parsed/AI data
  passes validation and review or an explicit trusted-source policy before
  becoming production truth. Preserve source/version history and auditability.
  The MVP makes no diagnosis, treatment or therapeutic-effectiveness claims.
- New food runtime follows `UI → API → services/domain → repositories → database`.
  Domain/services do not import SQLAlchemy. Food persistence uses synchronous
  SQLAlchemy 2.x Core, repositories and the project UoW. The custom SQLite
  migration runner remains the sole active SQLite schema authority; no ORM,
  async database stack, Alembic or production `create_all` in this phase.
- Persisted schema changes require an explicit migration strategy. Preserve
  existing data, transactions, versioned history and backup/export safety.
  Household-owned data stays Household-scoped across reads and writes.
- Never mechanically rename/reuse legacy concepts as food concepts: Client is
  not HouseholdMember, Order is not MealPlan, ProductionBatch is not PrepBatch,
  and cosmetic PackagingItem is not a retail food package. Introduce a new food
  context, move dependencies, test, then remove legacy only when authorized.
- Consumer UX is mobile-first and minimizes effort: the system proposes and the
  user confirms/changes. Administrative controls must not dominate navigation.

## Scope, delivery and verification

Current authorization belongs in `state/current-focus.md`; milestone order and
gates belong in the Master Roadmap. Follow the migration plan for replacement
strategy. No future context, AI, Retail, optimization, native app or shared/SaaS
infrastructure may start before its gate and authorization.

Keep `main` working. One feature branch/PR has one bounded goal. Never push work
directly to `main`. Never autonomously merge your own PR; merge requires explicit
post-review authorization. Never force-push shared history without explicit
authorization. Never begin the next milestone merely because a PR is review-ready.
Implementation readiness is not accepted milestone completion.

Complete authorized reversible local work and routine delivery mechanics without
repeated permission requests. Fix task-local implementation/test/lint/staging/PR
metadata defects autonomously; consequential decisions remain user-controlled.
Never weaken tests or acceptance criteria to make a branch green.

Use [proportional verification](docs/family-food/verification-policy.md): every
domain change needs meaningful affected tests; docs-only work does not default
to full regression. Run required checks, report exact failures/unavailable checks,
and never claim an unexecuted check passed. Repeat or broaden after changes,
failure/fix or a concrete unresolved concern, not merely because checks exist.

## Public repository and durable memory

Never commit secrets, credentials, `.env`, real personal/health records, local
databases or development environments. Use placeholders and documented
variable names; keep sensitive payloads out of logs.

Persist durable decisions in `docs/`; execution authorization/focus in
`state/current-focus.md`, verified progress in `state/progress.md`, and continuation
context in `state/handoff.md`. Link to canonical detail instead of duplicating it.
Chat history alone is not durable project memory.
