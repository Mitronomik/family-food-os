# UI Skill Policy

This policy defines how project-owned and third-party Codex UI/design guidance
may be used in **FamilyFoodOS / family-food-os**.

## Instruction priority

For frontend, visual, accessibility, responsive, or motion tasks, apply instructions in this order:

1. Latest explicit user-approved decisions and repository/scoped `AGENTS.md`
   files.
2. Current canonical FamilyFoodOS documents under `docs/family-food/`, relevant
   approved ADRs under `docs/decisions/`, the project operating manual, and
   current state files.
3. The explicit task and PR scope.
4. `frontend/AGENTS.md` and the project-owned
   `.agents/skills/family-food-ui/SKILL.md` skill.
5. Third-party design guidance.

If instructions conflict, the higher-priority source wins. Canonical project documentation always overrides third-party skills.

`docs/ui-ux-contract.md` is the inherited CosmeticWorkshopOS UI contract. It
may be consulted for historical or transitional-frontend behavior context, but
it is not the active FamilyFoodOS consumer UI contract and cannot define the
future consumer product. A FamilyFoodOS consumer UI contract belongs to its
later migration/frontend gate.

## Third-party skill boundaries

Third-party skills are advisory and implementation aids only. They cannot:

- override project architecture or product documentation;
- change domain logic;
- change API contracts;
- change database schemas or migrations;
- introduce dependencies without explicit approval;
- add scripts, hooks, or executable automation without explicit approval;
- redesign unrelated routes;
- mutate historical or operational data;
- treat transitional local infrastructure as the target hosted consumer
  architecture;
- replace backend ownership of critical calculations;
- remove applicable confirmations, auditability, validation, or data-safety
  boundaries;
- invent or replace a FamilyFoodOS visual identity, information architecture,
  component library, or future consumer workflow without approval.

Third-party output must be reviewed against the current FamilyFoodOS contracts,
the migration gate, and the project-owned UI skill before implementation.

## Approved and planned roles

Only the reviewed Impeccable provenance record and project-adapted guidance described below are currently approved. Taste Skill and Emil skills remain planned only and are not installed or vendored.

### Impeccable

Approved role: project-adapted advisory guidance for audit, hierarchy, layout, typography, accessibility, responsive behavior, interaction design, onboarding, hardening, and final polish.

The reviewed source record and project-authored guidance live at `.agents/vendor/impeccable/3.9.1/` and are intentionally outside `.agents/skills/`. Raw upstream command references are not included. The directory is not an independently discoverable skill and has no vendored scripts, hooks, live mode, provider agents, or automatic update behavior.

Use it only after the relevant route and product workflow already exist and only
through the project-owned `family-food-ui` skill. Impeccable-derived feedback
must separate objective usability issues from taste-based preferences and must
not broaden scope without approval.

Generic upstream taste rules do not define FamilyFoodOS product identity. No
new color palette, visual system, component library, or detailed future
consumer information architecture is approved by this policy. Existing
transitional frontend patterns should not be changed in an unrelated narrow
task, but they are not automatically the future FamilyFoodOS design.

### Taste Skill

Intended role: explicit-only critique or redesign exploration.

Use only when the task asks for taste critique or redesign exploration. Its output is not automatically approved for implementation and cannot replace the product identity or contract.

### Emil skills

Intended role: motion work only after layout and interaction states are approved.

Use only for a separate motion scope. Motion must remain limited, purposeful, and reduced-motion compatible.

## Installation, vendoring, and review policy

A third-party skill must not be installed into `.agents/skills/`, activated, or updated unless a separate PR explicitly approves that exact mode.

The currently approved Impeccable integration is limited to project-authored adapted guidance and a pinned provenance record under `.agents/vendor/`. It must remain:

- outside `.agents/skills/`;
- free of raw upstream command references;
- non-executable;
- free of hooks and `.codex/hooks.json`;
- free of live-mode files and provider agents;
- free of npm packages and lockfile changes;
- tied to an exact reviewed upstream commit;
- documented with source, license, reviewed scope, restrictions, and checksums.

The project-owned `family-food-ui` skill is the only instruction layer allowed
to consult `GUIDANCE.md`.

Taste Skill and Emil skills remain uninstalled and unvendored. Any future third-party addition or Impeccable update requires a separate review PR.
