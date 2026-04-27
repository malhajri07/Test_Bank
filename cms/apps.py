from django.apps import AppConfig


class CmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cms"

    def ready(self):
        # Wire post_save signals — IndexNow ping on blog/page publish/update.
        from . import signals  # noqa: F401
