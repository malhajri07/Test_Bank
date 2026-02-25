"""
Admin configuration for practice app.

Registers UserTestAccess, UserTestSession, and UserAnswer models with Django admin.
"""

from django.contrib import admin

from .models import UserAnswer, UserTestAccess, UserTestSession


@admin.register(UserTestAccess)
class UserTestAccessAdmin(admin.ModelAdmin):
    """Admin interface for UserTestAccess model."""
    list_display = ('user', 'test_bank', 'purchased_at', 'expires_at', 'is_active')
    list_filter = ('is_active', 'purchased_at', 'expires_at')
    search_fields = ('user__username', 'test_bank__title')
    readonly_fields = ('purchased_at',)
    date_hierarchy = 'purchased_at'


@admin.register(UserTestSession)
class UserTestSessionAdmin(admin.ModelAdmin):
    """Admin interface for UserTestSession model."""
    list_display = ('user', 'test_bank', 'started_at', 'completed_at', 'score', 'status', 'correct_answers', 'total_questions')
    list_filter = ('status', 'started_at', 'test_bank')
    search_fields = ('user__username', 'test_bank__title')
    readonly_fields = ('started_at', 'score', 'calculate_score')
    date_hierarchy = 'started_at'

    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'test_bank', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Results', {
            'fields': ('total_questions', 'correct_answers', 'score')
        }),
    )


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    """Admin interface for UserAnswer model."""
    list_display = ('session', 'question', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'answered_at', 'question__question_type')
    search_fields = ('session__user__username', 'question__question_text')
    readonly_fields = ('answered_at',)
    filter_horizontal = ('selected_options',)  # Better UI for ManyToMany field
    date_hierarchy = 'answered_at'
