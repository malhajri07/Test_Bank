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

# Country codes for phone numbers
COUNTRY_CODES = [
    ('+1', '+1 (US/CA)'),
    ('+44', '+44 (UK)'),
    ('+971', '+971 (UAE)'),
    ('+966', '+966 (Saudi Arabia)'),
    ('+965', '+965 (Kuwait)'),
    ('+974', '+974 (Qatar)'),
    ('+973', '+973 (Bahrain)'),
    ('+968', '+968 (Oman)'),
    ('+961', '+961 (Lebanon)'),
    ('+962', '+962 (Jordan)'),
    ('+20', '+20 (Egypt)'),
    ('+212', '+212 (Morocco)'),
    ('+213', '+213 (Algeria)'),
    ('+33', '+33 (France)'),
    ('+49', '+49 (Germany)'),
    ('+39', '+39 (Italy)'),
    ('+34', '+34 (Spain)'),
    ('+31', '+31 (Netherlands)'),
    ('+32', '+32 (Belgium)'),
    ('+41', '+41 (Switzerland)'),
    ('+43', '+43 (Austria)'),
    ('+46', '+46 (Sweden)'),
    ('+47', '+47 (Norway)'),
    ('+45', '+45 (Denmark)'),
    ('+358', '+358 (Finland)'),
    ('+7', '+7 (Russia)'),
    ('+81', '+81 (Japan)'),
    ('+82', '+82 (South Korea)'),
    ('+86', '+86 (China)'),
    ('+91', '+91 (India)'),
    ('+61', '+61 (Australia)'),
    ('+64', '+64 (New Zealand)'),
    ('+27', '+27 (South Africa)'),
    ('+234', '+234 (Nigeria)'),
    ('+254', '+254 (Kenya)'),
    ('+52', '+52 (Mexico)'),
    ('+55', '+55 (Brazil)'),
    ('+54', '+54 (Argentina)'),
    ('+56', '+56 (Chile)'),
    ('+57', '+57 (Colombia)'),
]

# Countries list
COUNTRIES = [
    ('', 'Select Country'),
    ('United States', 'United States'),
    ('Canada', 'Canada'),
    ('United Kingdom', 'United Kingdom'),
    ('United Arab Emirates', 'United Arab Emirates'),
    ('Saudi Arabia', 'Saudi Arabia'),
    ('Kuwait', 'Kuwait'),
    ('Qatar', 'Qatar'),
    ('Bahrain', 'Bahrain'),
    ('Oman', 'Oman'),
    ('Lebanon', 'Lebanon'),
    ('Jordan', 'Jordan'),
    ('Egypt', 'Egypt'),
    ('Morocco', 'Morocco'),
    ('Algeria', 'Algeria'),
    ('France', 'France'),
    ('Germany', 'Germany'),
    ('Italy', 'Italy'),
    ('Spain', 'Spain'),
    ('Netherlands', 'Netherlands'),
    ('Belgium', 'Belgium'),
    ('Switzerland', 'Switzerland'),
    ('Austria', 'Austria'),
    ('Sweden', 'Sweden'),
    ('Norway', 'Norway'),
    ('Denmark', 'Denmark'),
    ('Finland', 'Finland'),
    ('Russia', 'Russia'),
    ('Japan', 'Japan'),
    ('South Korea', 'South Korea'),
    ('China', 'China'),
    ('India', 'India'),
    ('Australia', 'Australia'),
    ('New Zealand', 'New Zealand'),
    ('South Africa', 'South Africa'),
    ('Nigeria', 'Nigeria'),
    ('Kenya', 'Kenya'),
    ('Mexico', 'Mexico'),
    ('Brazil', 'Brazil'),
    ('Argentina', 'Argentina'),
    ('Chile', 'Chile'),
    ('Colombia', 'Colombia'),
    ('Other', 'Other'),
]


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
    - Phone number (with country code)
    - Country
    - Preferred language (for RTL/LTR support)
    """
    
    # Separate fields for phone number with country code
    phone_country_code = forms.ChoiceField(
        choices=COUNTRY_CODES,
        required=False,
        label='Country Code',
        widget=forms.Select(attrs={
            'class': 'px-4 py-4 border-0 rounded-l-2xl focus:ring-2 focus:ring-[#e28f64] focus:border-transparent text-[#000000] font-medium bg-white outline-none'
        })
    )
    
    phone_number_only = forms.CharField(
        max_length=20,
        required=False,
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'flex-1 px-5 py-4 border-0 rounded-r-2xl focus:ring-2 focus:ring-[#e28f64] focus:border-transparent text-[#000000] font-medium outline-none',
            'placeholder': 'Phone number'
        })
    )
    
    # Override country field to use Select with choices
    country = forms.ChoiceField(
        choices=COUNTRIES,
        required=False,
        label='Country',
        widget=forms.Select(attrs={
            'class': 'w-full px-5 py-4 border border-gray-200 rounded-2xl focus:ring-2 focus:ring-[#e28f64] focus:border-transparent text-[#000000] font-medium shadow-sm hover:shadow-md transition-all'
        })
    )
    
    class Meta:
        """Meta options for UserProfileForm."""
        model = UserProfile
        fields = ('full_name', 'country', 'preferred_language')
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-5 py-4 border border-gray-200 rounded-2xl focus:ring-2 focus:ring-[#e28f64] focus:border-transparent text-[#000000] font-medium shadow-sm hover:shadow-md transition-all'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'w-full px-5 py-4 border border-gray-200 rounded-2xl focus:ring-2 focus:ring-[#e28f64] focus:border-transparent text-[#000000] font-medium shadow-sm hover:shadow-md transition-all'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form and split phone number if it exists."""
        super().__init__(*args, **kwargs)
        
        # Set country field choices
        self.fields['country'].choices = COUNTRIES
        
        # If editing existing profile, split phone number
        if self.instance and self.instance.pk and self.instance.phone_number:
            phone = self.instance.phone_number
            # Try to extract country code (format: +XXX or +XXXX followed by number)
            if phone.startswith('+'):
                # Find where the number part starts (after country code)
                # Most country codes are 1-4 digits
                for i in range(1, min(5, len(phone))):
                    if phone[i:].replace(' ', '').replace('-', '').isdigit():
                        code = phone[:i+1] if phone[i] != ' ' else phone[:i]
                        number = phone[i+1:].strip()
                        # Check if code is in our list
                        if any(code == choice[0] for choice in COUNTRY_CODES):
                            self.initial['phone_country_code'] = code
                            self.initial['phone_number_only'] = number
                            break
                else:
                    # Default to +1 if can't parse
                    self.initial['phone_country_code'] = '+1'
                    self.initial['phone_number_only'] = phone
            else:
                # No country code, assume +1
                self.initial['phone_country_code'] = '+1'
                self.initial['phone_number_only'] = phone
        else:
            # Default to +1
            self.initial['phone_country_code'] = '+1'
    
    def save(self, commit=True):
        """Combine country code and phone number before saving."""
        instance = super().save(commit=False)
        
        # Combine country code and phone number
        country_code = self.cleaned_data.get('phone_country_code', '+1')
        phone_number = self.cleaned_data.get('phone_number_only', '').strip()
        
        if phone_number:
            instance.phone_number = f"{country_code} {phone_number}"
        else:
            instance.phone_number = ''
        
        if commit:
            instance.save()
        return instance

