"""
Factory Boy factories for accounts app.
"""

import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for CustomUser."""

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    is_active = True
    is_staff = False

    @factory.lazy_attribute
    def password(self):
        return User.objects.make_random_password()

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', None)
        obj = super()._create(model_class, *args, **kwargs)
        if password:
            obj.set_password(password)
            obj.save()
        return obj
