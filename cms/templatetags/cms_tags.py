"""
Template tags for CMS app.

Provides template tags to:
- Render content blocks
- Display announcements
- Get CMS pages
"""

from django import template
from django.utils.safestring import mark_safe
from ..models import ContentBlock, Announcement, Page

register = template.Library()


@register.simple_tag
def content_block(slug):
    """
    Render a content block by slug.
    
    Usage:
        {% load cms_tags %}
        {% content_block "footer-content" %}
    
    Args:
        slug: Slug of the content block to render
        
    Returns:
        Rendered HTML content or empty string
    """
    try:
        block = ContentBlock.objects.get(slug=slug)
        return mark_safe(block.content)
    except ContentBlock.DoesNotExist:
        return ""


@register.inclusion_tag('cms/includes/announcement.html')
def render_announcement(announcement):
    """
    Render an announcement.
    
    Usage:
        {% load cms_tags %}
        {% for announcement in cms_homepage_announcements %}
            {% render_announcement announcement %}
        {% endfor %}
    """
    return {'announcement': announcement}


@register.simple_tag
def cms_page_url(slug):
    """
    Get URL for a CMS page by slug.
    
    Usage:
        {% load cms_tags %}
        <a href="{% cms_page_url 'about-us' %}">About Us</a>
    """
    try:
        page = Page.objects.get(slug=slug, status='published')
        return page.get_absolute_url()
    except Page.DoesNotExist:
        return "#"


@register.simple_tag
def get_cms_pages():
    """
    Get all published CMS pages.
    
    Usage:
        {% load cms_tags %}
        {% get_cms_pages as pages %}
        {% for page in pages %}
            <a href="{{ page.get_absolute_url }}">{{ page.title }}</a>
        {% endfor %}
    """
    return Page.objects.filter(status='published').order_by('order', 'title')

