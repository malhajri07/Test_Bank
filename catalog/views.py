"""
Catalog app views for browsing categories and test banks.

This module provides views for:
- Landing page with hero section
- Category listing
- Test bank listing by category
- Test bank detail page with purchase/practice options
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import Category, SubCategory, Certification, TestBank
from practice.models import UserTestAccess


def index(request):
    """
    Landing page view.
    
    Displays:
    - Hero section explaining the platform
    - Call-to-action buttons
    - Overview of categories and test banks
    - Testimonials
    - Partner logos
    - Trending test banks
    """
    # Get featured categories with test bank counts and subcategory counts
    # Convert to list immediately to avoid lazy evaluation issues
    categories = list(Category.objects.annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True)),
        subcategory_count=Count('subcategories')
    ).filter(test_bank_count__gt=0)[:8])
    
    # Get featured test banks
    featured_test_banks = list(TestBank.objects.filter(is_active=True)[:6])
    
    # Get trending test banks (most purchased or recently added)
    trending_test_banks = list(TestBank.objects.filter(is_active=True).order_by('-created_at')[:8])
    
    # Testimonials data (static for now, can be moved to model later)
    testimonials = [
        {
            'name': 'Sarah W.',
            'role': 'Data Analyst',
            'quote': "TestBank's reputation for high-quality content, paired with its flexible structure, made it possible for me to dive into data analytics while managing family, health, and everyday life."
        },
        {
            'name': 'Noeris B.',
            'role': 'Software Developer',
            'quote': "TestBank rebuilt my confidence and showed me I could dream bigger. It wasn't just about gaining knowledge—it was about believing in my potential again."
        },
        {
            'name': 'Abdullahi M.',
            'role': 'Project Manager',
            'quote': "I now feel more prepared to take on leadership roles and have already started mentoring some of my colleagues."
        },
        {
            'name': 'Anas A.',
            'role': 'Business Analyst',
            'quote': "Learning with TestBank has expanded my professional expertise by giving me access to cutting-edge research, practical tools, and global perspectives."
        },
    ]
    
    # Partner/Institution data (static for now)
    partners = [
        {'name': 'Google', 'logo_url': ''},
        {'name': 'Microsoft', 'logo_url': ''},
        {'name': 'IBM', 'logo_url': ''},
        {'name': 'Stanford', 'logo_url': ''},
        {'name': 'Meta', 'logo_url': ''},
        {'name': 'Amazon', 'logo_url': ''},
        {'name': 'Adobe', 'logo_url': ''},
        {'name': 'University of Michigan', 'logo_url': ''},
    ]
    
    return render(request, 'catalog/index.html', {
        'categories': categories,
        'featured_test_banks': featured_test_banks,
        'trending_test_banks': trending_test_banks,
        'testimonials': testimonials,
        'partners': partners,
    })


def category_list(request):
    """
    Category listing view.
    
    Displays all categories as cards.
    Each category shows:
    - Name and description
    - Number of test banks
    - Number of subcategories (if any)
    - Link to appropriate page (vocational_index, subcategory list, or test bank list)
    """
    # Get all categories with test bank counts and subcategory counts
    categories = Category.objects.annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True)),
        subcategory_count=Count('subcategories')
    ).order_by('name')
    
    return render(request, 'catalog/category_list.html', {
        'categories': categories,
    })


def category_detail(request, category_slug):
    """
    Category detail page showing subcategories.
    
    Displays all subcategories under a category.
    If category has no subcategories, redirects to test bank list.
    """
    category = get_object_or_404(Category, slug=category_slug)
    
    # Get all subcategories with certification counts
    subcategories = SubCategory.objects.filter(
        category=category
    ).annotate(
        certification_count=Count('certifications')
    ).order_by('order', 'name')
    
    # If no subcategories, redirect to test bank list
    if not subcategories.exists():
        from django.shortcuts import redirect
        return redirect('catalog:testbank_list', category_slug=category.slug)
    
    # Build breadcrumbs
    breadcrumbs = [
        {'label': _('Home'), 'url': reverse('catalog:index')},
        {'label': category.name, 'url': ''},
    ]
    
    return render(request, 'catalog/vocational_index.html', {
        'category': category,
        'subcategories': subcategories,
        'breadcrumbs': breadcrumbs,
    })


def vocational_index(request):
    """
    Vocational category landing page.
    
    Displays all subcategories under the Vocational category.
    This is a convenience view that redirects to category_detail.
    """
    return category_detail(request, 'vocational')


def subcategory_list(request, subcategory_slug, category_slug=None):
    """
    Subcategory listing view showing certifications.
    
    Displays all certifications under a subcategory.
    Can be accessed via:
    - /vocational/<subcategory_slug>/ (category_slug is None, assumes vocational)
    - /categories/<category_slug>/<subcategory_slug>/ (full path)
    
    Args:
        subcategory_slug: Slug of the subcategory
        category_slug: Optional slug of the category (if None, assumes vocational)
    """
    # Extract category_slug from URL kwargs if not provided as argument
    if not category_slug:
        category_slug = request.resolver_match.kwargs.get('category_slug')
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
    else:
        # Default to vocational category for vocational routes
        category = get_object_or_404(Category, slug='vocational')
    
    subcategory = get_object_or_404(SubCategory, category=category, slug=subcategory_slug)
    
    # Get all certifications with test bank counts
    certifications = Certification.objects.filter(
        subcategory=subcategory
    ).annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
    ).order_by('order', 'name')
    
    # Build breadcrumbs
    breadcrumbs = [
        {'label': _('Home'), 'url': reverse('catalog:index')},
        {'label': category.name, 'url': reverse('catalog:vocational_index') if category.slug == 'vocational' else reverse('catalog:category_detail', kwargs={'category_slug': category.slug})},
        {'label': subcategory.name, 'url': ''},
    ]
    
    return render(request, 'catalog/subcategory_list.html', {
        'category': category,
        'subcategory': subcategory,
        'certifications': certifications,
        'breadcrumbs': breadcrumbs,
    })


def certification_list(request, subcategory_slug, certification_slug, category_slug=None):
    """
    Certification listing view showing test banks.
    
    Displays all test banks for a specific certification.
    Can be accessed via:
    - /vocational/<subcategory_slug>/<certification_slug>/ (category_slug is None, assumes vocational)
    - /categories/<category_slug>/<subcategory_slug>/<certification_slug>/ (full path)
    
    Args:
        subcategory_slug: Slug of the subcategory
        certification_slug: Slug of the certification
        category_slug: Optional slug of the category (if None, assumes vocational)
    """
    # Extract category_slug from URL kwargs if not provided as argument
    if not category_slug:
        category_slug = request.resolver_match.kwargs.get('category_slug')
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
    else:
        # Default to vocational category for vocational routes
        category = get_object_or_404(Category, slug='vocational')
    
    subcategory = get_object_or_404(SubCategory, category=category, slug=subcategory_slug)
    certification = get_object_or_404(Certification, subcategory=subcategory, slug=certification_slug)
    
    # Get active test banks for this certification
    test_banks = TestBank.objects.filter(
        certification=certification,
        is_active=True
    ).order_by('-created_at')
    
    # Build breadcrumbs
    breadcrumbs = [
        {'label': _('Home'), 'url': reverse('catalog:index')},
        {'label': category.name, 'url': reverse('catalog:vocational_index') if category.slug == 'vocational' else reverse('catalog:category_detail', kwargs={'category_slug': category.slug})},
        {'label': subcategory.name, 'url': reverse('catalog:subcategory_list', kwargs={'subcategory_slug': subcategory.slug})},
        {'label': certification.name, 'url': ''},
    ]
    
    return render(request, 'catalog/certification_list.html', {
        'category': category,
        'subcategory': subcategory,
        'certification': certification,
        'test_banks': test_banks,
        'breadcrumbs': breadcrumbs,
    })


def testbank_list(request, category_slug, subcategory_slug=None, certification_slug=None):
    """
    Test bank listing view for a category, subcategory, or certification.
    
    Displays all active test banks filtered by:
    - Category only (if subcategory_slug is None)
    - Subcategory (if certification_slug is None)
    - Certification (if all parameters provided)
    
    Args:
        category_slug: Slug of the category
        subcategory_slug: Optional slug of the subcategory
        certification_slug: Optional slug of the certification
    """
    category = get_object_or_404(Category, slug=category_slug)
    subcategory = None
    certification = None
    
    # Build filter query
    filter_q = Q(category=category, is_active=True)
    
    if certification_slug:
        subcategory = get_object_or_404(SubCategory, category=category, slug=subcategory_slug)
        certification = get_object_or_404(Certification, subcategory=subcategory, slug=certification_slug)
        filter_q = Q(certification=certification, is_active=True)
    elif subcategory_slug:
        subcategory = get_object_or_404(SubCategory, category=category, slug=subcategory_slug)
        filter_q = Q(subcategory=subcategory, is_active=True)
    
    # Get active test banks
    test_banks = TestBank.objects.filter(filter_q).order_by('-created_at')
    
    # Build breadcrumbs
    breadcrumbs = [
        {'label': _('Home'), 'url': reverse('catalog:index')},
    ]
    
    if certification:
        breadcrumbs.extend([
            {'label': category.name, 'url': reverse('catalog:vocational_index') if category.slug == 'vocational' else reverse('catalog:category_detail', kwargs={'category_slug': category.slug})},
            {'label': subcategory.name, 'url': reverse('catalog:subcategory_list', kwargs={'subcategory_slug': subcategory.slug})},
            {'label': certification.name, 'url': reverse('catalog:certification_list', kwargs={'subcategory_slug': subcategory.slug, 'certification_slug': certification.slug})},
            {'label': _('Test Banks'), 'url': ''},
        ])
    elif subcategory:
        breadcrumbs.extend([
            {'label': category.name, 'url': reverse('catalog:vocational_index') if category.slug == 'vocational' else reverse('catalog:category_detail', kwargs={'category_slug': category.slug})},
            {'label': subcategory.name, 'url': reverse('catalog:subcategory_list', kwargs={'subcategory_slug': subcategory.slug})},
            {'label': _('Test Banks'), 'url': ''},
        ])
    else:
        breadcrumbs.extend([
            {'label': _('Categories'), 'url': reverse('catalog:category_list')},
            {'label': category.name, 'url': ''},
        ])
    
    return render(request, 'catalog/testbank_list.html', {
        'category': category,
        'subcategory': subcategory,
        'certification': certification,
        'test_banks': test_banks,
        'breadcrumbs': breadcrumbs,
    })


def testbank_detail(request, slug):
    """
    Test bank detail page.
    
    Displays full test bank information and:
    - If user not purchased: Show "Buy Now" button
    - If user has access: Show "Start Practice" button and "View Previous Attempts"
    
    Args:
        slug: Slug of the test bank to display
    """
    test_bank = get_object_or_404(TestBank, slug=slug, is_active=True)
    
    # Check if user has access (if authenticated)
    has_access = False
    if request.user.is_authenticated:
        has_access = UserTestAccess.objects.filter(
            user=request.user,
            test_bank=test_bank,
            is_active=True
        ).exists()
    
    # Get question count
    question_count = test_bank.get_question_count()
    
    # Get recent sessions if user has access
    recent_sessions = None
    if request.user.is_authenticated and has_access:
        recent_sessions = test_bank.user_sessions.filter(
            user=request.user
        ).order_by('-started_at')[:5]
    
    # Get related test banks (same category, exclude current)
    related_test_banks = TestBank.objects.filter(
        category=test_bank.category,
        is_active=True
    ).exclude(id=test_bank.id)[:6]
    
    # Check if test bank is free
    is_free = test_bank.price == 0
    
    return render(request, 'catalog/testbank_detail.html', {
        'test_bank': test_bank,
        'has_access': has_access,
        'question_count': question_count,
        'recent_sessions': recent_sessions,
        'related_test_banks': related_test_banks,
        'is_free': is_free,
    })
