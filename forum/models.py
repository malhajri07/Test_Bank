"""
Forum app models for discussion boards.

This module defines models for:
- ForumCategory: Categories for organizing forum topics
- ForumTopic: Discussion topics created by users
- ForumPost: Posts/replies within topics
"""

from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from ckeditor.fields import RichTextField

User = get_user_model()


class ForumCategory(models.Model):
    """
    ForumCategory model for organizing forum topics.
    
    Categories help organize discussions into logical groups.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Name',
        help_text='Category name'
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug',
        help_text='URL-friendly version of the name'
    )
    
    description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Description',
        help_text='Category description'
    )
    
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Icon',
        help_text='Icon name or emoji (e.g., "💬", "📚")'
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Display order (lower numbers appear first)'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Whether this category is visible'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    class Meta:
        """Meta options for ForumCategory model."""
        verbose_name = 'Forum Category'
        verbose_name_plural = 'Forum Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        """String representation of the category."""
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get absolute URL for the category."""
        return reverse('forum:category_detail', kwargs={'slug': self.slug})
    
    def get_topic_count(self):
        """Get count of topics in this category."""
        return self.topics.filter(is_locked=False).count()
    
    def get_post_count(self):
        """Get count of all posts in topics of this category."""
        return ForumPost.objects.filter(topic__category=self, topic__is_locked=False).count()


class ForumTopic(models.Model):
    """
    ForumTopic model for discussion topics.
    
    Users can create topics within categories to start discussions.
    """
    
    category = models.ForeignKey(
        ForumCategory,
        on_delete=models.CASCADE,
        related_name='topics',
        verbose_name='Category',
        help_text='Category this topic belongs to'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='Title',
        help_text='Topic title'
    )
    
    slug = models.SlugField(
        max_length=200,
        verbose_name='Slug',
        help_text='URL-friendly version of the title'
    )
    
    content = RichTextField(
        verbose_name='Content',
        help_text='Initial post content'
    )
    
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='forum_topics',
        verbose_name='Author',
        help_text='User who created this topic'
    )
    
    is_pinned = models.BooleanField(
        default=False,
        verbose_name='Is Pinned',
        help_text='Pin this topic to the top of the category'
    )
    
    is_locked = models.BooleanField(
        default=False,
        verbose_name='Is Locked',
        help_text='Lock this topic to prevent new replies'
    )
    
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Views Count',
        help_text='Number of times this topic has been viewed'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    last_activity_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Activity At',
        help_text='When the last post was made in this topic'
    )
    
    class Meta:
        """Meta options for ForumTopic model."""
        verbose_name = 'Forum Topic'
        verbose_name_plural = 'Forum Topics'
        ordering = ['-is_pinned', '-last_activity_at']
        indexes = [
            models.Index(fields=['category', 'is_pinned', 'is_locked']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        """String representation of the topic."""
        return self.title
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from title."""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while ForumTopic.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get absolute URL for the topic."""
        return reverse('forum:topic_detail', kwargs={'category_slug': self.category.slug, 'topic_slug': self.slug})
    
    def get_reply_count(self):
        """Get count of replies (excluding the initial post)."""
        return self.posts.exclude(pk=self.posts.first().pk).count() if self.posts.exists() else 0
    
    def get_last_post(self):
        """Get the most recent post in this topic."""
        return self.posts.order_by('-created_at').first()


class ForumPost(models.Model):
    """
    ForumPost model for posts/replies within topics.
    
    Users can reply to topics, creating threaded discussions.
    """
    
    topic = models.ForeignKey(
        ForumTopic,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Topic',
        help_text='Topic this post belongs to'
    )
    
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='forum_posts',
        verbose_name='Author',
        help_text='User who wrote this post'
    )
    
    content = RichTextField(
        verbose_name='Content',
        help_text='Post content'
    )
    
    is_edited = models.BooleanField(
        default=False,
        verbose_name='Is Edited',
        help_text='Whether this post has been edited'
    )
    
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Edited At',
        help_text='When this post was last edited'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for ForumPost model."""
        verbose_name = 'Forum Post'
        verbose_name_plural = 'Forum Posts'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['topic', 'created_at']),
        ]
    
    def __str__(self):
        """String representation of the post."""
        return f"Post by {self.author.username} in {self.topic.title}"
    
    def save(self, *args, **kwargs):
        """Update topic's last_activity_at when a new post is created."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update topic's last activity
            from django.utils import timezone
            self.topic.last_activity_at = timezone.now()
            self.topic.save(update_fields=['last_activity_at'])
