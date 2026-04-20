"""
Catalog app models for test banks, categories, questions, and answer options.

This module defines the core domain models:
- Category: Organizes test banks by level (School, College, Professional)
- TestBank: A purchasable product containing questions
- Question: Individual questions within a test bank
- AnswerOption: Answer choices for questions
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Category(models.Model):
    """
    Category model for organizing test banks.
    
    Categories represent different levels of education/certification:
    - School level: K-12 education
    - College level: Undergraduate/Graduate
    - Professional: Certifications (PMP, KPIs, etc.)
    
    Uses slug field for clean URL routing (e.g., /categories/school-level/)
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Category Name',
        help_text='Name of the category (e.g., School, College, Professional)'
    )
    
    # Slug for URL-friendly routing
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug',
        help_text='URL-friendly version of the name'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Detailed description of the category'
    )
    
    # Category image/icon
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name='Category Image',
        help_text='Image/icon for the category card'
    )
    
    # Optional JSON field for additional metadata (level details, tags, etc.)
    level_details = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name='Level Details',
        help_text='Additional metadata as JSON (tags, requirements, etc.)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for Category model."""
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        """String representation of the category."""
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get URL for category's test banks list page."""
        return reverse('catalog:testbank_list', kwargs={'category_slug': self.slug})


class Certification(models.Model):
    """
    Certification model for organizing test banks within a category.
    
    Certifications represent specific professional certifications or exams.
    For example, under "Vocational" category, we might have:
    - CompTIA IT Fundamentals (ITF+)
    - CompTIA A+
    - CompTIA Network+
    etc.
    
    Uses slug field for clean URL routing.
    """
    
    name = models.CharField(
        max_length=200,
        verbose_name='Certification Name',
        help_text='Name of the certification or exam'
    )
    
    # Slug for URL-friendly routing
    slug = models.SlugField(
        max_length=200,
        verbose_name='Slug',
        help_text='URL-friendly version of the name'
    )
    
    # ForeignKey to Category - each certification belongs to one category
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='certifications',
        verbose_name='Category',
        help_text='Category this certification belongs to'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Detailed description of the certification'
    )
    
    # Order field for custom ordering within category
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Order of this certification within the category'
    )
    
    # Difficulty level choices
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('advanced', 'Advanced'),
    ]
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='easy',
        verbose_name='Difficulty Level',
        help_text='Difficulty level of the certification'
    )
    
    # Official URL for the certification
    official_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Official URL',
        help_text='Official website URL for the certification or organization'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for Certification model."""
        verbose_name = 'Certification'
        verbose_name_plural = 'Certifications'
        ordering = ['order', 'name']
        constraints = [
            models.UniqueConstraint(fields=['category', 'slug', 'difficulty_level'], name='unique_certification_per_category_difficulty'),
        ]
        indexes = [
            models.Index(fields=['category', 'order']),
            models.Index(fields=['category', 'difficulty_level']),
        ]
    
    def __str__(self):
        """String representation of the certification."""
        return f"{self.category.name} - {self.name} ({self.get_difficulty_level_display()})"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided, including difficulty level for uniqueness."""
        if not self.slug:
            base_slug = slugify(self.name)
            # Include difficulty level in slug to ensure uniqueness
            self.slug = f"{base_slug}-{self.difficulty_level}"
        else:
            # Ensure slug includes difficulty level even if manually set
            base_slug = slugify(self.name)
            expected_slug = f"{base_slug}-{self.difficulty_level}"
            if not self.slug.endswith(f"-{self.difficulty_level}"):
                self.slug = expected_slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get URL for certification's test banks list page."""
        return reverse('catalog:certification_list', kwargs={
            'category_slug': self.category.slug,
            'certification_slug': self.slug
        })


