# Arabic Localization Guide

## Overview

The Test Bank Platform now supports full Arabic localization with RTL (Right-to-Left) layout support. Users can switch between English and Arabic at any time.

## Features

- **Language Switcher**: Available in the navigation bar (desktop) and mobile menu
- **RTL Support**: Automatic layout direction switching for Arabic
- **User Preference**: Language preference is saved to user profile
- **Session Persistence**: Language choice persists across sessions
- **Font Support**: Cairo font for Arabic, Inter font for English

## How to Use

### For Users

1. **Switch Language**: Use the language dropdown in the navigation bar
2. **Profile Setting**: Set your preferred language in your profile (Settings → Profile)
3. **Automatic RTL**: When Arabic is selected, the entire interface switches to RTL layout

### For Developers

#### Adding New Translations

1. **Mark strings for translation** in Python code:
   ```python
   from django.utils.translation import gettext_lazy as _
   message = _("Your message here")
   ```

2. **Mark strings in templates**:
   ```django
   {% load i18n %}
   {% trans "Your message here" %}
   ```

3. **Update translation files**:
   ```bash
   python manage.py makemessages -l ar
   ```

4. **Add Arabic translations** to `locale/ar/LC_MESSAGES/django.po`

5. **Compile translations**:
   ```bash
   python manage.py compilemessages
   ```

#### Language Switching View

The language switcher uses Django's built-in i18n system:
- View: `accounts.views.set_language`
- URL: `/accounts/set-language/`
- Updates both session and user profile (if authenticated)

#### Context Processor

The `user_language` context processor provides:
- `CURRENT_LANGUAGE`: Current language code ('en' or 'ar')
- `IS_RTL`: Boolean indicating if RTL layout should be used
- `USER_LANGUAGE_CODE`: User's preferred language

## Translation Files

- Location: `locale/ar/LC_MESSAGES/`
- Source: `django.po` (editable)
- Compiled: `django.mo` (binary, auto-generated)

## Current Status

✅ Basic translations added for:
- Registration messages
- Profile update messages
- Language change messages

📝 To add more translations:
1. Use `{% trans %}` tags in templates
2. Use `_()` in Python code
3. Run `makemessages` to extract strings
4. Add Arabic translations to `.po` file
5. Compile with `compilemessages`

## Testing

1. Switch to Arabic using the language dropdown
2. Verify RTL layout is applied
3. Check that Arabic text displays correctly
4. Verify language persists after page refresh
5. Test on mobile devices

## Notes

- Arabic translations use UTF-8 encoding
- RTL layout is handled automatically via CSS `dir="rtl"` attribute
- Font switching (Cairo for Arabic) is handled in base template
- Language preference syncs with user profile for logged-in users

