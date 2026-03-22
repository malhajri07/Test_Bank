"""
Celery configuration for testbank_platform.

Used for async tasks: exam grading, PDF certificate generation, email dispatch.
"""

from celery import Celery

app = Celery('testbank_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery connection."""
    print(f'Request: {self.request!r}')