class TestBank(models.Model):
    """
    TestBank model representing a purchasable test bank product.
    
    A TestBank is a collection of questions that users can purchase and practice.
    Each TestBank can belong to:
    - A Category (top level)
    - A Certification (within a category)
    
    At least one of category or certification must be assigned.
    
    Users purchase access to a TestBank, which grants them the ability to:
    - Practice questions multiple times
    - Review results and explanations
    - Track their progress
    """
    
    # ForeignKey to Category - each test bank can belong to a category
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='test_banks',
        verbose_name='Category',
        help_text='Category this test bank belongs to',
        null=True,
        blank=True
    )
    
    # ForeignKey to Certification - optional, for specific certification exams
    certification = models.ForeignKey(
        Certification,
        on_delete=models.CASCADE,
        related_name='test_banks',
        verbose_name='Certification',
        help_text='Certification this test bank belongs to (optional)',
        null=True,
        blank=True
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='Title',
        help_text='Title of the test bank'
    )
    
    # Slug for URL-friendly routing
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Slug',
        help_text='URL-friendly version of the title'
    )
    
    description = models.TextField(
        verbose_name='Description',
        help_text='Detailed description of the test bank content'
    )
    
    # Certification metadata fields
    certification_domain = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Certification Domain',
        help_text='Subject area or domain of the certification (e.g., Information Technology, Healthcare) - metadata field'
    )
    
    organization = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Organization',
        help_text='Organization or body that issues the certification (e.g., CompTIA, Microsoft, PMI)'
    )
    
    official_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Official URL',
        help_text='Official website URL for the certification or organization'
    )
    
    certification_details = models.TextField(
        blank=True,
        null=True,
        verbose_name='Certification Details',
        help_text='Additional details about the certification, requirements, or exam information'
    )
    
    # Test bank image/thumbnail
    image = models.ImageField(
        upload_to='testbanks/',
        blank=True,
        null=True,
        verbose_name='Test Bank Image',
        help_text='Image/thumbnail for the test bank card'
    )
    
    # Difficulty level choices
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('advanced', 'Advanced'),
    ]
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='easy',
        verbose_name='Difficulty Level',
        help_text='Difficulty level of the test bank'
    )
    
    # Price for purchasing access (in USD or configured currency)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Price',
        help_text='Price to purchase access to this test bank'
    )
    
    # Time limit for practice sessions (in minutes, null = no time limit)
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Time Limit (minutes)',
        help_text='Time limit for practice sessions in minutes (null for no time limit)'
    )

    # Attempts per purchase (e.g., 1, 3, or 999 for unlimited)
    attempts_per_purchase = models.PositiveIntegerField(
        default=3,
        verbose_name='Attempts Per Purchase',
        help_text='Number of exam attempts granted per purchase (e.g., 1, 3, or 999 for unlimited)'
    )
    
    # Active flag - only active test banks are shown to users
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Whether this test bank is active and visible to users'
    )
    
    # Rating fields - cached for performance
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name='Average Rating',
        help_text='Average rating (0.00 to 5.00)'
    )
    
    total_ratings = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Ratings',
        help_text='Total number of ratings received'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for TestBank model."""
        verbose_name = 'Test Bank'
        verbose_name_plural = 'Test Banks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['certification', 'is_active']),
            models.Index(fields=['slug']),
        ]
    
    def clean(self):
        """Validate that at least one level (category or certification) is assigned."""
        from django.core.exceptions import ValidationError
        if not self.category and not self.certification:
            raise ValidationError('Test bank must belong to at least one level: category or certification.')
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided and validate."""
        if not self.slug:
            self.slug = slugify(self.title)
        # Auto-set category from certification if not set
        if not self.category:
            if self.certification:
                self.category = self.certification.category
        self.full_clean()  # Run validation
        super().save(*args, **kwargs)
    
    def __str__(self):
        """String representation of the test bank."""
        return self.title
    
    
    def get_absolute_url(self):
        """Get URL for test bank detail page."""
        return reverse('catalog:testbank_detail', kwargs={'slug': self.slug})
    
    def get_question_count(self):
        """Get total number of active questions in this test bank."""
        return self.questions.filter(is_active=True).count()
    
    def get_user_count(self):
        """Get total number of users who have selected/purchased this test bank."""
        return self.user_accesses.filter(is_active=True).count()
    
    def update_rating(self):
        """Update average rating and total ratings count from user ratings."""
        ratings = self.ratings.all()
        if ratings.exists():
            self.total_ratings = ratings.count()
            self.average_rating = ratings.aggregate(
                avg=models.Avg('rating')
            )['avg'] or 0.00
        else:
            self.total_ratings = 0
            self.average_rating = 0.00
        self.save(update_fields=['average_rating', 'total_ratings'])


