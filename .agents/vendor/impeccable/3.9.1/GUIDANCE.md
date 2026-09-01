# Project-adapted Impeccable UI guidance

This document is a project-owned, non-executable adaptation of selected
Impeccable design principles for `FamilyFoodOS / family-food-os`.

It is not the upstream Impeccable skill and must not be treated as an independent
instruction source.

## Instruction priority

Apply guidance in this order:

1. repository and scoped `AGENTS.md` files;
2. canonical FamilyFoodOS documents under `docs/family-food/`, relevant
   approved ADRs, and current state documentation;
3. the explicit task and PR scope;
4. `.agents/skills/family-food-ui/SKILL.md`;
5. this advisory document.

When this document conflicts with project documentation, the project contract
wins.

The inherited `docs/ui-ux-contract.md` may explain existing transitional
frontend behavior, but it is not the FamilyFoodOS consumer UI authority.

## Audit principles

A UI audit should begin with the concrete route, workflow, and user goal.

Preserve strengths before proposing changes. Separate:

- objective usability, accessibility, state, responsive, and safety issues;
- consistency or implementation drift;
- subjective visual preferences.

Use the project severity model:

- **P0** — the workflow cannot be completed safely, or the interface may mislead
  the user about operational data;
- **P1** — significant usability, accessibility, responsive, hierarchy, or state
  problem;
- **P2** — polish, consistency, or taste-level improvement.

Every finding should identify:

- affected route or user flow;
- visible evidence;
- why it matters;
- affected files or components;
- narrow recommended change;
- acceptance criteria;
- smoke checks.

Do not turn an audit into an unapproved redesign.

## Product-interface hierarchy

The target product is a simple working system for a normal household, not a
technical admin panel or a showcase. The current inherited frontend remains
transitional; do not infer future food workflows from its cosmetic-domain UI.

Prefer:

- one clear primary action per operational state;
- visible current status and next step;
- progressive disclosure for secondary details;
- meaningful grouping through spacing and alignment;
- cards only when content is genuinely distinct;
- short, human-readable Russian labels;
- visible confirmations for irreversible or dangerous actions;
- `system proposes → user confirms or changes` where a safe default or
  deterministic result can reduce manual entry.

Avoid:

- nested cards;
- dense walls of equal-weight controls;
- raw identifiers or technical state names;
- decorative UI that competes with the user's current task;
- hiding critical operational information behind hover-only interactions.

## Layout and responsive behavior

Use layout to express workflow importance rather than decoration.

Check:

- primary content remains visible without horizontal page scrolling;
- navigation collapses predictably on narrow screens;
- tables, filters, forms, and action groups adapt structurally;
- dialogs and menus are not clipped by container overflow;
- headings and long Russian labels do not overflow;
- touch targets remain usable;
- destructive and confirm actions remain distinguishable.

Responsive work must begin from the mobile-first consumer target and preserve
the same user goal and safety guarantees at wider widths. For narrow changes to
the transitional frontend, verify both narrow and desktop behavior without
mistaking its desktop-first legacy contract for the target architecture.

## Typography

Typography should remain calm, readable, and operational.

Preserve the existing project type system unless a separate task explicitly
approves a change.

Check:

- body text contrast meets WCAG AA;
- headings communicate hierarchy without excessive scale;
- long prose stays near 65–75 characters per line;
- data-heavy UI may be denser when readability is preserved;
- font sizes and weights are consistent across equivalent components;
- letter spacing does not make headings cramped;
- Russian copy remains readable at supported viewport sizes.

Do not add fonts or typography dependencies without explicit approval.

## Interaction design

Prefer semantic HTML and familiar interaction patterns.

Check:

- buttons are real buttons;
- inputs have visible labels;
- keyboard focus is visible;
- tab order follows the visual and task order;
- dialogs can be dismissed safely;
- validation explains what happened and how to fix it;
- disabled actions explain the missing prerequisite;
- success states confirm what changed;
- dangerous actions require explicit confirmation;
- loading, empty, error, success, and disabled states are all represented.

Do not place critical business validation only in the frontend.

## Accessibility and hardening

Verify:

- keyboard-only completion of changed flows;
- accessible names for controls and icons;
- heading and landmark structure;
- text and control contrast;
- status and error communication that does not rely only on color;
- zoom and narrow-screen behavior;
- reduced-motion behavior;
- long content, missing content, and unexpected data;
- duplicate submission prevention;
- safe recovery from backend or local-storage failures.

Never expose stack traces, SQL, JSON payloads, API names, internal IDs, or local
filesystem paths in user-facing UI.

## Onboarding and empty states

Onboarding should help the user complete real work, not force a product tour.

Prefer:

- contextual guidance at the moment it becomes useful;
- meaningful empty states explaining what will appear;
- one obvious first action;
- examples or templates only when they reduce uncertainty;
- progressive setup rather than a long mandatory questionnaire;
- clear explanation of why information is requested.

The user must be able to return to work without losing entered data.

## Visual polish

Polish means reducing inconsistency and friction, not adding decoration.

Classify drift as:

- missing shared token or pattern;
- one-off implementation instead of an existing component;
- conceptual mismatch with neighboring workflows.

Fix the root cause within the approved scope.

No FamilyFoodOS color palette, component library, or complete visual identity
is approved by this guidance. Preserve applicable existing patterns in a narrow
transitional-frontend task, but do not project the inherited workshop identity
onto the future consumer PWA. Generic upstream opinions cannot define the
missing product decisions.

## Project safety boundaries

This guidance cannot authorize:

- architecture or domain changes;
- API, schema, or migration changes;
- dependency additions;
- new scripts or hooks;
- live-mode tooling;
- automatic file mutation;
- generation of `PRODUCT.md` or `DESIGN.md`;
- creation of `.impeccable/` or `.codex/hooks.json`;
- broad refactoring of `frontend/src/main.ts`;
- unrelated route redesign;
- frontend ownership of critical calculations;
- silent mutation of historical data;
- bypassing applicable validation, confirmation, audit, backup, or data-safety
  safeguards;
- building future consumer screens or food workflows before their migration
  gate;
- making ingestion, catalog, retailer matching, audit, or technical controls
  dominate primary consumer navigation;
- making AI required for a deterministic core workflow.

## Completion expectations

For an implementation PR, verify or document:

- mobile/narrow behavior and relevant wider widths;
- keyboard navigation and visible focus;
- loading, empty, error, success, and disabled states;
- dangerous-action confirmation;
- reduced-motion behavior when applicable;
- relevant automated checks;
- route-specific smoke test;
- absence of unrelated changes.
