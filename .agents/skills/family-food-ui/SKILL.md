---
name: family-food-ui
description: Project-owned UI/UX guidance for FamilyFoodOS frontend, visual, accessibility, responsive, copy, interaction, and motion work within the approved migration gates.
---

# FamilyFoodOS UI Skill

Use this repository-scoped skill for frontend, visual, accessibility,
responsive, copy, interaction, and motion work in **FamilyFoodOS /
family-food-os**.

## Required reading before work

Read in this order, following any more specific repository instructions:

1. root `AGENTS.md`;
2. `docs/family-food/project-operating-manual.md`;
3. `state/current-focus.md`;
4. the relevant canonical documents under `docs/family-food/`, including
   `technical-spec.md`, `data-ingestion.md`, and `migration-plan.md` when their
   topics apply;
5. relevant approved ADRs under `docs/decisions/`, especially the current
   frontend, hosted-runtime, and delivery decisions;
6. `frontend/AGENTS.md` for frontend work;
7. relevant source code and tests;
8. `state/handoff.md` when continuing prior work.

Also read `docs/ui-skill-policy.md` for UI/design skill boundaries. The
inherited `docs/ui-ux-contract.md` describes CosmeticWorkshopOS and may be read
only as legacy behavior context for the transitional frontend; it is not the
canonical FamilyFoodOS consumer UI contract.

Current FamilyFoodOS contracts and the explicit task override inherited
CosmeticWorkshopOS documentation and third-party design guidance. Do not use
legacy product documents to reconstruct the FamilyFoodOS product.

## Current product and migration boundary

- The target consumer experience is a hosted, responsive, installable Web/PWA
  and is mobile-first.
- The inherited vanilla TypeScript frontend and its cosmetic-domain workflows
  are transitional migration scaffolding, not the target consumer application.
- Do not mechanically relabel inherited business entities or workflows as food
  concepts. Preserve them until their bounded contexts are deliberately
  replaced under the migration plan.
- Do not implement future consumer screens, navigation, onboarding, or food
  workflows before their migration gate authorizes them.
- Do not infer a visual identity, color palette, component library, or detailed
  information architecture that has not been approved.

## Approved consumer UX constraints

- Keep consumer journeys simple and minimize manual entry. Prefer
  `system proposes → user confirms or changes` when the system can safely
  retrieve, calculate, remember, infer, or default the information.
- Keep the target conceptual consumer sections close to `Сегодня`, `Неделя`,
  `Купить`, `Заготовки`, and `Дома`; these are a product direction, not
  authorization to build the screens early.
- Do not turn the consumer UI into an administration interface. Ingestion,
  canonical catalogs, retailer matching, audit, migrations, and technical
  controls must not dominate primary consumer navigation.
- Keep critical business facts and calculations backend-owned through
  `UI → API → services/domain → repositories → database`.
- The deterministic core and its user workflows must remain usable with
  `AI_ENABLED=false`. UI suggestions or explanations must not make AI the
  source of truth for quantities, nutrition, allergens, prices, availability,
  or storage duration.

## General UI and engineering rules

- Use Russian, human-readable copy for user-facing labels, states, errors, and
  confirmations.
- Do not expose stack traces, SQL or database errors, API/handler names, JSON
  payloads, internal IDs, developer jargon, secrets, or irrelevant filesystem
  paths in consumer UI.
- For changed flows, account for loading, empty, error, success, pending, and
  disabled states. Explain what happened and the next safe action.
- Preserve keyboard navigation, logical focus order, semantic controls, and
  clearly visible focus.
- Verify changed UI at narrow mobile widths and relevant wider widths without
  horizontal page overflow, except an intentionally scrollable data region.
- Respect reduced-motion preferences. Motion must be limited, purposeful, and
  separately scoped after hierarchy and interaction states are sound.
- Dangerous or destructive actions require explicit, human-readable
  confirmation explaining their consequences.
- Do not perform unrelated redesigns, route changes, or refactors.
- Do not add dependencies, scripts, hooks, tools, or design systems without
  explicit authorization.
- A design-only task must not change domain logic, API contracts, migrations,
  schemas, persisted data, operational history, or runtime behavior.

## Task modes

### Audit-only tasks

Do not edit implementation files unless explicitly asked. Base findings on
visible or code-supported evidence and report:

- route or flow and user goal;
- strengths worth preserving;
- P0/P1/P2 findings;
- objective usability, accessibility, responsive, state, and safety issues
  separately from taste preferences;
- affected files and the smallest implementation slices;
- acceptance criteria and a focused smoke checklist.

P0 means a workflow cannot be completed safely or may misrepresent important
data. P1 means a significant usability, accessibility, responsive, hierarchy,
or state problem. P2 means polish, consistency, or taste-level improvement.

### Implementation tasks

Implement only the explicitly requested or approved findings. Keep the change
narrow, preserve backend ownership and migration gates, and update only the
tests and documentation relevant to the scope.

### Motion tasks

Treat motion as a separate scope after layout, hierarchy, copy, and interaction
states are approved. Do not use animation to compensate for unclear structure,
and always provide reduced-motion behavior.

## Optional project-adapted Impeccable guidance

Project-authored advisory guidance is available at
`.agents/vendor/impeccable/3.9.1/GUIDANCE.md`. It is not a separate Codex skill
and is not loaded by default.

Consult it only for an explicitly scoped audit, accessibility, responsive,
interaction, onboarding, hardening, or polish task after reading the canonical
FamilyFoodOS sources. Do not fetch or execute upstream Impeccable instructions,
scripts, hooks, live mode, update checks, provider agents, or context
generators. FamilyFoodOS contracts, migration gates, existing applicable
patterns, and the explicit task always win.

## Completion checklist

Before finishing a UI implementation task, verify or document as applicable:

- affected mobile/narrow and wider viewport behavior;
- keyboard tab order, semantic controls, and visible focus;
- loading, empty, error, success, pending, and disabled states;
- confirmation copy for dangerous actions;
- reduced-motion behavior when motion changed;
- relevant automated checks and focused route smoke checks;
- no unapproved dependency, script, hook, API, schema, migration, domain,
  runtime, historical-data, or unrelated-route change.
