"""
Forms for catalog app, including JSON upload form for test banks.
"""

from django import forms

from .models import ContactMessage, ReviewReply, TestBank, TestBankRating


class TestBankJSONUploadForm(forms.Form):
    """
    Form for uploading test bank data via JSON file.

    Expected JSON format:
    {
        "test_bank": {
            "title": "Test Bank Title",
            "description": "Description of the test bank",
            "category": "category-slug",
            "certification": "certification-slug",  # optional, requires category
            "organization": "CompTIA",  # optional
            "official_url": "https://www.example.com",  # optional
            "certification_details": "Additional details",  # optional
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


class TestBankReviewForm(forms.ModelForm):
    """Form for submitting reviews and ratings for test banks."""

    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.HiddenInput(),
        required=True
    )

    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Review title...',
            'class': 'w-full px-3 py-2 text-sm border-0 border-b border-gray-300 focus:border-[#5624d0] focus:outline-none focus:ring-0 bg-transparent',
            'maxlength': '200'
        }),
        required=False,
        max_length=200
    )

    review = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Write your review...',
            'class': 'w-full px-3 py-2 text-sm border-0 border-b border-gray-300 focus:border-[#5624d0] focus:outline-none focus:ring-0 resize-none bg-transparent'
        }),
        required=False,
        max_length=1000
    )

    class Meta:
        model = TestBankRating
        fields = ['rating', 'title', 'review']


class ReviewReplyForm(forms.ModelForm):
    """Form for replying to reviews."""

    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Write a reply...',
            'class': 'w-full px-3 py-2 text-sm border-0 border-b border-gray-300 focus:border-[#5624d0] focus:outline-none focus:ring-0 resize-none bg-transparent'
        }),
        required=True,
        max_length=1000
    )

    class Meta:
        model = ReviewReply
        fields = ['content']


class ContactForm(forms.ModelForm):
    """Form for submitting contact messages."""

    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 text-sm border-0 border-b border-gray-300 focus:border-[#5624d0] focus:outline-none focus:ring-0 bg-transparent',
            'placeholder': 'Your name'
        }),
        required=True,
        max_length=200
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 text-sm border-0 border-b border-gray-300 focus:border-[#5624d0] focus:outline-none focus:ring-0 bg-transparent',
            'placeholder': 'your.email@example.com'
        }),
        required=True
    )

    subject = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 text-sm border-0 border-b border-gray-300 focus:border-[#5624d0] focus:outline-none focus:ring-0 bg-transparent',
            'placeholder': 'Subject'
        }),
        required=True,
        max_length=200
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Your message...',
            'class': 'w-full px-4 py-3 text-sm border-0 border-b border-gray-300 focus:border-[#5624d0] focus:outline-none focus:ring-0 resize-none bg-transparent'
        }),
        required=True
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']

