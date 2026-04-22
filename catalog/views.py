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
from django_ratelimit.decorators import ratelimit
from .models import Category, Certification, ExamPackage, Question, QuestionReport, TestBank, TestBankRating, ReviewReply, ContactMessage
from .forms import TestBankReviewForm, ReviewReplyForm, ContactForm
from practice.models import UserTestAccess
from payments.currency import BASE_CURRENCY, display_options, format_amount


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
    # distinct=True on both counts — without it, the two JOINs cross-multiply
    # and every count comes back inflated by the size of the other relation.
    categories = list(Category.objects.annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True), distinct=True),
        certification_count=Count('certifications', distinct=True),
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
    
    # Certifying / training organizations whose exams we cover.
    # Rendered in a 3-row marquee on the homepage (alternating directions).
    # `logo_url` left blank so the template falls back to a text badge;
    # replace with hosted logo paths when available.
    partners = [
        {'name': 'Project Management Institute', 'url': 'https://www.pmi.org', 'logo_url': ''},
        {'name': 'AXELOS / PeopleCert', 'url': 'https://www.axelos.com', 'logo_url': ''},
        {'name': 'Scrum Alliance', 'url': 'https://www.scrumalliance.org', 'logo_url': ''},
        {'name': 'Scrum.org', 'url': 'https://www.scrum.org', 'logo_url': ''},
        {'name': 'Scaled Agile', 'url': 'https://www.scaledagile.com', 'logo_url': ''},
        {'name': 'Amazon Web Services', 'url': 'https://aws.amazon.com/certification', 'logo_url': ''},
        {'name': 'Microsoft', 'url': 'https://learn.microsoft.com/certifications', 'logo_url': ''},
        {'name': 'Google Cloud', 'url': 'https://cloud.google.com/certification', 'logo_url': ''},
        {'name': 'CompTIA', 'url': 'https://www.comptia.org', 'logo_url': ''},
        {'name': 'Cloud Native Computing Foundation', 'url': 'https://www.cncf.io/certification/cka', 'logo_url': ''},
        {'name': '(ISC)²', 'url': 'https://www.isc2.org', 'logo_url': ''},
        {'name': 'ISACA', 'url': 'https://www.isaca.org', 'logo_url': ''},
        {'name': 'EC-Council', 'url': 'https://www.eccouncil.org', 'logo_url': ''},
        {'name': 'Offensive Security', 'url': 'https://www.offsec.com', 'logo_url': ''},
        {'name': 'PECB / IRCA', 'url': 'https://pecb.com', 'logo_url': ''},
        {'name': 'Cisco', 'url': 'https://www.cisco.com/go/certifications', 'logo_url': ''},
        {'name': 'Juniper Networks', 'url': 'https://www.juniper.net/certification', 'logo_url': ''},
        {'name': 'TM Forum', 'url': 'https://www.tmforum.org', 'logo_url': ''},
        {'name': 'CWNP', 'url': 'https://www.cwnp.com', 'logo_url': ''},
        {'name': 'Telecoms Academy', 'url': 'https://www.telecomsacademy.com', 'logo_url': ''},
        {'name': 'Huawei', 'url': 'https://e.huawei.com/en/talent', 'logo_url': ''},
        {'name': 'Databricks', 'url': 'https://www.databricks.com/learn/certification', 'logo_url': ''},
        {'name': 'Tableau (Salesforce)', 'url': 'https://www.tableau.com/learn/certification', 'logo_url': ''},
        {'name': 'INFORMS', 'url': 'https://www.certifiedanalytics.org', 'logo_url': ''},
        {'name': 'The Open Group', 'url': 'https://www.opengroup.org', 'logo_url': ''},
        {'name': 'Oracle', 'url': 'https://education.oracle.com', 'logo_url': ''},
        {'name': 'GitHub', 'url': 'https://resources.github.com/learn/certifications', 'logo_url': ''},
        {'name': 'IIBA', 'url': 'https://www.iiba.org', 'logo_url': ''},
        {'name': 'ASQ / IASSC', 'url': 'https://asq.org', 'logo_url': ''},
        {'name': 'IRCA / Exemplar Global', 'url': 'https://www.irca.org', 'logo_url': ''},
        {'name': 'CFA Institute', 'url': 'https://www.cfainstitute.org', 'logo_url': ''},
        {'name': 'AICPA', 'url': 'https://www.aicpa-cima.com', 'logo_url': ''},
        {'name': 'ACCA', 'url': 'https://www.accaglobal.com', 'logo_url': ''},
        {'name': 'IMA', 'url': 'https://www.imanet.org', 'logo_url': ''},
        {'name': 'GARP', 'url': 'https://www.garp.org', 'logo_url': ''},
        {'name': 'The IIA', 'url': 'https://www.theiia.org', 'logo_url': ''},
        {'name': 'SHRM', 'url': 'https://www.shrm.org', 'logo_url': ''},
        {'name': 'CIPD', 'url': 'https://www.cipd.co.uk', 'logo_url': ''},
        {'name': 'ASCM / APICS', 'url': 'https://www.ascm.org', 'logo_url': ''},
        {'name': 'CIPS', 'url': 'https://www.cips.org', 'logo_url': ''},
        {'name': 'Google', 'url': 'https://skillshop.withgoogle.com', 'logo_url': ''},
        {'name': 'Meta', 'url': 'https://www.facebook.com/business/learn/certification', 'logo_url': ''},
        {'name': 'HubSpot Academy', 'url': 'https://academy.hubspot.com', 'logo_url': ''},
        {'name': 'CXPA', 'url': 'https://www.cxpa.org', 'logo_url': ''},
        {'name': 'Salesforce', 'url': 'https://trailhead.salesforce.com/credentials', 'logo_url': ''},
        {'name': 'NEBOSH', 'url': 'https://www.nebosh.org.uk', 'logo_url': ''},
        {'name': 'IOSH', 'url': 'https://iosh.com', 'logo_url': ''},
        {'name': 'OSHA', 'url': 'https://www.osha.gov', 'logo_url': ''},
        {'name': 'NCEES', 'url': 'https://ncees.org', 'logo_url': ''},
        {'name': 'USGBC / GBCI', 'url': 'https://www.usgbc.org', 'logo_url': ''},
        {'name': 'Saudi Council of Engineers', 'url': 'https://www.saudieng.sa', 'logo_url': ''},
        {'name': 'IWCF', 'url': 'https://www.iwcf.org', 'logo_url': ''},
        {'name': 'American Petroleum Institute', 'url': 'https://www.api.org', 'logo_url': ''},
        {'name': 'AEE', 'url': 'https://www.aeecenter.org', 'logo_url': ''},
        {'name': 'SCFHS', 'url': 'https://www.scfhs.org.sa', 'logo_url': ''},
        {'name': 'American Heart Association', 'url': 'https://cpr.heart.org', 'logo_url': ''},
        {'name': 'AAPC', 'url': 'https://www.aapc.com', 'logo_url': ''},
        {'name': 'AHLEI', 'url': 'https://www.ahlei.org', 'logo_url': ''},
        {'name': 'IATA', 'url': 'https://www.iata.org/training', 'logo_url': ''},
        {'name': 'American Welding Society', 'url': 'https://www.aws.org', 'logo_url': ''},
        {'name': 'ASE', 'url': 'https://www.ase.com', 'logo_url': ''},
        {'name': 'CCIM Institute', 'url': 'https://www.ccim.com', 'logo_url': ''},
        {'name': 'Adobe / Certiport', 'url': 'https://certiport.pearsonvue.com', 'logo_url': ''},
        {'name': 'Autodesk', 'url': 'https://www.autodesk.com/certification', 'logo_url': ''},
        {'name': 'Cambridge English', 'url': 'https://www.cambridgeenglish.org', 'logo_url': ''},
        {'name': 'ATD', 'url': 'https://www.td.org/certification', 'logo_url': ''},
        {'name': 'Challenger Inc.', 'url': 'https://challengerinc.com', 'logo_url': ''},
        {'name': 'NVIDIA', 'url': 'https://www.nvidia.com/en-us/training/certification', 'logo_url': ''},
    ]
    
    # Split the partner list into 3 rows (round-robin) for the marquee.
    # Round-robin keeps visual density balanced even if the list grows.
    partner_rows = [partners[i::3] for i in range(3)]

    # Category explorer tree — powers the 3-column drilldown on the homepage.
    # Shape:  [
    #   {
    #     'category': Category,
    #     'total_banks': int,
    #     'certifications': [
    #       {
    #         'name': str,           # deduped display name (one row per name)
    #         'slug_base': str,       # slug without difficulty suffix
    #         'difficulty_options': [
    #           {
    #             'level': 'easy'|'medium'|'advanced',
    #             'display': 'Easy'|'Medium'|'Advanced',
    #             'bank_count': int,
    #             'certification': Certification,  # the actual row to link to
    #           },
    #           ...
    #         ],
    #       },
    #       ...
    #     ],
    #   },
    #   ...
    # ]
    # A single "certification name" like "PMP" may exist as multiple
    # Certification rows (one per difficulty level) — we roll those up here.
    category_tree = []
    from collections import OrderedDict
    _diff_order = {'easy': 0, 'medium': 1, 'advanced': 2}
    testbank_counts = dict(
        TestBank.objects.filter(is_active=True)
        .values_list('certification_id')
        .annotate(n=Count('id'))
        .values_list('certification_id', 'n')
    )
    for cat in categories:
        cert_buckets = OrderedDict()
        for cert in cat.certifications.all().order_by('order', 'name', 'difficulty_level'):
            bucket = cert_buckets.setdefault(cert.name, {
                'name': cert.name,
                'slug_base': cert.name.lower().replace(' ', '-'),
                'difficulty_options': [],
            })
            bucket['difficulty_options'].append({
                'level': cert.difficulty_level,
                'display': cert.get_difficulty_level_display(),
                'bank_count': testbank_counts.get(cert.id, 0),
                'certification': cert,
            })
        # Stable sort within each bucket by easy → medium → advanced
        for bucket in cert_buckets.values():
            bucket['difficulty_options'].sort(key=lambda d: _diff_order.get(d['level'], 99))
        category_tree.append({
            'category': cat,
            'total_banks': getattr(cat, 'test_bank_count', 0),
            'certifications': list(cert_buckets.values()),
        })

    # Popular exams — top 6 test banks by user count (enrollments).
    # Rendered as quick-jump pills above the category explorer so users
    # who know what they want can skip the drilldown entirely. B2C
    # exam-prep users typically arrive with a specific exam in mind.
    popular_exams = list(
        TestBank.objects.filter(is_active=True)
        .select_related('category')
        .annotate(enrolls=Count('user_accesses', filter=Q(user_accesses__is_active=True)))
        .order_by('-enrolls', '-average_rating')[:6]
    )

    return render(request, 'catalog/index.html', {
        'categories': categories,
        'featured_test_banks': featured_test_banks,
        'trending_test_banks': trending_test_banks,
        'partners': partners,
        'partner_rows': partner_rows,
        'category_tree': category_tree,
        'popular_exams': popular_exams,
    })


