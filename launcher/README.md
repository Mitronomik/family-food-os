# FamilyFoodOS source-run launcher

This directory contains the transitional source-run launcher for
**FamilyFoodOS**. It remains development and migration scaffolding while the
hosted responsive Web/PWA defined by ADR 0030 is built under later migration
gates; it is not the target consumer delivery.

Current scope:

- resolve repository/backend/frontend runtime paths;
- build safe localhost runtime configuration;
- explicitly run backend startup initialization in `user` mode by default;
- start the FastAPI backend on `127.0.0.1:8000`;
- optionally open the browser at the current frontend development URL placeholder.

This is **not** final packaging. The inherited macOS consumer `.app` and ZIP
path are retired under ADR 0031; this launcher is not a `.dmg`, installer,
Electron shell, Docker runtime, service daemon, or auto-updater.

Developer command:

```bash
python3 -m launcher.main --no-browser
```

The launcher uses the current backend path contract: `FAMILY_FOOD_USER_DATA_DIR`
may override the default `~/Documents/FamilyFoodOS` user-data root, whose
database is `data/family_food.sqlite`; `FAMILY_FOOD_DB_PATH` may select an
explicit development database. The old source-product variables are not
aliases. User data must stay outside the repository/package directory.
