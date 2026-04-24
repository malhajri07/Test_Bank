"""
Custom allauth adapter so Google sign-in never drops into the social-
signup confirmation page. Two behaviors:

1. Link to an existing local user by email. If the Google account's
   verified email matches an existing user, attach the SocialAccount to
   that user and log them in — no duplicate account, no signup form.

2. Guarantee a unique username when auto-signing up. Without this, when
   allauth's derived username collides (e.g. the local portion of the
   email is already taken), auto-signup fails and the user sees the
   unstyled /accounts/3rdparty/signup/ form.
"""

from allauth.account.utils import filter_users_by_email
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.utils import generate_unique_username


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Attach a new SocialAccount to an existing user matched by email
        before allauth decides to show the signup form.
        """
        # Already linked to a user — nothing to do.
        if sociallogin.is_existing:
            return

        email = (sociallogin.account.extra_data or {}).get('email')
        if not email:
            return

        users = filter_users_by_email(email)
        if not users:
            return

        # One user per email in this app; pick the first if multiple.
        sociallogin.connect(request, users[0])

    def populate_user(self, request, sociallogin, data):
        """
        Ensure the user allauth is about to create has a unique username
        so auto-signup actually completes.
        """
        user = super().populate_user(request, sociallogin, data)
        username = (user.username or '').strip()

        if not username or _username_is_taken(username):
            email = (data.get('email') or '').strip()
            base_hints = [
                username,
                email.split('@', 1)[0] if '@' in email else email,
                data.get('name') or '',
                'user',
            ]
            base_hints = [h for h in base_hints if h]
            user.username = generate_unique_username(base_hints)
        return user


def _username_is_taken(username):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(username__iexact=username).exists()