class TestBankRating(models.Model):
    """
    TestBankRating model for user ratings of test banks.
    
    Users can rate test banks from 1 to 5 stars.
    Each user can only rate a test bank once (enforced by unique_together).
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='test_bank_ratings',
        verbose_name='User',
        help_text='User who gave the rating'
    )
    
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Test Bank',
        help_text='Test bank being rated'
    )
    
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Rating',
        help_text='Rating from 1 to 5 stars'
    )
    
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Review Title',
        help_text='Optional title for the review'
    )
    
    review = models.TextField(
        blank=True,
        verbose_name='Review',
        help_text='Optional review text'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for TestBankRating model."""
        verbose_name = 'Test Bank Rating'
        verbose_name_plural = 'Test Bank Ratings'
        constraints = [
            models.UniqueConstraint(fields=['user', 'test_bank'], name='unique_rating_per_user_testbank'),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        """String representation of the rating."""
        return f'{self.user.username} - {self.test_bank.title} - {self.rating} stars'
    
    def save(self, *args, **kwargs):
        """Save rating and update test bank's cached rating fields."""
        super().save(*args, **kwargs)
        self.test_bank.update_rating()
    
    def delete(self, *args, **kwargs):
        """Delete rating and update test bank's cached rating fields."""
        test_bank = self.test_bank
        super().delete(*args, **kwargs)
        test_bank.update_rating()


class ExamPackage(models.Model):
    """
    ExamPackage model for bundling multiple test banks at a discounted price.

    Per 01_backend.md: ExamPackage bundles multiple certification exams sold together
    at a discounted price (e.g., "CompTIA Starter Pack", "AWS Associate Bundle").
    """

    title = models.CharField(
        max_length=200,
        verbose_name='Title',
        help_text='Package name (e.g., CompTIA Starter Pack)',
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Slug',
        help_text='URL-friendly version of the title',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Detailed description of the package contents',
    )
    test_banks = models.ManyToManyField(
        TestBank,
        related_name='exam_packages',
        through='ExamPackageItem',
        blank=True,
        verbose_name='Test Banks',
        help_text='Test banks included in this package',
    )
    package_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Package Price',
        help_text='Discounted price for the bundle',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Whether this package is visible and purchasable',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Exam Package'
        verbose_name_plural = 'Exam Packages'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['slug']),
                   models.Index(fields=['is_active'])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('catalog:package_detail', kwargs={'slug': self.slug})

    def get_retail_value(self):
        """Sum of individual test bank prices."""
        return self.test_banks.aggregate(
            total=models.Sum('price')
        )['total'] or 0

    def get_savings(self):
        """Amount saved vs buying individually."""
        retail = self.get_retail_value()
        return max(0, retail - self.package_price)


class ExamPackageItem(models.Model):
    """Through model for ExamPackage M2M to TestBank (allows ordering)."""

    exam_package = models.ForeignKey(
        ExamPackage,
        on_delete=models.CASCADE,
        related_name='items',
    )
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='package_items',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = [['exam_package', 'test_bank']]


