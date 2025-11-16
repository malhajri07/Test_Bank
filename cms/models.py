"""
CMS app models for content management.

This module defines models for:
- Page: Static pages (About, Terms, Privacy, etc.)
- Announcement: Site-wide announcements/banners
- Media: File uploads and media management
- ContentBlock: Reusable content blocks for pages
"""

from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField

User = get_user_model()


class Page(models.Model):
    """
    Page model for static content pages.
    
    Allows admins to create and manage static pages like:
    - About Us
    - Terms of Service
    - Privacy Policy
    - Help/FAQ pages
    - Custom landing pages
    """
    
    # Page status choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Title',
        help_text='Page title'
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Slug',
        help_text='URL-friendly version of the title (e.g., "about-us")'
    )
    
    content = RichTextField(
        verbose_name='Content',
        help_text='Page content (rich text editor)',
        blank=True
    )
    
    # Meta fields for SEO
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Meta Title',
        help_text='SEO meta title (defaults to title if empty)'
    )
    
    meta_description = models.TextField(
        max_length=300,
        blank=True,
        verbose_name='Meta Description',
        help_text='SEO meta description'
    )
    
    # Status and visibility
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
        help_text='Page publication status'
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Is Featured',
        help_text='Show this page in featured sections'
    )
    
    # Ordering for menu display
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Display order (lower numbers appear first)'
    )
    
    # Author tracking
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_pages',
        verbose_name='Author',
        help_text='User who created this page'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Published At',
        help_text='When the page was published'
    )
    
    class Meta:
        """Meta options for Page model."""
        verbose_name = 'Page'
        verbose_name_plural = 'Pages'
        ordering = ['order', 'title']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        """String representation of the page."""
        return self.title
    
    def save(self, *args, **kwargs):
        """Auto-generate slug and set published_at."""
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get URL for page detail view."""
        return reverse('cms:page_detail', kwargs={'slug': self.slug})
    
    def clean(self):
        """Validate page data."""
        if self.status == 'published' and not self.content:
            raise ValidationError('Published pages must have content.')


class Announcement(models.Model):
    """
    Announcement model for site-wide announcements and banners.
    
    Allows admins to create announcements that can be displayed:
    - In header/banner areas
    - On specific pages
    - With expiration dates
    """
    
    # Announcement type choices
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Title',
        help_text='Announcement title'
    )
    
    content = RichTextField(
        verbose_name='Content',
        help_text='Announcement content (rich text editor)',
        blank=True
    )
    
    announcement_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='info',
        verbose_name='Type',
        help_text='Announcement type (affects styling)'
    )
    
    # Visibility and scheduling
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Whether this announcement is currently active'
    )
    
    show_on_homepage = models.BooleanField(
        default=True,
        verbose_name='Show on Homepage',
        help_text='Display this announcement on the homepage'
    )
    
    # Scheduling
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Start Date',
        help_text='When to start showing this announcement'
    )
    
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='End Date',
        help_text='When to stop showing this announcement'
    )
    
    # Link (optional)
    link_url = models.URLField(
        blank=True,
        verbose_name='Link URL',
        help_text='Optional link URL for the announcement'
    )
    
    link_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Link Text',
        help_text='Text for the optional link'
    )
    
    # Author tracking
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_announcements',
        verbose_name='Author',
        help_text='User who created this announcement'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for Announcement model."""
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'show_on_homepage']),
        ]
    
    def __str__(self):
        """String representation of the announcement."""
        return self.title
    
    def is_currently_active(self):
        """Check if announcement is currently active based on dates."""
        if not self.is_active:
            return False
        
        from django.utils import timezone
        now = timezone.now()
        
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        return True


class Media(models.Model):
    """
    Media model for file uploads and media management.
    
    Allows admins to upload and manage:
    - Images
    - Documents
    - Videos
    - Other files
    """
    
    # Media type choices
    TYPE_CHOICES = [
        ('image', 'Image'),
        ('document', 'Document'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Title',
        help_text='Media title/name'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Media description'
    )
    
    file = models.FileField(
        upload_to='cms/media/%Y/%m/%d/',
        verbose_name='File',
        help_text='Upload file'
    )
    
    media_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='image',
        verbose_name='Type',
        help_text='Media type'
    )
    
    # Alt text for images (SEO and accessibility)
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Alt Text',
        help_text='Alternative text for images (for accessibility and SEO)'
    )
    
    # Upload tracking
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_media',
        verbose_name='Uploaded By',
        help_text='User who uploaded this file'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    class Meta:
        """Meta options for Media model."""
        verbose_name = 'Media'
        verbose_name_plural = 'Media'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['media_type']),
        ]
    
    def __str__(self):
        """String representation of the media."""
        return self.title
    
    def get_file_url(self):
        """Get the URL of the uploaded file."""
        if self.file:
            return self.file.url
        return None


class ContentBlock(models.Model):
    """
    ContentBlock model for reusable content blocks.
    
    Allows admins to create reusable content blocks that can be:
    - Embedded in pages
    - Used across multiple pages
    - Updated in one place to reflect everywhere
    """
    
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Name',
        help_text='Unique name for this content block'
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Slug',
        help_text='URL-friendly identifier'
    )
    
    content = RichTextField(
        verbose_name='Content',
        help_text='Block content (rich text editor)',
        blank=True
    )
    
    # Block type for categorization
    block_type = models.CharField(
        max_length=50,
        default='general',
        verbose_name='Block Type',
        help_text='Type/category of this block (e.g., "header", "footer", "sidebar")'
    )
    
    # Author tracking
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_blocks',
        verbose_name='Author',
        help_text='User who created this block'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for ContentBlock model."""
        verbose_name = 'Content Block'
        verbose_name_plural = 'Content Blocks'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug', 'block_type']),
        ]
    
    def __str__(self):
        """String representation of the content block."""
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
