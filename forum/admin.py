"""
Admin configuration for Forum app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import ForumCategory, ForumTopic, ForumPost


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    """Admin interface for ForumCategory model."""
    
    list_display = ('name', 'slug', 'order', 'is_active', 'get_topic_count', 'get_post_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_topic_count(self, obj):
        """Display topic count."""
        return obj.get_topic_count()
    get_topic_count.short_description = 'Topics'
    
    def get_post_count(self, obj):
        """Display post count."""
        return obj.get_post_count()
    get_post_count.short_description = 'Posts'


@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    """Admin interface for ForumTopic model."""
    
    list_display = ('title', 'category', 'author', 'is_pinned', 'is_locked', 'views_count', 'get_reply_count', 'created_at', 'last_activity_at')
    list_filter = ('category', 'is_pinned', 'is_locked', 'created_at', 'category')
    search_fields = ('title', 'content', 'author__username', 'author__email')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'last_activity_at', 'views_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'title', 'slug', 'content', 'author')
        }),
        ('Moderation', {
            'fields': ('is_pinned', 'is_locked')
        }),
        ('Statistics', {
            'fields': ('views_count', 'created_at', 'updated_at', 'last_activity_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_reply_count(self, obj):
        """Display reply count."""
        return obj.get_reply_count()
    get_reply_count.short_description = 'Replies'


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    """Admin interface for ForumPost model."""
    
    list_display = ('topic', 'author', 'is_edited', 'created_at', 'content_preview')
    list_filter = ('is_edited', 'created_at', 'topic__category')
    search_fields = ('content', 'author__username', 'topic__title')
    readonly_fields = ('created_at', 'updated_at', 'edited_at')
    
    fieldsets = (
        ('Post Information', {
            'fields': ('topic', 'author', 'content')
        }),
        ('Metadata', {
            'fields': ('is_edited', 'edited_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Display preview of post content."""
        content = obj.content
        # Remove HTML tags for preview
        import re
        text = re.sub('<[^<]+?>', '', content)
        if len(text) > 100:
            return text[:100] + '...'
        return text
    content_preview.short_description = 'Content Preview'