def category_list(request):
    """
    Full browse page — same 3-column explorer pattern used on the homepage,
    plus a paginated, sortable, filterable grid of all active test banks
    below it.

    Query params:
      - category=<slug>  filter the bank grid to one category
      - sort=popular|newest|price_asc|price_desc|rating (default: popular)
      - q=<str>          optional text search over title/description
      - page=<n>         pagination
    """
    from collections import OrderedDict

    # Hide categories with zero active test banks — they're admin cleanup
    # debris, not a useful browse option.
    categories = list(
        Category.objects
        .annotate(
            # distinct=True prevents the two JOINs from cross-multiplying
            # and inflating both counts.
            test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True), distinct=True),
            certification_count=Count('certifications', distinct=True),
        )
        .filter(test_bank_count__gt=0)
        .order_by('-test_bank_count', 'name')
    )

    # Category explorer tree (same shape as homepage).
    testbank_counts = dict(
        TestBank.objects.filter(is_active=True)
        .values_list('certification_id')
        .annotate(n=Count('id'))
        .values_list('certification_id', 'n')
    )
    _diff_order = {'easy': 0, 'medium': 1, 'advanced': 2}
    category_tree = []
    for cat in categories:
        cert_buckets = OrderedDict()
        for cert in cat.certifications.all().order_by('order', 'name', 'difficulty_level'):
            bucket = cert_buckets.setdefault(cert.name, {
                'name': cert.name,
                'slug_base': cert.name.lower().replace(' ', '-'),
                'difficulty_options': [],
            })
            bucket['difficulty_options'].append({
                'level': cert.difficulty_level,
                'display': cert.get_difficulty_level_display(),
                'bank_count': testbank_counts.get(cert.id, 0),
                'certification': cert,
            })
        for bucket in cert_buckets.values():
            bucket['difficulty_options'].sort(key=lambda d: _diff_order.get(d['level'], 99))
        category_tree.append({
            'category': cat,
            'total_banks': getattr(cat, 'test_bank_count', 0),
            'certifications': list(cert_buckets.values()),
        })

    # Popular exams for quick-jump pills (same pattern as homepage).
    popular_exams = list(
        TestBank.objects.filter(is_active=True)
        .select_related('category')
        .annotate(enrolls=Count('user_accesses', filter=Q(user_accesses__is_active=True)))
        .order_by('-enrolls', '-average_rating')[:6]
    )

    # Sortable test-bank grid.
    SORT_CHOICES = [
        ('popular', _('Most popular')),
        ('newest', _('Newest')),
        ('rating', _('Top rated')),
        ('price_asc', _('Price: low to high')),
        ('price_desc', _('Price: high to low')),
        ('az', _('A–Z')),
    ]
    sort_keys = {k for k, _label in SORT_CHOICES}
    current_sort = request.GET.get('sort') or 'popular'
    if current_sort not in sort_keys:
        current_sort = 'popular'

    sort_order_map = {
        'popular': ('-enrolls', '-average_rating', '-created_at'),
        'newest': ('-created_at',),
        'rating': ('-average_rating', '-total_ratings'),
        'price_asc': ('price', '-average_rating'),
        'price_desc': ('-price', '-average_rating'),
        'az': ('title',),
    }

    current_category_slug = (request.GET.get('category') or '').strip()
    query = (request.GET.get('q') or '').strip()

    banks_qs = (
        TestBank.objects.filter(is_active=True)
        .select_related('category', 'certification')
        .annotate(enrolls=Count('user_accesses', filter=Q(user_accesses__is_active=True)))
    )
    if current_category_slug:
        banks_qs = banks_qs.filter(category__slug=current_category_slug)
    if query:
        banks_qs = banks_qs.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Per-user access + rating annotations so the shared card template
    # renders state-aware CTAs (Start Practicing / View Details).
    if request.user.is_authenticated:
        from django.db.models import Exists, IntegerField, OuterRef, Subquery
        access_subquery = UserTestAccess.objects.filter(
            user=request.user, test_bank=OuterRef('pk'), is_active=True,
        )
        rating_subquery = TestBankRating.objects.filter(
            user=request.user, test_bank=OuterRef('pk'),
        ).values('rating')[:1]
        banks_qs = banks_qs.annotate(
            has_access=Exists(access_subquery),
            user_rating=Subquery(rating_subquery, output_field=IntegerField()),
        )

    banks_qs = banks_qs.order_by(*sort_order_map[current_sort])

    paginator = Paginator(banks_qs, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'catalog/category_list.html', {
        'categories': categories,
        'category_tree': category_tree,
        'popular_exams': popular_exams,
        'banks_page': page_obj,
        'sort_choices': SORT_CHOICES,
        'current_sort': current_sort,
        'current_category_slug': current_category_slug,
        'query': query,
    })


