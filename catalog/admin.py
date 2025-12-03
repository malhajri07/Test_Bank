"""
Admin configuration for catalog app.

Registers Category, SubCategory, Certification, TestBank, Question, and AnswerOption models with Django admin.
Includes inline admin for AnswerOptions within Questions and Certifications within SubCategories.
Includes JSON upload functionality for importing test banks with questions and answers.
"""

from django.contrib import admin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import path
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from .models import Category, SubCategory, Certification, TestBank, TestBankRating, Question, AnswerOption
from .forms import TestBankJSONUploadForm
from .utils import import_test_bank_from_json, parse_json_file


# Inline admin for AnswerOptions (shown within Question admin page)
class AnswerOptionInline(admin.TabularInline):
    """Inline admin for AnswerOptions, displayed within Question admin."""
    model = AnswerOption
    extra = 2  # Show 2 extra empty forms by default
    fields = ('option_text', 'is_correct', 'order')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    list_display = ('name', 'slug', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}  # Auto-generate slug from name
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'image')
        }),
        ('Metadata', {
            'fields': ('level_details',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Inline admin for Certifications (shown within SubCategory admin page)
class CertificationInline(admin.TabularInline):
    """Inline admin for Certifications, displayed within SubCategory admin."""
    model = Certification
    extra = 1  # Show 1 extra empty form by default
    fields = ('name', 'slug', 'description', 'order')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    """Admin interface for SubCategory model."""
    list_display = ('name', 'category', 'order', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    prepopulated_fields = {'slug': ('name',)}  # Auto-generate slug from name
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CertificationInline]  # Show certifications inline
    ordering = ('category', 'order', 'name')
    
    # Fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'slug', 'description')
        }),
        ('Settings', {
            'fields': ('order',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    """Admin interface for Certification model."""
    list_display = ('name', 'subcategory', 'order', 'created_at')
    list_filter = ('subcategory__category', 'subcategory', 'created_at')
    search_fields = ('name', 'description', 'subcategory__name')
    prepopulated_fields = {'slug': ('name',)}  # Auto-generate slug from name
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('subcategory', 'order', 'name')
    
    # Fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('subcategory', 'name', 'slug', 'description')
        }),
        ('Settings', {
            'fields': ('order',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TestBank)
class TestBankAdmin(admin.ModelAdmin):
    """Admin interface for TestBank model with JSON upload functionality."""
    list_display = ('title', 'category', 'subcategory', 'certification', 'difficulty_level', 'price', 'average_rating', 'total_ratings', 'user_count', 'is_active', 'question_count', 'created_at')
    list_filter = ('category', 'subcategory', 'certification', 'difficulty_level', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}  # Auto-generate slug from title
    readonly_fields = ('created_at', 'updated_at', 'question_count', 'user_count', 'average_rating', 'total_ratings')
    
    def user_count(self, obj):
        """Display user count for this test bank."""
        return obj.get_user_count()
    user_count.short_description = 'Users'
    
    def changelist_view(self, request, extra_context=None):
        """Add custom button for JSON upload."""
        extra_context = extra_context or {}
        extra_context['show_json_upload'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    # Fieldsets for better organization in admin
    fieldsets = (
        ('Hierarchy', {
            'fields': ('category', 'subcategory', 'certification'),
            'description': 'Test bank can belong to category, subcategory, or certification. At least one must be selected.'
        }),
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'image')
        }),
        ('Details', {
            'fields': ('difficulty_level', 'price', 'is_active')
        }),
        ('Statistics', {
            'fields': ('question_count', 'user_count', 'average_rating', 'total_ratings'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_count(self, obj):
        """Display question count for the test bank."""
        count = obj.get_question_count()
        return format_html('<span style="color: #8FABD4; font-weight: bold;">{}</span>', count)
    question_count.short_description = 'Questions'
    
    def get_urls(self):
        """Add custom URL for JSON upload."""
        urls = super().get_urls()
        custom_urls = [
            path('upload-json/', self.admin_site.admin_view(self.upload_json_view), name='catalog_testbank_upload_json'),
        ]
        return custom_urls + urls
    
    def upload_json_view(self, request):
        """View for uploading JSON file with test bank data."""
        if request.method == 'POST':
            form = TestBankJSONUploadForm(request.POST, request.FILES)
            if form.is_valid():
                json_file = form.cleaned_data['json_file']
                update_existing = form.cleaned_data.get('test_bank')
                
                try:
                    # Parse JSON file
                    json_data = parse_json_file(json_file)
                    
                    # Import test bank
                    test_bank, questions_count, errors, created_items = import_test_bank_from_json(
                        json_data, 
                        update_existing=update_existing
                    )
                    
                    # Show what was created
                    if created_items:
                        items_msg = 'Created: ' + ', '.join(created_items)
                        messages.info(request, items_msg)
                    
                    if errors:
                        for error in errors:
                            messages.warning(request, error)
                    
                    if questions_count > 0:
                        action = 'updated' if update_existing else 'created'
                        messages.success(
                            request, 
                            f'Successfully {action} test bank "{test_bank.title}" with {questions_count} questions!'
                        )
                        return redirect('admin:catalog_testbank_change', test_bank.pk)
                    else:
                        messages.error(request, 'No questions were imported. Please check your JSON file.')
                        
                except ValidationError as e:
                    # Handle validation errors with better formatting
                    error_message = str(e)
                    # If error is a list, join it
                    if isinstance(e.messages, list):
                        error_message = '\n'.join(e.messages)
                    messages.error(request, f'Validation Error: {error_message}')
                except Exception as e:
                    # Handle other exceptions
                    error_message = str(e)
                    # Clean up nested error messages
                    if 'Error importing test bank:' in error_message:
                        error_message = error_message.replace('Error importing test bank: ', '')
                    messages.error(request, f'Error importing test bank: {error_message}')
        else:
            form = TestBankJSONUploadForm()
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Upload Test Bank from JSON',
            'form': form,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        return render(request, 'admin/catalog/testbank/upload_json.html', context)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for Question model."""
    list_display = ('question_text', 'test_bank', 'question_type', 'order', 'is_active', 'created_at')
    list_filter = ('test_bank', 'question_type', 'is_active', 'created_at')
    search_fields = ('question_text', 'explanation')
    inlines = [AnswerOptionInline]  # Show answer options inline
    readonly_fields = ('created_at', 'updated_at')
    
    # Fieldsets for better organization
    fieldsets = (
        ('Question Details', {
            'fields': ('test_bank', 'question_text', 'question_type', 'explanation')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TestBankRating)
class TestBankRatingAdmin(admin.ModelAdmin):
    """Admin interface for TestBankRating model."""
    list_display = ('user', 'test_bank', 'rating', 'created_at', 'updated_at')
    list_filter = ('rating', 'created_at', 'test_bank')
    search_fields = ('user__username', 'test_bank__title', 'review')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Rating Information', {
            'fields': ('user', 'test_bank', 'rating', 'review')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    """Admin interface for AnswerOption model."""
    list_display = ('option_text', 'question', 'is_correct', 'order', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('option_text', 'question__question_text')
    readonly_fields = ('created_at',)
