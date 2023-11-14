from allauth.account.forms import LoginForm


class UserLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        del self.fields["login"]  # Remove the default 'login' field
        # You can add customizations here if needed
