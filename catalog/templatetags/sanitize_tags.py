"""
Template filter for rendering sanitized HTML content.

Uses nh3 to strip dangerous tags/attributes (script, onclick, etc.)
while preserving safe formatting markup.
"""

import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = {
    "a", "abbr", "acronym", "b", "blockquote", "br", "code", "dd", "del",
    "div", "dl", "dt", "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
    "i", "img", "ins", "li", "ol", "p", "pre", "span", "strong", "sub",
    "sup", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "u", "ul",
}

ALLOWED_ATTRIBUTES = {
    "*": {"class", "id", "style", "dir", "lang"},
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title", "width", "height"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
}


@register.filter(name="sanitize")
def sanitize_html(value):
    """
    Sanitize HTML content, stripping dangerous tags and attributes.

    Usage in templates:
        {% load sanitize_tags %}
        {{ content|sanitize }}
    """
    if not value:
        return ""
    cleaned = nh3.clean(
        str(value),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        link_rel="noopener noreferrer",
    )
    return mark_safe(cleaned)