class ReviewReply(models.Model):
    """
    ReviewReply model for replies to test bank reviews.
    
    Users can reply to reviews, creating a discussion thread.
    """
    
    review = models.ForeignKey(
        TestBankRating,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name='Review',
        help_text='Review being replied to'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review_replies',
        verbose_name='User',
        help_text='User who wrote the reply'
    )
    
    content = models.TextField(
        max_length=1000,
        verbose_name='Content',
        help_text='Reply content'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for ReviewReply model."""
        verbose_name = 'Review Reply'
        verbose_name_plural = 'Review Replies'
        ordering = ['created_at']
    
    def __str__(self):
        """String representation of the reply."""
        return f'{self.user.username} - Reply to {self.review.user.username}\'s review'


class ContactMessage(models.Model):
    """
    ContactMessage model for storing user contact form submissions.
    """
    name = models.CharField(
        max_length=200,
        verbose_name='Name',
        help_text='Name of the person sending the message'
    )
    email = models.EmailField(
        verbose_name='Email',
        help_text='Email address for response'
    )
    subject = models.CharField(
        max_length=200,
        verbose_name='Subject',
        help_text='Subject of the message'
    )
    message = models.TextField(
        verbose_name='Message',
        help_text='The message content'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Is Read',
        help_text='Whether the message has been read by an admin'
    )

    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']

    def __str__(self):
        return f'Contact from {self.name} - {self.subject}'


class QuestionDomain(models.Model):
    """
    QuestionDomain model for grouping questions within a test bank by topic.

    Enables per-topic analytics on practice results (e.g. "Networking: 60%",
    "Security: 85%"). Scoped per test bank — each certification defines its
    own domain structure (CompTIA A+ has different domains than PMP).
    """

    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='domains',
        verbose_name='Test Bank',
        help_text='Test bank this domain belongs to',
    )
    name = models.CharField(
        max_length=150,
        verbose_name='Name',
        help_text='Domain/topic name (e.g. "Networking Fundamentals")',
    )
    slug = models.SlugField(
        max_length=150,
        verbose_name='Slug',
        help_text='URL-friendly identifier (unique per test bank)',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Optional description shown in analytics',
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Display order in analytics breakdowns',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Question Domain'
        verbose_name_plural = 'Question Domains'
        ordering = ['order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['test_bank', 'slug'],
                name='unique_domain_slug_per_testbank',
            ),
        ]
        indexes = [
            models.Index(fields=['test_bank', 'order']),
        ]

    def __str__(self):
        return f'{self.test_bank.title} — {self.name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Question(models.Model):
    """
    Question model representing individual questions within a test bank.

    Questions can be of different types:
    - MCQ single: Multiple choice with one correct answer
    - MCQ multi: Multiple choice with multiple correct answers
    - True/False: Boolean question

    Each question has answer options (AnswerOption) and an explanation shown after answering.

    Optionally tagged with a QuestionDomain for per-topic analytics on
    practice results.
    """

    # ForeignKey to TestBank - each question belongs to one test bank
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Test Bank',
        help_text='Test bank this question belongs to'
    )

    # ForeignKey to QuestionDomain — optional; enables weak-area analytics.
    # Nullable so existing questions and test banks without domain taxonomy
    # continue to work unchanged.
    domain = models.ForeignKey(
        'QuestionDomain',
        on_delete=models.SET_NULL,
        related_name='questions',
        null=True,
        blank=True,
        verbose_name='Domain',
        help_text='Topic/domain for analytics grouping (optional)',
    )
    
    question_text = models.TextField(
        verbose_name='Question Text',
        help_text='The question content'
    )
    
    # Question type choices
    QUESTION_TYPE_CHOICES = [
        ('mcq_single', 'Multiple Choice (Single Answer)'),
        ('mcq_multi', 'Multiple Choice (Multiple Answers)'),
        ('true_false', 'True/False'),
    ]
    
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='mcq_single',
        verbose_name='Question Type',
        help_text='Type of question'
    )
    
    # Explanation shown to user after answering
    explanation = models.TextField(
        blank=True,
        verbose_name='Explanation',
        help_text='Explanation shown after user answers the question'
    )
    
    # Active flag - only active questions are shown in practice sessions
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Whether this question is active'
    )
    
    # Order field for custom ordering of questions
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Order of this question within the test bank'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for Question model."""
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['test_bank', 'is_active']),
        ]
    
    def __str__(self):
        """String representation of the question."""
        return f"{self.test_bank.title} - Question {self.order}"
    
    def get_correct_answers(self):
        """Get all correct answer options for this question."""
        return self.answer_options.filter(is_correct=True)


