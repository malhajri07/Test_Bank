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
    # Blog
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    # Blog comments
    path('blog/comment/<int:comment_id>/reply/', views.add_comment_reply, name='add_comment_reply'),
]

