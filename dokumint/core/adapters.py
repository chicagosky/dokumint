from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class DokumintAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return settings.REGISTRATION_OPEN


class DokumintSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return settings.REGISTRATION_OPEN
