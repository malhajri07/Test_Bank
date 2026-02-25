"""
Catalog app views for browsing categories and test banks.

This module provides views for:
- Landing page with hero section
- Category listing
- Test bank listing by category
- Test bank detail page with purchase/practice options
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from .models import Category, Certification, TestBank, TestBankRating, ReviewReply, ContactMessage
from .forms import TestBankReviewForm, ReviewReplyForm, ContactForm
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
    # Get featured categories with test bank counts and certification counts
    # Convert to list immediately to avoid lazy evaluation issues
    categories = list(Category.objects.annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True)),
        certification_count=Count('certifications')
    ).filter(test_bank_count__gt=0)[:8])
    
    # Get featured test banks with user counts (optimized with select_related)
    featured_test_banks = list(TestBank.objects.filter(is_active=True).select_related(
        'category', 'certification'
    ).annotate(
        user_count=Count('user_accesses', filter=Q(user_accesses__is_active=True))
    ).order_by('-user_count', '-average_rating')[:6])
    
    # Get trending test banks (ordered by user count, then rating, then recent)
    # Optimized with select_related to avoid N+1 queries
    trending_qs = TestBank.objects.filter(is_active=True).select_related(
        'category', 'certification'
    ).annotate(
        user_count=Count('user_accesses', filter=Q(user_accesses__is_active=True))
    )

    if request.user.is_authenticated:
        from django.db.models import OuterRef, Subquery, Exists, IntegerField
        from practice.models import UserTestAccess
        from .models import TestBankRating

        # Subquery to check if user has access
        access_subquery = UserTestAccess.objects.filter(
            user=request.user,
            test_bank=OuterRef('pk'),
            is_active=True
        )
        
        # Subquery to get user's rating
        rating_subquery = TestBankRating.objects.filter(
            user=request.user,
            test_bank=OuterRef('pk')
        ).values('rating')[:1]

        trending_qs = trending_qs.annotate(
            has_access=Exists(access_subquery),
            user_rating=Subquery(rating_subquery, output_field=IntegerField())
        )
    
    trending_test_banks = list(trending_qs.order_by('-user_count', '-average_rating', '-created_at')[:10])
    
    # Testimonials are now loaded from CMS via context processor
    
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
        'partners': partners,
    })


def category_list(request):
    """
    Category listing view.
    
    Displays all categories as cards.
    Each category shows:
    - Name and description
    - Number of test banks
    - Number of certifications (if any)
    - Link to appropriate page (vocational_index, certification list, or test bank list)
    """
    # Get all categories with test bank counts and certification counts
    categories = Category.objects.annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True)),
        certification_count=Count('certifications')
    ).order_by('name')
    
    return render(request, 'catalog/category_list.html', {
        'categories': categories,
    })


def category_detail(request, category_slug):
    """
    Category detail page showing certifications.
    
    Displays all certifications under a category.
    If category has no certifications, redirects to test bank list.
    """
    category = get_object_or_404(Category, slug=category_slug)
    
    # Get all certifications with test bank counts
    certifications = Certification.objects.filter(
        category=category
    ).annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
    ).order_by('order', 'name')
    
    # If no certifications, redirect to test bank list
    if not certifications.exists():
        from django.shortcuts import redirect
        return redirect('catalog:testbank_list', category_slug=category.slug)
    
    # Build breadcrumbs
    breadcrumbs = [
        {'label': _('Home'), 'url': reverse('catalog:index')},
        {'label': category.name, 'url': ''},
    ]
    
    return render(request, 'catalog/vocational_index.html', {
        'category': category,
        'certifications': certifications,
        'breadcrumbs': breadcrumbs,
    })


def vocational_index(request):
    """
    Vocational category landing page.
    
    Displays all certifications under the Vocational category.
    This is a convenience view that redirects to category_detail.
    """
    return category_detail(request, 'vocational')


def certification_list(request, certification_slug, category_slug=None):
    """
    Certification listing view showing test banks.
    
    Displays all test banks for a specific certification.
    Can be accessed via:
    - /vocational/<certification_slug>/ (category_slug is None, assumes vocational)
    - /categories/<category_slug>/<certification_slug>/ (full path)
    
    Args:
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
    
    certification = get_object_or_404(Certification, category=category, slug=certification_slug)
    
    # Get active test banks for this certification
    test_banks = TestBank.objects.filter(
        certification=certification,
        is_active=True
    ).order_by('-created_at')
    
    # Build breadcrumbs
    breadcrumbs = [
        {'label': _('Home'), 'url': reverse('catalog:index')},
        {'label': category.name, 'url': reverse('catalog:vocational_index') if category.slug == 'vocational' else reverse('catalog:category_detail', kwargs={'category_slug': category.slug})},
        {'label': certification.name, 'url': ''},
    ]
    
    return render(request, 'catalog/certification_list.html', {
        'category': category,
        'certification': certification,
        'test_banks': test_banks,
        'breadcrumbs': breadcrumbs,
    })


