"""
Mixins for catalog app models.

Provides reusable functionality like auto-slug generation.
"""

from django.db import models
from django.utils.text import slugify


class AutoSlugMixin:
    """
    Mixin that automatically generates a slug from a specified field.
    
    Usage:
        class MyModel(AutoSlugMixin, models.Model):
            name = models.CharField(max_length=200)
            slug = models.SlugField(max_length=200, blank=True)
            
            def get_slug_source(self):
                return self.name
            
            class Meta:
                abstract = True
    """
    
    def get_slug_source(self):
        """
        Override this method to specify which field to use for slug generation.
        
        Returns:
            str: The source text to generate slug from
        """
        raise NotImplementedError("Subclasses must implement get_slug_source()")
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from source field if not provided."""
        if not self.slug:
            source = self.get_slug_source()
            if source:
                self.slug = slugify(source)
        super().save(*args, **kwargs)
