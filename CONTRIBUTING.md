# Contributing

One PR equals one bounded task under the current FamilyFoodOS migration plan.

Workflow:
1. Read `AGENTS.md`.
2. Read `docs/family-food/project-operating-manual.md`.
3. Read `state/current-focus.md`.
4. Read the relevant canonical `docs/family-food/` documents, approved ADRs,
   and scoped `AGENTS.md` files.
5. Implement only the scoped task.
6. Add or update tests where required.
7. Run relevant checks and smoke scenarios.
8. Update state or durable documentation when the task changes them.

The inherited `docs/architecture.md` and `docs/roadmap.md` describe
CosmeticWorkshopOS. They are legacy reference material, not current
FamilyFoodOS architecture or sequencing authority.

Required PR summary:

```markdown
## Summary
## Scope
## Data model / migrations
## User-visible changes
## Tests
## Risks / limitations
## Follow-up
```