class QuestionReport(models.Model):
    """
    User-submitted report flagging a question for admin review.

    Primary purpose is containment of "brain-dump" content risk: if a user
    recognizes a question as copied verbatim from a real live certification
    exam, they can flag it so admins can remove it before it draws a
    cease-and-desist (or worse, gets legitimate users' certifications
    revoked for NDA breach). Secondary uses: factual errors, wrong answer
    keys, outdated content.
    """

    class Reason(models.TextChoices):
        BRAIN_DUMP = 'brain_dump', 'Appears to be from a real exam (NDA/copyright concern)'
        FACTUAL_ERROR = 'factual_error', 'Factually wrong'
        WRONG_ANSWER = 'wrong_answer', 'Wrong answer marked as correct'
        TYPO = 'typo', 'Typo or formatting issue'
        OUTDATED = 'outdated', 'Outdated / no longer relevant'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        UNDER_REVIEW = 'under_review', 'Under review'
        RESOLVED = 'resolved', 'Resolved — fixed'
        DISMISSED = 'dismissed', 'Dismissed — no action'

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Question',
        help_text='The question being reported',
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='question_reports',
        null=True,
        blank=True,
        verbose_name='Reporter',
        help_text='User who reported (null if user later deleted)',
    )
    reason = models.CharField(
        max_length=32,
        choices=Reason.choices,
        default=Reason.FACTUAL_ERROR,
        verbose_name='Reason',
    )
    details = models.TextField(
        blank=True,
        max_length=2000,
        verbose_name='Details',
        help_text='Optional extra context from the reporter',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name='Status',
    )
    resolution_note = models.TextField(
        blank=True,
        max_length=2000,
        verbose_name='Resolution note',
        help_text='Admin note describing what was done',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Question Report'
        verbose_name_plural = 'Question Reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['question', 'status']),
            models.Index(fields=['reason', 'status']),
        ]

    def __str__(self):
        return f'{self.get_reason_display()} — Q#{self.question_id} ({self.get_status_display()})'

    def is_open(self):
        return self.status in (self.Status.OPEN, self.Status.UNDER_REVIEW)


class AnswerOption(models.Model):
    """
    AnswerOption model representing answer choices for questions.
    
    Each question can have multiple answer options.
    For MCQ single questions, exactly one option should be marked as correct.
    For MCQ multi questions, multiple options can be correct.
    For True/False questions, typically two options (True/False).
    
    The order field allows custom ordering of options.
    """
    
    # ForeignKey to Question - each answer option belongs to one question
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answer_options',
        verbose_name='Question',
        help_text='Question this answer option belongs to'
    )
    
    option_text = models.CharField(
        max_length=500,
        verbose_name='Option Text',
        help_text='The text of this answer option'
    )
    
    # Boolean flag indicating if this option is correct
    is_correct = models.BooleanField(
        default=False,
        verbose_name='Is Correct',
        help_text='Whether this answer option is correct'
    )
    
    # Order field for custom ordering of options
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Order of this option within the question'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    class Meta:
        """Meta options for AnswerOption model."""
        verbose_name = 'Answer Option'
        verbose_name_plural = 'Answer Options'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        """String representation of the answer option."""
        return f"{self.question} - Option {self.order}: {self.option_text[:50]}"
