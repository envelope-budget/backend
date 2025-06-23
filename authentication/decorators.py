from functools import wraps
from django.views.decorators.csrf import csrf_exempt


def conditional_csrf_exempt(view_func):
    """
    Decorator that exempts mobile app requests from CSRF validation
    while keeping it enabled for web requests.
    """

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Check if request is from mobile app
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        is_mobile_app = (
            "EnvelopeBudgetApp" in user_agent
            or request.META.get("HTTP_X_MOBILE_APP") == "true"
            or request.META.get("HTTP_X_REQUESTED_WITH") == "EnvelopeBudgetApp"
        )

        if is_mobile_app:
            # Exempt from CSRF for mobile
            return csrf_exempt(view_func)(request, *args, **kwargs)
        else:
            # Normal CSRF validation for web
            return view_func(request, *args, **kwargs)

    return wrapped_view
