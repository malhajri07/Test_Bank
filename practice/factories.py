"""
Factory Boy factories for practice app.
"""

import factory
from django.contrib.auth import get_user_model

from catalog.factories import TestBankFactory
from practice.models import UserTestAccess, UserTestSession

User = get_user_model()


class UserTestAccessFactory(factory.django.DjangoModelFactory):
    """Factory for UserTestAccess."""

    class Meta:
        model = UserTestAccess

    user = factory.SubFactory('accounts.factories.UserFactory')
    test_bank = factory.SubFactory(TestBankFactory)
    is_active = True
    attempts_allowed = 3
    attempts_used = 0


class UserTestSessionFactory(factory.django.DjangoModelFactory):
    """Factory for UserTestSession."""

    class Meta:
        model = UserTestSession

    user = factory.SubFactory('accounts.factories.UserFactory')
    test_bank = factory.SubFactory(TestBankFactory)
    status = 'completed'
    total_questions = 10
    correct_answers = 8
    score = 80.00
