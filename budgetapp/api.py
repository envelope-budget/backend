from ninja import NinjaAPI
from ninja.security import django_auth

from budgets.apis import router as budgets_router
from accounts.apis import router as accounts_router
from envelopes.apis import router as envelopes_router
from transactions.apis import router as transactions_router
from authentication.api import router as authentication_router

api = NinjaAPI(title="EnvelopeBudget API", csrf=True)

api.add_router("/budgets", budgets_router)
api.add_router("/accounts", accounts_router)
api.add_router("/envelopes", envelopes_router)
api.add_router("/transactions", transactions_router)
api.add_router("/auth", authentication_router)
