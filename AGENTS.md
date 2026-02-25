# AGENTS.md

## Cursor Cloud specific instructions

### Project Overview

Exam Stellar is a Django-based test bank e-commerce platform. See `README.md` for full details.

### Services

| Service | How to run | Port |
|---------|-----------|------|
| PostgreSQL | `sudo pg_ctlcluster 16 main start` | 5432 |
| Django dev server | `source venv/bin/activate && python manage.py runserver 0.0.0.0:8000` | 8000 |

### Key Gotchas

- **Stripe guard**: `payments/stripe_integration.py` lazily initializes Stripe on first use. The `.env` file must have a non-empty `STRIPE_SECRET_KEY` (dummy values like `sk_test_devdummy` work for non-payment flows).
- **pytest import-mode**: `pyproject.toml` configures `--import-mode=importlib` automatically. Identically-named test files across apps have `__init__.py` files for proper namespacing.
- **Stress tests**: Tests under `stress_tests/` can take very long or hang. Exclude them for fast feedback: `pytest --ignore=stress_tests --benchmark-disable`.
- **test_email.py**: This file uses `input()` and is not a real automated test. Exclude it: `--ignore=test_email.py`.
- **NPM_BIN_PATH**: The `.env` must set `NPM_BIN_PATH` to the actual npm path. In cloud VMs with nvm: `/home/ubuntu/.nvm/versions/node/v22.22.0/bin/npm`. Check with `which npm`.

### Standard Commands

See `README.md` for full command reference. Quick summary:

- **Tests**: `source venv/bin/activate && pytest --ignore=stress_tests --ignore=test_email.py --benchmark-disable`
- **Lint**: `source venv/bin/activate && ruff check accounts/ catalog/ payments/ practice/ forum/ cms/ testbank_platform/`
- **Django checks**: `source venv/bin/activate && python manage.py check`
- **Migrations**: `source venv/bin/activate && python manage.py migrate`
- **Tailwind build**: `source venv/bin/activate && python manage.py tailwind build`
- **Dev server**: `source venv/bin/activate && python manage.py runserver 0.0.0.0:8000`

### Dev credentials

- Admin user: `admin` / `admin123`
- Database: `testbank_db` / user `postgres` / password `postgres`
