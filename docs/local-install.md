# Local Install for Developers

Status: **CURRENT FOR SOURCE-RUN DEVELOPMENT ONLY**.

FamilyFoodOS consumer delivery targets a hosted Web/PWA. These commands are
transitional developer scaffolding; no local consumer package is planned.

Planned/available commands:

- `make setup` - install backend and frontend developer dependencies.
- `make dev` - print separate backend/frontend development commands.
- `make run-local` - run the launcher MVP without opening the browser.
- `python3 -m launcher.main --no-browser` - start the minimal local backend runtime directly.
- `make test` - run backend and launcher tests from the repository root.

Development persistence defaults:

- Default development SQLite path: `.local/family_food.sqlite` at the repository root.
- Override the development database file with `FAMILY_FOOD_DB_PATH=/path/to/family_food.sqlite`.
- User-mode startup uses the user data resolver and creates data directories only through explicit startup initialization.
- Override the user-mode data directory with `FAMILY_FOOD_USER_DATA_DIR=/path/to/user-data`.

Launcher MVP behavior:

- Safe defaults: host `127.0.0.1`, backend port `8000`, frontend URL placeholder `http://127.0.0.1:5173`.
- Default mode is `user`, so startup uses the user data directory and the existing backup-before-migration path.
- The launcher starts only a local backend process. It does not provide a
  consumer desktop package.
- The launcher is developer-facing migration scaffolding; normal consumers will
  use the separately gated hosted Web/PWA.
