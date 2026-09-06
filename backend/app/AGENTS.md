# Application layers

Scope: `backend/app/`.

- `api/`: thin HTTP handlers; `schemas/`: explicit request/response contracts.
- `domain/`: business objects, value types and rules; `services/`: use cases,
  calculations and workflows.
- `repositories/`: application/domain data-access contracts; inherited concrete
  repositories may remain transitional `sqlite3` until deliberately replaced.
- `persistence/`: concrete adapters for new FamilyFoodOS contexts.
- `migrations/`: schema evolution; `backend/tests/`: backend behavior tests.
  Inherited `models/` are not a mandate to introduce food ORM models.
- Domain/services never import SQLAlchemy. Driver types, raw connections and
  SQLAlchemy remain inside concrete persistence adapters. Follow the relevant
  canonical architecture contract for new or changed boundaries.
- Repositories persist facts; they do not make hidden business decisions.
- API schemas must not leak database internals. Errors support human-readable,
  actionable frontend messages without exposing driver details.
- Verify changed behavior with success, validation-failure and important edge
  cases at the affected layers.
