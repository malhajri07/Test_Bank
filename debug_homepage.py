import os
import django
import sys
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testbank_platform.settings')
django.setup()

def debug():
    c = Client()
    try:
        response = c.get('/')
        if response.status_code == 200:
            print("Success: Homepage loaded (200 OK)")
        else:
            print(f"Error: Homepage returned {response.status_code}")
            # If it's a 500, Django debug page is in content. 
            # But we want the exception.
            # The Client doesn't raise the exception by default unless we tell it to, 
            # or we can inspect the response context if it's a template error.
            
            # Let's try to render the template manually to catch template errors
            from django.template.loader import render_to_string
            from catalog.models import TestBank
            
            print("Attempting to render template directly...")
            try:
                # Mock context data similar to view
                context = {
                    'trending_test_banks': TestBank.objects.all()[:5],
                    'featured_test_banks': TestBank.objects.all()[:5],
                    'categories': [],
                }
                content = render_to_string('catalog/index.html', context)
                print("Template rendered successfully.")
                with open('rendered_homepage.html', 'w') as f:
                    f.write(content)
                print("Rendered HTML saved to rendered_homepage.html")
            except Exception as e:
                print(f"Template Rendering Error: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"Request Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug()