def testbank_list(request, category_slug, certification_slug=None):
    """
    Test bank listing view for a category or certification.
    
    Displays all active test banks filtered by:
    - Category only (if certification_slug is None)
    - Certification (if certification_slug is provided)
    
    Args:
        category_slug: Slug of the category
        certification_slug: Optional slug of the certification
    """
    category = get_object_or_404(Category, slug=category_slug)
    certification = None
    
    # Build filter query
    filter_q = Q(category=category, is_active=True)
    
    if certification_slug:
        certification = get_object_or_404(Certification, category=category, slug=certification_slug)
        filter_q = Q(certification=certification, is_active=True)
    
    # Get active test banks with user counts
    test_banks = TestBank.objects.filter(filter_q).annotate(
        user_count=Count('user_accesses', filter=Q(user_accesses__is_active=True))
    ).order_by('-user_count', '-average_rating', '-created_at')
    
    # Build breadcrumbs
    breadcrumbs = [
        {'label': _('Home'), 'url': reverse('catalog:index')},
    ]
    
    if certification:
        breadcrumbs.extend([
            {'label': category.name, 'url': reverse('catalog:vocational_index') if category.slug == 'vocational' else reverse('catalog:category_detail', kwargs={'category_slug': category.slug})},
            {'label': certification.name, 'url': reverse('catalog:certification_list', kwargs={'certification_slug': certification.slug})},
            {'label': _('Test Banks'), 'url': ''},
        ])
    else:
        breadcrumbs.extend([
            {'label': _('Categories'), 'url': reverse('catalog:category_list')},
            {'label': category.name, 'url': ''},
        ])
    
    return render(request, 'catalog/testbank_list.html', {
        'category': category,
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
    
    # Get recent sessions if user has access (optimized with select_related)
    recent_sessions = None
    if request.user.is_authenticated and has_access:
        recent_sessions = test_bank.user_sessions.filter(
            user=request.user
        ).select_related('user', 'test_bank').order_by('-started_at')[:5]
    
    # Get related test banks (same category, exclude current)
    # Optimized with select_related and prefetch_related for ratings
    related_test_banks = TestBank.objects.filter(
        category=test_bank.category,
        is_active=True
    ).select_related('category', 'certification').prefetch_related(
        'ratings'
    ).exclude(id=test_bank.id)[:6]
    
    # Check if test bank is free
    is_free = test_bank.price == 0
    
    # Get all reviews with user information and replies
    reviews = TestBankRating.objects.filter(test_bank=test_bank).select_related('user').prefetch_related('replies__user').order_by('-created_at')[:10]
    
    # Get user's existing review if authenticated
    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = TestBankRating.objects.get(user=request.user, test_bank=test_bank)
        except TestBankRating.DoesNotExist:
            pass
    
    # Handle review submission
    review_form = None
    reply_form = None
    
    if request.method == 'POST' and request.user.is_authenticated:
        # Check if this is a reply submission
        reply_to_review_id = request.POST.get('reply_to_review_id')
        if reply_to_review_id:
            # Handle reply submission
            try:
                parent_review = TestBankRating.objects.get(id=reply_to_review_id, test_bank=test_bank)
                reply_form = ReviewReplyForm(request.POST)
                if reply_form.is_valid():
                    reply = reply_form.save(commit=False)
                    reply.user = request.user
                    reply.review = parent_review
                    reply.save()
                    messages.success(request, _('Your reply has been posted.'))
                    return redirect('catalog:testbank_detail', slug=slug)
            except TestBankRating.DoesNotExist:
                messages.error(request, _('Review not found.'))
        elif has_access:
            # Handle review submission
            if user_review:
                review_form = TestBankReviewForm(request.POST, instance=user_review)
            else:
                review_form = TestBankReviewForm(request.POST)
            
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.user = request.user
                review.test_bank = test_bank
                review.save()
                messages.success(request, _('Thank you for your review!'))
                return redirect('catalog:testbank_detail', slug=slug)
        else:
            messages.error(request, _('You must have access to this test bank to leave a review.'))
    
    # Initialize forms for GET request
    if review_form is None:
        if user_review:
            review_form = TestBankReviewForm(instance=user_review)
        else:
            review_form = TestBankReviewForm()
    
    if reply_form is None:
        reply_form = ReviewReplyForm()
    
    return render(request, 'catalog/testbank_detail.html', {
        'test_bank': test_bank,
        'has_access': has_access,
        'question_count': question_count,
        'recent_sessions': recent_sessions,
        'related_test_banks': related_test_banks,
        'is_free': is_free,
        'reviews': reviews,
        'user_review': user_review,
        'review_form': review_form,
        'reply_form': reply_form,
    })


from django.views.decorators.http import require_POST
import json

@require_POST
@login_required
def rate_test_bank(request, slug):
    """
    Handle AJAX request to rate a test bank.
    """
    # Validate JSON size to prevent DoS attacks
    MAX_JSON_SIZE = 1024 * 1024  # 1MB
    if len(request.body) > MAX_JSON_SIZE:
        return JsonResponse({'status': 'error', 'message': 'Payload too large'}, status=413)
    
    try:
        data = json.loads(request.body)
        rating_value = int(data.get('rating'))
        
        if not 1 <= rating_value <= 5:
            return JsonResponse({'status': 'error', 'message': 'Invalid rating value'}, status=400)
            
        test_bank = get_object_or_404(TestBank, slug=slug, is_active=True)
        
        # Check if user has access
        has_access = UserTestAccess.objects.filter(
            user=request.user,
            test_bank=test_bank,
            is_active=True
        ).exists()
        
        if not has_access:
            return JsonResponse({'status': 'error', 'message': 'You must have access to rate this test bank'}, status=403)
            
        # Create or update rating
        from .models import TestBankRating
        TestBankRating.objects.update_or_create(
            user=request.user,
            test_bank=test_bank,
            defaults={'rating': rating_value}
        )
        
        return JsonResponse({'status': 'success'})
        
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def contact(request):
    """
    Contact page view.
    
    Displays a contact form for users to send messages.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            messages.success(request, _('Thank you for your message! We will get back to you soon.'))
            return redirect('catalog:contact')
    else:
        form = ContactForm()
    
    return render(request, 'catalog/contact.html', {
        'form': form,
    })


def search(request):
    """
    Search view that searches across multiple models.
    
    Searches:
    - TestBank (title, description)
    - Category (name, description)
    - BlogPost (title, content, excerpt) - from CMS
    - ForumTopic (title, content) - from Forum
    
    Returns results categorized by type.
    """
    from django.db import DatabaseError
    
    query = request.GET.get('q', '').strip()
    results = {
        'test_banks': [],
        'categories': [],
        'blog_posts': [],
        'forum_topics': [],
    }
    
    # Validate query - must be at least 2 characters
    if not query:
        return render(request, 'catalog/search_results.html', {
            'query': '',
            'results': results,
            'error': None,
        })
    
    if len(query) < 2:
        return render(request, 'catalog/search_results.html', {
            'query': query,
            'results': results,
            'error': 'Search query must be at least 2 characters long.',
        })
    
    try:
        # Search TestBanks
        test_banks = TestBank.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            is_active=True
        ).select_related('category', 'certification').annotate(
            user_count=Count('user_accesses', filter=Q(user_accesses__is_active=True))
        ).order_by('-user_count', '-average_rating')[:10]
        results['test_banks'] = list(test_banks)
        
        # Search Categories
        categories = Category.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).annotate(
            test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
        ).order_by('name')[:10]
        results['categories'] = list(categories)
        
        # Search Blog Posts (from CMS)
        try:
            from cms.models import BlogPost
            blog_posts = BlogPost.objects.filter(
                Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query),
                status='published'
            ).order_by('-published_at', '-created_at')[:10]
            results['blog_posts'] = list(blog_posts)
        except (ImportError, DatabaseError) as e:
            # Log error but don't fail the entire search
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Error searching blog posts: {str(e)}')
        
        # Search Forum Topics
        try:
            from forum.models import ForumTopic
            forum_topics = ForumTopic.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                is_locked=False
            ).select_related('author', 'category').order_by('-last_activity_at', '-created_at')[:10]
            results['forum_topics'] = list(forum_topics)
        except (ImportError, DatabaseError) as e:
            # Log error but don't fail the entire search
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Error searching forum topics: {str(e)}')
            
    except DatabaseError as e:
        # Handle database errors gracefully
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Database error in search: {str(e)}')
        return render(request, 'catalog/search_results.html', {
            'query': query,
            'results': results,
            'error': 'An error occurred while searching. Please try again.',
        })
    
    # Calculate total results count
    total_results = sum(len(results[key]) for key in results)
    
    return render(request, 'catalog/search_results.html', {
        'query': query,
        'results': results,
        'error': None,
        'total_results': total_results,
    })
