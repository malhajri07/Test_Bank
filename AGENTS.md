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

- **Stripe guard**: `payments/stripe_integration.py` raises `ValueError` at import time if `STRIPE_SECRET_KEY` is empty. The `.env` file must have a non-empty `STRIPE_SECRET_KEY` (dummy values like `sk_test_devdummy` work for non-payment flows).
- **pytest import-mode**: The repo has identically-named test files across apps (e.g. `test_views.py` in both `catalog/tests/` and `practice/tests/`) without `__init__.py` files. You must run pytest with `--import-mode=importlib` to avoid collection errors.
- **Stress tests**: Tests under `stress_tests/` can take very long or hang. Exclude them for fast feedback: `pytest --import-mode=importlib --ignore=stress_tests --benchmark-disable`.
- **Pre-existing test failures**: Several tests in `catalog/tests/` and `practice/tests/` fail due to test data using invalid model field values (e.g. `difficulty_level='beginner'` which is not a valid choice). These are pre-existing issues, not caused by environment setup.
- **NPM_BIN_PATH**: The `.env` must set `NPM_BIN_PATH` to the actual npm path. In cloud VMs with nvm: `/home/ubuntu/.nvm/versions/node/v22.22.0/bin/npm`. Check with `which npm`.
- **No linter configured**: The repo has no flake8/ruff/pylint config. Use `python manage.py check` for Django system checks.

### Standard Commands

See `README.md` for full command reference. Quick summary:

- **Tests**: `source venv/bin/activate && pytest --import-mode=importlib --ignore=stress_tests --benchmark-disable`
- **Django checks**: `source venv/bin/activate && python manage.py check`
- **Migrations**: `source venv/bin/activate && python manage.py migrate`
- **Tailwind build**: `source venv/bin/activate && python manage.py tailwind build`
- **Dev server**: `source venv/bin/activate && python manage.py runserver 0.0.0.0:8000`

### Dev credentials

- Admin user: `admin` / `admin123`
- Database: `testbank_db` / user `postgres` / password `postgres`
