# Backend contract

Scope: `backend/`.

- Keep API handlers thin: validate input, call application services, return
  explicit schemas/errors. Business rules belong in domain/services.
- Persisted schema changes require migrations and preservation of existing data.
- Use `Decimal`, never `float`, for critical numeric calculations.
- Preserve transaction boundaries and data integrity; do not hide business
  decisions in data-access code.
- Test affected behavior, validation and failure paths; select integration,
  transaction and migration checks using the verification policy.
- Keep secrets and private personal/health payloads out of logs and fixtures.
- Inherited CosmeticWorkshopOS entities and workflows apply only when an
  explicitly scoped legacy task touches them. They are not universal food
  import, inventory, production or audit requirements.
