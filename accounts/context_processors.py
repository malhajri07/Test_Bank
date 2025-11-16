"""
Context processors for accounts app.

Provides user's preferred language to templates for RTL/LTR support.
"""

def user_language(request):
    """
    Add user's preferred language to template context.
    
    Returns static default values to avoid recursion.
    Language switching is handled by LocaleMiddleware via session.
    """
    # Return static default to avoid any recursion issues
    # The actual language is handled by LocaleMiddleware
    return {
        'USER_LANGUAGE_CODE': 'en',
        'IS_RTL': False,
        'CURRENT_LANGUAGE': 'en',
    }

