from accounts.models import Account
from budgets.models import Budget


def global_context(request):
    if not request.user.is_authenticated:
        return {}

    budget = None
    user_budgets = Budget.objects.filter(user=request.user)
    active_budget_id = request.session.get("budget")

    for b in user_budgets:
        if str(b.id) == active_budget_id:
            budget = b
            break

    if not budget:
        budget_count = len(user_budgets)
        if budget_count == 0:
            budget = Budget.objects.create(user=request.user, name="My Budget")
            _create_sample_envelopes(budget)
        elif budget_count == 1:
            budget = user_budgets.first()
        else:
            # use the last opened budget
            budget = (
                Budget.objects.filter(user=request.user).order_by("-created_at").first()
            )
        request.session["budget"] = budget.id

    all_accounts = Account.objects.filter(budget=budget)
    accounts = []
    credit_cards = []
    loans = []
    for a in all_accounts:
        if a.type in ("checking", "savings"):
            accounts.append(a)
        if a.type == "credit_card":
            credit_cards.append(a)
        if a.type == "loan":
            loans.append(a)

    return {
        "accounts": accounts,
        "credit_cards": credit_cards,
        "loans": loans,
        "budget": budget,
        "budgets": user_budgets,
    }


def _create_sample_envelopes(budget):
    from envelopes.models import Category, Envelope

    envelopes = {
        "Necessities": [
            "⛪️ Tithing",
            "🏡 Mortgage/Rent",
            "🚰 Utilities",
            "⛽️ Gasoline",
            "👩‍💼 Insurance",
            "🛒 Groceries",
            "📱 Phone",
            "🚗 Auto Maintenance",
            "🏥 Medical",
            "🦷 Dental",
        ],
        "Savings": [
            "💰 Savings",
            "🚨 Emergency Fund",
        ],
        "Quality of Life": [
            "💝 Charitable Gifts",
            "🍽️ Eating Out",
            "👚 Clothing",
            "🎁 Gifts",
            "🐶 Pets",
            "🏋️‍♀️ Gym/Fitness",
            "💇‍♀️ Hair Cuts/Care",
            "🦄 Miscellaneous",
        ],
        "Just for Fun": [
            "🎄 Christmas",
            "🧢 Blow Money",
            "🍿 Dates/Entertainment",
            "🏝️ Vacation",
            "🛋️ Decor",
        ],
    }

    categories = [
        Category(budget=budget, name=name, sort_order=index)
        for index, name in enumerate(envelopes.keys())
    ]

    Category.objects.bulk_create(categories)

    envelope_list = [
        Envelope(
            budget=budget,
            category=category,
            name=envelope_name,
            sort_order=sort_order,
        )
        for category in categories
        for sort_order, envelope_name in enumerate(envelopes[category.name], start=1)
    ]

    Envelope.objects.bulk_create(envelope_list)
