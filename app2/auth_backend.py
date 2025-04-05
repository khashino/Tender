from django.contrib.auth.backends import ModelBackend
from .models import App2User

class App2AuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = App2User.objects.get(username=username)
            if user.check_password(password):
                return user
        except App2User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return App2User.objects.get(pk=user_id)
        except App2User.DoesNotExist:
            return None

    def user_can_authenticate(self, user):
        return isinstance(user, App2User) 