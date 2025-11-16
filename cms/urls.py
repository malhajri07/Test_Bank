"""
URL configuration for CMS app.

Routes for:
- Static pages
- Content blocks (via template tags)
"""

from django.urls import path
from . import views

app_name = 'cms'

urlpatterns = [
    # Static page detail
    path('page/<slug:slug>/', views.page_detail, name='page_detail'),
]

