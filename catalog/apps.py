from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"

    def ready(self):
        # Wire post_save signals — IndexNow ping on TestBank publish/update.
        from . import signals  # noqa: F401
