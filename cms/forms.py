"""
CMS app forms for blog comments.
"""

from django import forms
from .models import BlogComment


class BlogCommentForm(forms.ModelForm):
    """
    Form for creating blog comments.
    
    Minimalist design with clean styling.
    """
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5525d0] focus:border-transparent resize-none',
            'rows': 4,
            'placeholder': 'Write your comment...',
        }),
        label='',
        max_length=2000,
        required=True
    )
    
    class Meta:
        model = BlogComment
        fields = ['content']
    
    def __init__(self, *args, **kwargs):
        """Initialize form with custom styling."""
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5525d0] focus:border-transparent resize-none',
        })


class BlogCommentReplyForm(forms.ModelForm):
    """
    Form for replying to blog comments.
    
    Similar to BlogCommentForm but for nested replies.
    """
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5525d0] focus:border-transparent resize-none',
            'rows': 3,
            'placeholder': 'Write your reply...',
        }),
        label='',
        max_length=2000,
        required=True
    )
    
    class Meta:
        model = BlogComment
        fields = ['content']




