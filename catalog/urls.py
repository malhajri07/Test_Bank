"""
URL configuration for catalog app.

Routes for:
- Landing page
- Category listing
- Vocational hierarchical structure
- Test bank listing by category/subcategory/certification
- Test bank detail page
"""

from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # Landing page
    path('', views.index, name='index'),
    
    # Category listing
    path('categories/', views.category_list, name='category_list'),
    
    # Vocational category landing page (convenience route - must come before category_detail)
    path('vocational/', views.vocational_index, name='vocational_index'),
    
    # Subcategory listing (shows certifications) - vocational route
    path('vocational/<slug:subcategory_slug>/', views.subcategory_list, name='subcategory_list'),
    
    # Certification listing (shows test banks) - vocational route
    path('vocational/<slug:subcategory_slug>/<slug:certification_slug>/', views.certification_list, name='certification_list'),
    
    # IMPORTANT: More specific patterns must come before general ones
    # Test bank listing by certification (most specific)
    path('categories/<slug:category_slug>/<slug:subcategory_slug>/<slug:certification_slug>/test-banks/', views.testbank_list, name='testbank_list_certification'),
    
    # Test bank listing by subcategory
    path('categories/<slug:category_slug>/<slug:subcategory_slug>/test-banks/', views.testbank_list, name='testbank_list_subcategory'),
    
    # Test bank listing by category
    path('categories/<slug:category_slug>/test-banks/', views.testbank_list, name='testbank_list'),
    
    # Certification listing with category - full path route
    path('categories/<slug:category_slug>/<slug:subcategory_slug>/<slug:certification_slug>/', views.certification_list, name='certification_list_full'),
    
    # Subcategory listing with category - full path route
    path('categories/<slug:category_slug>/<slug:subcategory_slug>/', views.subcategory_list, name='subcategory_list_full'),
    
    # Category detail page (shows subcategories if they exist) - must come after all specific patterns
    path('categories/<slug:category_slug>/', views.category_detail, name='category_detail'),
    
    # Test bank detail
    path('test-bank/<slug:slug>/', views.testbank_detail, name='testbank_detail'),
    
    # Rate test bank (AJAX)
    path('rate-test-bank/<slug:slug>/', views.rate_test_bank, name='rate_test_bank'),
]

