from django.contrib.auth.backends import ModelBackend
from .models import App1User

class App1AuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = App1User.objects.get(username=username)
            if user.check_password(password):
                return user
        except App1User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return App1User.objects.get(pk=user_id)
        except App1User.DoesNotExist:
            return None

    def user_can_authenticate(self, user):
        return isinstance(user, App1User) 