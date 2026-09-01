# backend/app/persistence/AGENTS.md

Scope: new FamilyFoodOS persistence infrastructure under `backend/app/persistence/`.

- Use synchronous SQLAlchemy 2.x Core only.
- Do not use the SQLAlchemy ORM or an async database stack.
- Do not add Alembic during the SQLite phase. The existing custom migration runner remains the sole SQLite schema authority.
- Never use `MetaData.create_all()` for production schema management.
- PR2-B introduces no food tables, food migrations or business semantics.
- Concrete SQLAlchemy, DBAPI and driver types may exist only inside this infrastructure package.
- Application/domain-facing contracts must remain driver-independent and must not expose connections, transactions, rows or SQL expressions.
- Persistence repositories share the active adapter connection supplied by the concrete Unit of Work and never commit independently.
