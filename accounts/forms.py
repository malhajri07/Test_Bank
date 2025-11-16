"""
Accounts app forms for user registration and profile management.

This module defines forms for:
- User registration (username, email, password)
- User profile editing (full_name, phone, country, language)
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """
    User registration form extending Django's UserCreationForm.
    
    Adds additional fields:
    - Email (required)
    - Full name, phone number, country, preferred language
    """
    
    email = forms.EmailField(
        required=True,
        label='Email',
        help_text='Required. Enter a valid email address.'
    )
    
    full_name = forms.CharField(
        max_length=255,
        required=False,
        label='Full Name',
        help_text='Your full name'
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label='Phone Number',
        help_text='Your contact phone number'
    )
    
    country = forms.CharField(
        max_length=100,
        required=False,
        label='Country',
        help_text='Your country'
    )
    
    preferred_language = forms.ChoiceField(
        choices=UserProfile.LANGUAGE_CHOICES,
        initial='en',
        label='Preferred Language',
        help_text='Your preferred language for the interface'
    )
    
    class Meta:
        """Meta options for UserRegistrationForm."""
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'full_name', 
                  'phone_number', 'country', 'preferred_language')
    
    def __init__(self, *args, **kwargs):
        """Initialize form with custom styling classes."""
        super().__init__(*args, **kwargs)
        # Add Tailwind CSS classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
    
    def clean_email(self):
        """Validate that email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def save(self, commit=True):
        """Save user and return user instance."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """
    Form for editing user profile information.
    
    Allows users to update:
    - Full name
    - Phone number
    - Country
    - Preferred language (for RTL/LTR support)
    """
    
    class Meta:
        """Meta options for UserProfileForm."""
        model = UserProfile
        fields = ('full_name', 'phone_number', 'country', 'preferred_language')
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'country': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
        }

