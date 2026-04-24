"""
Post-save signal to ensure every CustomUser has a UserProfile row.

Why this exists:
- The email-signup flow in accounts/views.register creates the UserProfile
  manually after the form saves.
- The Google/social signup flow goes through django-allauth's
  SOCIALACCOUNT_AUTO_SIGNUP path, which creates the User directly without
  touching our register view — no UserProfile is created.
- Any view that does `request.user.profile.<field>` via the OneToOne
  reverse descriptor would then raise UserProfile.DoesNotExist.

get_or_create is idempotent: the email-signup view creating a profile first
is fine; the signal re-running is a no-op when a profile already exists.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
