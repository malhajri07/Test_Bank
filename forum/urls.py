"""
URL configuration for Forum app.
"""

from django.urls import path

from . import views

app_name = 'forum'

urlpatterns = [
    # Forum index
    path('', views.forum_index, name='index'),

    # Category detail
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),

    # Category create (AJAX)
    path('category/create/', views.category_create_ajax, name='category_create'),

    # Topic create
    path('topic/create/', views.topic_create, name='topic_create'),
    path('category/<slug:category_slug>/topic/create/', views.topic_create, name='topic_create'),

    # Topic detail
    path('category/<slug:category_slug>/topic/<slug:topic_slug>/', views.topic_detail, name='topic_detail'),

    # Topic reply
    path('category/<slug:category_slug>/topic/<slug:topic_slug>/reply/', views.topic_reply, name='topic_reply'),

    # Post edit
    path('post/<int:post_id>/edit/', views.post_edit, name='post_edit'),
]

