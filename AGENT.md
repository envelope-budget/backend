# Envelope Budget Backend - Agent Guide

## Commands

- **Test**: `python manage.py test` (all tests), `python manage.py test transactions` (single app)
- **Run**: `python manage.py runserver` (development server)
- **Lint**: `pylint <file>` (Python), `pnpm run biome:check` (JS/TS)
- **Format**: `pnpm run biome:format` (JS/TS), follows Biome config
- **DB**: `python manage.py migrate` (migrate), `python manage.py makemigrations` (create migrations)

## Architecture

- **Django** budget management app with Django Ninja APIs
- **Apps**: budgets, transactions, accounts, envelopes, authentication, reports, mobile
- **Frontend**: HTMX + Alpine.js + Tailwind CSS
- **Database**: SQLite (development), configurable via settings
- **APIs**: Django Ninja routers in each app's `apis.py`

## Code Style

- **Python**: snake_case, 100 char line limit, PEP 8, no docstrings required
- **JS**: Biome formatting (2 spaces, single quotes, semicolons)
- **Imports**: Use absolute imports, Django standard import order
- **Models**: Use Django ORM, snake_case fields, PascalCase classes
- **APIs**: Use Django Ninja schemas, type hints required
- **Templates**: Django templates with HTMX attributes
