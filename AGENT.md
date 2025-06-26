# Envelope Budget Backend - Agent Guide

## Commands

- **Test**: `python manage.py test` (all tests), `python manage.py test transactions` (single app)
- **Run**: `./run` (development server)
- **Lint**: `pylint <file>` (Python), `pnpm run biome:check` (JS/TS)
- **Format**: `pnpm run biome:format` (JS/TS), follows Biome config
- **DB**: `python manage.py migrate` (migrate), `python manage.py makemigrations` (create migrations)

## Architecture

- **Django** budget management app with Django Ninja APIs
- **Apps**: budgets, transactions, accounts, envelopes, authentication, reports, mobile
- **Frontend**: HTMX + Alpine.js + Flowbite & Tailwind CSS
- **Database**: SQLite (development), configurable via settings, PostgreSQL (production)
- **APIs**: Django Ninja routers in each app's `apis.py` or `api.py`

## Code Style

- **Python**: snake_case, 100 char line limit, PEP 8, no docstrings required, Black formatting enforced
- **JS**: Biome formatting (2 spaces, single quotes, semicolons)
- **Imports**: Use absolute imports, Django standard import order
- **Models**: Use Django ORM, snake_case fields, PascalCase classes
- **APIs**: Use Django Ninja schemas, type hints required
- **Templates**: Django templates with HTMX attributes

## Notes

Assume the development serving is running. You can access the development site at http://127.0.0.1:8007. The Ninja docs
can be found at http://127.0.0.1:8007/api/docs. Django admin can be found at http://127.0.0.1:8007/admin/.
