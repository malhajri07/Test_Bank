"""
Forms for Forum app.
"""

from ckeditor.widgets import CKEditorWidget
from django import forms

from .models import ForumCategory, ForumPost, ForumTopic


class ForumCategoryForm(forms.ModelForm):
    """Form for creating new forum categories."""

    class Meta:
        model = ForumCategory
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5525d0] focus:border-transparent',
                'placeholder': 'Category name...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5525d0] focus:border-transparent',
                'rows': 3,
                'placeholder': 'Category description (optional)...'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5525d0] focus:border-transparent',
                'placeholder': 'Icon emoji or name (optional, e.g., 💬)'
            }),
        }


class ForumTopicForm(forms.ModelForm):
    """Form for creating/editing forum topics."""

    class Meta:
        model = ForumTopic
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#5525d0] focus:border-transparent',
                'placeholder': 'Enter topic title...'
            }),
            'content': CKEditorWidget(attrs={
                'class': 'w-full',
            }),
        }


class ForumPostForm(forms.ModelForm):
    """Form for creating/editing forum posts."""

    class Meta:
        model = ForumPost
        fields = ['content']
        widgets = {
            'content': CKEditorWidget(attrs={
                'class': 'w-full',
            }),
        }
