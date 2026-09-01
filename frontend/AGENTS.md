# frontend/AGENTS.md

Scope: everything under `frontend/`.

Frontend-wide rules:

- Use Russian, human-readable labels and messages for user-facing UI.
- Do not show raw stack traces, internal IDs, database errors or developer-centric names to the user.
- Every empty state must explain what is missing and what the user can do next.
- Dangerous or destructive actions require clear confirmation.
- The frontend must not implement critical business calculations alone.
- The backend API remains the source of truth for critical calculations and
  operational facts in both inherited bounded contexts and future FamilyFoodOS
  contexts.
- Frontend forms must guide the user with clear validation messages and next actions.
- Frontend changes require a build check; user-visible workflow changes also require relevant smoke testing.
- The inherited vanilla frontend and its cosmetic-domain workflows are
  transitional migration scaffolding. Do not mechanically relabel them as food
  workflows or build the future consumer PWA before its migration gate.

UI/UX contract references:

- For frontend, visual, accessibility, responsive, or motion work, follow the
  root FamilyFoodOS reading order, then read `docs/ui-skill-policy.md` and
  `.agents/skills/family-food-ui/SKILL.md` before changing UI.
- `docs/ui-ux-contract.md` is an inherited CosmeticWorkshopOS contract. It may
  explain the transitional frontend's existing behavior, but it is not the
  canonical FamilyFoodOS consumer UI contract.
- Verify affected routes at desktop and narrow-screen widths when UI changes are made.
- Changed flows must account for loading, empty, error, success, and disabled states.
- Preserve keyboard navigation, visible focus, and reduced-motion expectations.
- Project documentation and architecture rules override third-party design skills.
