class BudgetCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only set cookie for authenticated users
        if request.user.is_authenticated:
            budget_id = request.session.get("budget")
            current_cookie = request.COOKIES.get("budget_id")

            # Set the cookie if budget_id exists and is different from current cookie
            if budget_id and str(current_cookie) != str(budget_id):
                response.set_cookie("budget_id", budget_id)

        return response