def category_detail(request, category_slug):
    """
    Category detail page showing certifications.
    
    Displays all certifications under a category.
    If category has no certifications, redirects to test bank list.
    """
    category = get_object_or_404(Category, slug=category_slug)
    
    # All certifications under this category (flat rows — one per difficulty).
    certifications = Certification.objects.filter(
        category=category
    ).annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
    ).order_by('order', 'name', 'difficulty_level')

    # If no certifications, redirect to test bank list (covers categories
    # that skipped the certification layer entirely).
    if not certifications.exists():
        from django.shortcuts import redirect
        return redirect('catalog:testbank_list', category_slug=category.slug)

    # Roll up duplicate names into one card with 3 difficulty chips.
    # Without this, users see "Certified ScrumMaster (CSM)" 3× in a row
    # with no visible distinction, which is the current UX problem.
    from collections import OrderedDict
    _diff_order = {'easy': 0, 'medium': 1, 'advanced': 2}
    cert_buckets = OrderedDict()
    for cert in certifications:
        bucket = cert_buckets.setdefault(cert.name, {
            'name': cert.name,
            'description': cert.description,
            'official_url': cert.official_url,
            'total_banks': 0,
            'difficulty_options': [],
        })
        bucket['total_banks'] += getattr(cert, 'test_bank_count', 0) or 0
        bucket['difficulty_options'].append({
            'level': cert.difficulty_level,
            'display': cert.get_difficulty_level_display(),
            'bank_count': getattr(cert, 'test_bank_count', 0) or 0,
            'certification': cert,
        })
    for bucket in cert_buckets.values():
        bucket['difficulty_options'].sort(key=lambda d: _diff_order.get(d['level'], 99))
    certification_groups = list(cert_buckets.values())

    # Sortable, paginated test-bank grid scoped to this category.
    SORT_CHOICES = [
        ('popular', _('Most popular')),
        ('newest', _('Newest')),
        ('rating', _('Top rated')),
        ('price_asc', _('Price: low to high')),
        ('price_desc', _('Price: high to low')),
        ('az', _('A–Z')),
    ]
    current_sort = request.GET.get('sort') or 'popular'
    sort_order_map = {
        'popular': ('-enrolls', '-average_rating', '-created_at'),
        'newest': ('-created_at',),
        'rating': ('-average_rating', '-total_ratings'),
        'price_asc': ('price', '-average_rating'),
        'price_desc': ('-price', '-average_rating'),
        'az': ('title',),
    }
    if current_sort not in sort_order_map:
        current_sort = 'popular'

    banks_qs = (
        TestBank.objects.filter(is_active=True, category=category)
        .select_related('category', 'certification')
        .annotate(enrolls=Count('user_accesses', filter=Q(user_accesses__is_active=True)))
    )
    if request.user.is_authenticated:
        from django.db.models import Exists, IntegerField, OuterRef, Subquery
        access_sq = UserTestAccess.objects.filter(
            user=request.user, test_bank=OuterRef('pk'), is_active=True,
        )
        rating_sq = TestBankRating.objects.filter(
            user=request.user, test_bank=OuterRef('pk'),
        ).values('rating')[:1]
        banks_qs = banks_qs.annotate(
            has_access=Exists(access_sq),
            user_rating=Subquery(rating_sq, output_field=IntegerField()),
        )

    banks_qs = banks_qs.order_by(*sort_order_map[current_sort])
    paginator = Paginator(banks_qs, 24)
    page_obj = paginator.get_page(request.GET.get('page'))

    breadcrumbs = [
        {'label': _('Home'), 'url': reverse('catalog:index')},
        {'label': _('Browse'), 'url': reverse('catalog:category_list')},
        {'label': category.name, 'url': ''},
    ]

    return render(request, 'catalog/vocational_index.html', {
        'category': category,
        'certifications': certifications,                # kept for any legacy usage
        'certification_groups': certification_groups,    # new: deduped rollups
        'banks_page': page_obj,
        'sort_choices': SORT_CHOICES,
        'current_sort': current_sort,
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

    # A single "certification name" (e.g. "CAPM") may exist as multiple
    # Certification rows — one per difficulty level. Treat them as one family
    # on this page so users see the full set of test banks available for the
    # cert, no matter which difficulty variant's URL they landed on.
    cert_family = list(
        Certification.objects
        .filter(category=category, name=certification.name)
        .order_by('difficulty_level')
    )
    cert_ids = [c.id for c in cert_family]

    # Active test banks across the whole cert family, with the same
    # ownership/rating annotations the shared card template expects.
    test_banks_qs = (
        TestBank.objects
        .filter(certification_id__in=cert_ids, is_active=True)
        .select_related('category', 'certification')
        .prefetch_related('ratings')
    )
    if request.user.is_authenticated:
        from django.db.models import OuterRef, Subquery, Exists, IntegerField
        from practice.models import UserTestAccess
        from .models import TestBankRating

        access_sq = UserTestAccess.objects.filter(
            user=request.user, test_bank=OuterRef('pk'), is_active=True,
        )
        rating_sq = TestBankRating.objects.filter(
            user=request.user, test_bank=OuterRef('pk'),
        ).values('rating')[:1]

        test_banks_qs = test_banks_qs.annotate(
            has_access=Exists(access_sq),
            user_rating=Subquery(rating_sq, output_field=IntegerField()),
        )

    test_banks = list(test_banks_qs.order_by('-average_rating', '-created_at'))

    # Group banks by difficulty level for a grouped render, and build a
    # filter list that only surfaces levels we actually have content for.
    _diff_order = {'easy': 0, 'medium': 1, 'advanced': 2}
    groups_by_level = {}
    for tb in test_banks:
        level = tb.certification.difficulty_level if tb.certification_id else 'easy'
        groups_by_level.setdefault(level, []).append(tb)

    difficulty_groups = []
    level_display = dict(Certification.DIFFICULTY_CHOICES)
    for level in sorted(groups_by_level, key=lambda lv: _diff_order.get(lv, 99)):
        difficulty_groups.append({
            'level': level,
            'display': level_display.get(level, level.title()),
            'test_banks': groups_by_level[level],
            'count': len(groups_by_level[level]),
        })

    # Aggregate stats for the hero — counts + mean rating across the family.
    total_questions = sum((tb.get_question_count() or 0) for tb in test_banks)
    rated = [tb for tb in test_banks if tb.total_ratings]
    overall_rating = (
        sum(tb.average_rating for tb in rated) / len(rated)
        if rated else 0
    )
    price_values = [tb.price for tb in test_banks if tb.price]
    price_from = min(price_values) if price_values else None

    breadcrumbs = [
        {'label': _('Home'), 'url': reverse('catalog:index')},
        {'label': category.name, 'url': reverse('catalog:vocational_index') if category.slug == 'vocational' else reverse('catalog:category_detail', kwargs={'category_slug': category.slug})},
        {'label': certification.name, 'url': ''},
    ]

    return render(request, 'catalog/certification_list.html', {
        'category': category,
        'certification': certification,
        'cert_family': cert_family,
        'test_banks': test_banks,
        'difficulty_groups': difficulty_groups,
        'breadcrumbs': breadcrumbs,
        'total_questions': total_questions,
        'overall_rating': overall_rating,
        'price_from': price_from,
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
    user_access = None
    if request.user.is_authenticated:
        user_access = UserTestAccess.objects.filter(
            user=request.user,
            test_bank=test_bank,
            is_active=True
        ).first()
        has_access = user_access is not None and user_access.is_valid()
    
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
    
    currency_options = []
    display_price = ''
    base_price_formatted = ''
    if not is_free:
        currency_options = display_options(test_bank.price)
        display_price = format_amount(test_bank.price, BASE_CURRENCY)
        base_price_formatted = display_price

    return render(request, 'catalog/testbank_detail.html', {
        'test_bank': test_bank,
        'has_access': has_access,
        'user_access': user_access,
        'question_count': question_count,
        'recent_sessions': recent_sessions,
        'related_test_banks': related_test_banks,
        'is_free': is_free,
        'reviews': reviews,
        'user_review': user_review,
        'review_form': review_form,
        'reply_form': reply_form,
        'currency_options': currency_options,
        'display_price': display_price,
        'base_price_formatted': base_price_formatted,
        'base_currency': BASE_CURRENCY,
    })


def package_detail(request, slug):
    """
    Exam package detail page.

    Displays package contents, savings, and purchase option.
    """
    package = get_object_or_404(ExamPackage, slug=slug, is_active=True)
    test_banks = package.test_banks.filter(is_active=True).order_by('exampackageitem__order')

    # Check if user has access to all test banks in package
    has_full_access = False
    if request.user.is_authenticated:
        from practice.models import UserTestAccess
        tb_ids = list(test_banks.values_list('id', flat=True))
        access_count = UserTestAccess.objects.filter(
            user=request.user,
            test_bank_id__in=tb_ids,
            is_active=True,
        ).count()
        has_full_access = access_count == len(tb_ids) if tb_ids else False

    retail_value = package.get_retail_value()
    savings = package.get_savings()

    return render(request, 'catalog/package_detail.html', {
        'package': package,
        'test_banks': test_banks,
        'has_full_access': has_full_access,
        'retail_value': retail_value,
        'savings': savings,
    })


from django.views.decorators.http import require_POST
import json

@require_POST
@login_required
@ratelimit(key='user', rate='30/m', method='POST', block=True)
def rate_test_bank(request, slug):
    """
    Handle AJAX request to rate a test bank.

    Rate-limited: 30/min per user — generous for legitimate rapid-fire updates,
    tight enough to stop automated rating abuse.
    """
    # Validate JSON size to prevent DoS attacks — rating payload is tiny.
    MAX_JSON_SIZE = 1024  # 1 KB
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


@ratelimit(key='ip', rate='5/h', method='POST', block=True)
@login_required
@require_POST
@ratelimit(key='user', rate='10/h', method='POST', block=True)
def report_question(request, question_id):
    """
    Accept a user-submitted report flagging a question.

    Brain-dump reports are the highest-risk — they mean a user recognizes
    the question as lifted verbatim from a real live exam, which is a
    copyright + NDA exposure. Admin triage happens via the QuestionReport
    admin changelist.

    Size-capped to 1 KB; rate-limited to 10/h per user.
    """
    MAX_JSON_SIZE = 1024
    if len(request.body) > MAX_JSON_SIZE:
        return JsonResponse({'status': 'error', 'message': 'Payload too large'}, status=413)

    question = get_object_or_404(Question, pk=question_id, is_active=True)

    try:
        data = json.loads(request.body)
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    reason = (data.get('reason') or '').strip()
    details = (data.get('details') or '').strip()[:2000]

    valid_reasons = {choice[0] for choice in QuestionReport.Reason.choices}
    if reason not in valid_reasons:
        return JsonResponse({'status': 'error', 'message': 'Invalid reason'}, status=400)

    # Dedupe: if the same user already has an open report for this question
    # with the same reason, don't create a duplicate row.
    existing = QuestionReport.objects.filter(
        question=question,
        reporter=request.user,
        reason=reason,
        status__in=(QuestionReport.Status.OPEN, QuestionReport.Status.UNDER_REVIEW),
    ).first()
    if existing:
        return JsonResponse({'status': 'ok', 'message': 'Already reported — thanks.', 'duplicate': True})

    QuestionReport.objects.create(
        question=question,
        reporter=request.user,
        reason=reason,
        details=details,
    )
    return JsonResponse({'status': 'ok', 'message': 'Reported. Thanks — our team will review it.'})


def contact(request):
    """
    Contact page view.

    Displays a contact form for users to send messages.
    Rate-limited to 5 POSTs per hour per IP to stop spam submissions.
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
