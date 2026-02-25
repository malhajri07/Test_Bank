"""
Admin configuration for CMS app.

Provides comprehensive admin interfaces for:
- Pages: Static content pages
- Announcements: Site-wide announcements
- Media: File uploads and media management
- ContentBlocks: Reusable content blocks

Includes role-based permissions and rich text editing.
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Announcement, BlogComment, BlogPost, ContentBlock, HeroSlide, Media, Page, Testimonial


# Permission mixins for role-based access
class CMSAdminMixin:
    """Mixin to add CMS permission checks to admin classes."""

    def has_add_permission(self, request):
        """Check if user can add content."""
        # Superusers and staff always have full access
        if request.user.is_superuser or request.user.is_staff:
            return True
        return request.user.is_editor()

    def has_change_permission(self, request, obj=None):
        """Check if user can change content."""
        # Superusers and staff always have full access
        if request.user.is_superuser or request.user.is_staff:
            return True
        return request.user.is_editor()

    def has_delete_permission(self, request, obj=None):
        """Check if user can delete content."""
        # Superusers and staff always have full access
        if request.user.is_superuser or request.user.is_staff:
            return True
        return request.user.is_content_manager()

    def has_view_permission(self, request, obj=None):
        """Check if user can view content."""
        # Superusers and staff always have full access
        if request.user.is_superuser or request.user.is_staff:
            return True
        return request.user.is_editor()


# Custom admin actions
@admin.action(description='Mark selected pages as published')
def make_published(modeladmin, request, queryset):
    """Admin action to publish selected pages."""
    queryset.update(status='published', published_at=timezone.now())


@admin.action(description='Mark selected pages as draft')
def make_draft(modeladmin, request, queryset):
    """Admin action to set selected pages as draft."""
    queryset.update(status='draft')


@admin.action(description='Activate selected announcements')
def activate_announcements(modeladmin, request, queryset):
    """Admin action to activate selected announcements."""
    queryset.update(is_active=True)


@admin.action(description='Deactivate selected announcements')
def deactivate_announcements(modeladmin, request, queryset):
    """Admin action to deactivate selected announcements."""
    queryset.update(is_active=False)


@admin.register(Page)
class PageAdmin(CMSAdminMixin, admin.ModelAdmin):
    """Admin interface for Page model with rich text editing."""

    list_display = ('title', 'slug', 'status', 'is_featured', 'author', 'created_at', 'published_at', 'view_link')
    list_filter = ('status', 'is_featured', 'created_at', 'author')
    search_fields = ('title', 'slug', 'content', 'meta_title', 'meta_description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'published_at', 'author')

    # RichTextField is used directly in the model, so no custom form needed

    # Fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'content')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Publication', {
            'fields': ('status', 'is_featured', 'order', 'published_at')
        }),
        ('Metadata', {
            'fields': ('author', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Admin actions
    actions = [make_published, make_draft]

    def view_link(self, obj):
        """Display link to view page on site."""
        if obj.status == 'published':
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">View</a>', url)
        return '-'
    view_link.short_description = 'View on Site'

    def save_model(self, request, obj, form, change):
        """Set author when creating new page and check publish permissions."""
        if not change:  # New object
            obj.author = request.user

        # Check publish permission (superusers and staff can always publish)
        if obj.status == 'published' and not (request.user.is_superuser or request.user.is_staff or request.user.can_publish_content()):
            obj.status = 'draft'

        super().save_model(request, obj, form, change)


@admin.register(Announcement)
class AnnouncementAdmin(CMSAdminMixin, admin.ModelAdmin):
    """Admin interface for Announcement model."""

    list_display = ('title', 'announcement_type', 'is_active', 'show_on_homepage', 'start_date', 'end_date', 'author', 'created_at', 'status_indicator')
    list_filter = ('announcement_type', 'is_active', 'show_on_homepage', 'created_at', 'author')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at', 'author')

    # RichTextField is used directly in the model, so no custom form needed

    # Fieldsets for better organization
    fieldsets = (
        ('Content', {
            'fields': ('title', 'content', 'announcement_type')
        }),
        ('Visibility', {
            'fields': ('is_active', 'show_on_homepage')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date'),
            'description': 'Set dates to schedule when announcement should be displayed'
        }),
        ('Link (Optional)', {
            'fields': ('link_url', 'link_text'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('author', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Admin actions
    actions = [activate_announcements, deactivate_announcements]

    def status_indicator(self, obj):
        """Display visual indicator of announcement status."""
        if obj.is_currently_active():
            return format_html('<span style="color: green;">●</span> Active')
        return format_html('<span style="color: red;">●</span> Inactive')
    status_indicator.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """Set author when creating new announcement."""
        if not change:  # New object
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Media)
class MediaAdmin(CMSAdminMixin, admin.ModelAdmin):
    """Admin interface for Media model with file preview."""

    list_display = ('title', 'media_type', 'file_preview', 'uploaded_by', 'created_at', 'file_size')
    list_filter = ('media_type', 'created_at', 'uploaded_by')
    search_fields = ('title', 'description', 'alt_text')
    readonly_fields = ('uploaded_by', 'created_at', 'file_preview_large')

    # Fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'media_type')
        }),
        ('File', {
            'fields': ('file', 'file_preview_large', 'alt_text')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def file_preview(self, obj):
        """Display file preview in list view."""
        if obj.file and obj.media_type == 'image':
            return format_html('<img src="{}" style="max-width: 50px; max-height: 50px;" />', obj.file.url)
        return '-'
    file_preview.short_description = 'Preview'

    def file_preview_large(self, obj):
        """Display larger file preview in detail view."""
        if obj.file and obj.media_type == 'image':
            return format_html('<img src="{}" style="max-width: 300px; max-height: 300px;" />', obj.file.url)
        return 'Preview not available for this file type'
    file_preview_large.short_description = 'File Preview'
    file_preview_large.allow_tags = True

    def file_size(self, obj):
        """Display file size."""
        if obj.file:
            size = obj.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return '-'
    file_size.short_description = 'Size'

    def save_model(self, request, obj, form, change):
        """Set uploaded_by when creating new media."""
        if not change:  # New object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContentBlock)
class ContentBlockAdmin(CMSAdminMixin, admin.ModelAdmin):
    """Admin interface for ContentBlock model."""

    list_display = ('name', 'slug', 'block_type', 'author', 'created_at', 'updated_at')
    list_filter = ('block_type', 'created_at', 'author')
    search_fields = ('name', 'slug', 'content')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'author')

    # RichTextField is used directly in the model, so no custom form needed

    # Fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'block_type')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Metadata', {
            'fields': ('author', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set author when creating new content block."""
        if not change:  # New object
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(HeroSlide)
class HeroSlideAdmin(CMSAdminMixin, admin.ModelAdmin):
    """Admin interface for HeroSlide model."""

    list_display = ('title', 'is_active', 'order', 'created_at', 'preview')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Content', {
            'fields': ('title', 'description')
        }),
        ('Background', {
            'fields': ('background_image', 'gradient_from', 'gradient_to'),
            'description': 'Either use a background image or gradient colors'
        }),
        ('Call-to-Action Buttons', {
            'fields': ('primary_button_text', 'primary_button_url', 'secondary_button_text', 'secondary_button_url')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def preview(self, obj):
        """Display preview of slide."""
        if obj.background_image:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 50px;" />', obj.background_image.url)
        return format_html('<div style="width: 100px; height: 50px; background: linear-gradient(to right, {}, {});"></div>', obj.gradient_from, obj.gradient_to)
    preview.short_description = 'Preview'


@admin.register(Testimonial)
class TestimonialAdmin(CMSAdminMixin, admin.ModelAdmin):
    """Admin interface for Testimonial model."""

    list_display = ('name', 'role', 'is_active', 'order', 'created_at', 'photo_preview')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'role', 'quote')
    readonly_fields = ('created_at', 'updated_at', 'photo_preview_large')

    fieldsets = (
        ('Content', {
            'fields': ('name', 'role', 'quote')
        }),
        ('Photo', {
            'fields': ('photo', 'photo_preview_large')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def photo_preview(self, obj):
        """Display photo preview in list view."""
        if obj.photo:
            return format_html('<img src="{}" style="max-width: 50px; max-height: 50px; border-radius: 50%;" />', obj.photo.url)
        return '-'
    photo_preview.short_description = 'Photo'

    def photo_preview_large(self, obj):
        """Display larger photo preview in detail view."""
        if obj.photo:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 50%;" />', obj.photo.url)
        return 'No photo uploaded'
    photo_preview_large.short_description = 'Photo Preview'


@admin.register(BlogPost)
class BlogPostAdmin(CMSAdminMixin, admin.ModelAdmin):
    """Admin interface for BlogPost model with rich text editing."""

    list_display = ('title', 'slug', 'status', 'is_featured', 'author', 'published_at', 'created_at', 'view_link')
    list_filter = ('status', 'is_featured', 'created_at', 'published_at', 'author')
    search_fields = ('title', 'slug', 'excerpt', 'content', 'meta_title', 'meta_description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'published_at', 'author', 'featured_image_preview')

    # Fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'content')
        }),
        ('Featured Image', {
            'fields': ('featured_image', 'featured_image_preview')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Publication', {
            'fields': ('status', 'is_featured', 'published_at')
        }),
        ('Metadata', {
            'fields': ('author', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Admin actions
    actions = [make_published, make_draft]

    def featured_image_preview(self, obj):
        """Display featured image preview."""
        if obj.featured_image:
            return format_html('<img src="{}" style="max-width: 300px; max-height: 200px;" />', obj.featured_image.url)
        return 'No featured image uploaded'
    featured_image_preview.short_description = 'Featured Image Preview'

    def view_link(self, obj):
        """Display link to view blog post on site."""
        if obj.status == 'published':
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">View</a>', url)
        return '-'
    view_link.short_description = 'View on Site'

    def save_model(self, request, obj, form, change):
        """Set author when creating new blog post and check publish permissions."""
        if not change:  # New object
            obj.author = request.user

        # Check publish permission (superusers and staff can always publish)
        if obj.status == 'published' and not (request.user.is_superuser or request.user.is_staff or request.user.can_publish_content()):
            obj.status = 'draft'

        super().save_model(request, obj, form, change)


@admin.register(BlogComment)
class BlogCommentAdmin(CMSAdminMixin, admin.ModelAdmin):
    """Admin interface for BlogComment model."""

    list_display = ('user', 'blog_post', 'parent', 'is_approved', 'created_at', 'content_preview')
    list_filter = ('is_approved', 'created_at', 'blog_post')
    search_fields = ('content', 'user__username', 'user__email', 'blog_post__title')
    readonly_fields = ('created_at', 'updated_at', 'user', 'blog_post', 'parent')

    fieldsets = (
        ('Comment Information', {
            'fields': ('blog_post', 'user', 'parent', 'content')
        }),
        ('Moderation', {
            'fields': ('is_approved',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def content_preview(self, obj):
        """Display preview of comment content."""
        if len(obj.content) > 100:
            return obj.content[:100] + '...'
        return obj.content
    content_preview.short_description = 'Content Preview'

    actions = ['approve_comments', 'unapprove_comments']

    @admin.action(description='Approve selected comments')
    def approve_comments(self, request, queryset):
        """Approve selected comments."""
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} comments approved.')

    @admin.action(description='Unapprove selected comments')
    def unapprove_comments(self, request, queryset):
        """Unapprove selected comments."""
        queryset.update(is_approved=False)
        self.message_user(request, f'{queryset.count()} comments unapproved.')
