"""
Forms for catalog app, including JSON upload form for test banks.
"""

from django import forms
from .models import TestBank, Category, SubCategory, Certification


class TestBankJSONUploadForm(forms.Form):
    """
    Form for uploading test bank data via JSON file.
    
    Expected JSON format:
    {
        "test_bank": {
            "title": "Test Bank Title",
            "description": "Description of the test bank",
            "category": "category-slug",
            "subcategory": "subcategory-slug",  # optional
            "certification": "certification-slug",  # optional
            "difficulty_level": "easy|medium|advanced",
            "price": 0.00,
            "is_active": true
        },
        "questions": [
            {
                "question_text": "Question text here",
                "question_type": "mcq_single|mcq_multi|true_false",
                "explanation": "Explanation of the correct answer",
                "order": 1,
                "options": [
                    {
                        "option_text": "Option A",
                        "is_correct": true,
                        "order": 1
                    },
                    {
                        "option_text": "Option B",
                        "is_correct": false,
                        "order": 2
                    }
                ]
            }
        ]
    }
    """
    
    json_file = forms.FileField(
        label='JSON File',
        help_text='Upload a JSON file containing test bank data with questions and answers.',
        widget=forms.FileInput(attrs={
            'accept': '.json',
            'class': 'form-control'
        })
    )
    
    test_bank = forms.ModelChoiceField(
        queryset=TestBank.objects.all(),
        required=False,
        label='Update Existing Test Bank',
        help_text='Select an existing test bank to update, or leave empty to create a new one.',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean_json_file(self):
        """Validate JSON file."""
        json_file = self.cleaned_data.get('json_file')
        if json_file:
            if not json_file.name.endswith('.json'):
                raise forms.ValidationError('File must be a JSON file (.json)')
            
            # Check file size (max 10MB)
            if json_file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 10MB')
        
        return json_file

