"""
Utility functions for catalog app, including JSON import functionality.
"""

import json

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.text import slugify

from .models import AnswerOption, Category, Certification, Question, TestBank


def import_test_bank_from_json(json_data, update_existing=None):
    """
    Import a test bank with questions and answers from JSON data.

    Args:
        json_data: Dictionary containing test bank and questions data
        update_existing: Optional TestBank instance to update instead of creating new

    Returns:
        Tuple of (test_bank, created_questions_count, errors, created_items)
        - test_bank: The created or updated TestBank instance
        - created_questions_count: Number of questions successfully imported
        - errors: List of warning/error messages
        - created_items: List of categories/certifications that were created

    Raises:
        ValidationError: If JSON structure is invalid
    """
    errors = []

    try:
        # Validate JSON structure
        if 'test_bank' not in json_data:
            raise ValidationError('JSON must contain a "test_bank" key')

        if 'questions' not in json_data:
            raise ValidationError('JSON must contain a "questions" key')

        test_bank_data = json_data['test_bank']
        questions_data = json_data['questions']

        # Validate required fields
        required_fields = ['title', 'description']
        for field in required_fields:
            if field not in test_bank_data:
                raise ValidationError(f'Test bank data must contain "{field}" field')

        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Get or create category/certification
            category = None
            certification = None

            # Track if any hierarchy field was provided (even if invalid)
            has_category_field = 'category' in test_bank_data and test_bank_data.get('category')
            has_certification_field = 'certification' in test_bank_data and test_bank_data.get('certification')

            # Check if at least one hierarchy field was provided
            if not has_category_field and not has_certification_field:
                raise ValidationError('At least one of category or certification must be specified in the JSON file.')

            # Helper function to get or create category by name or slug
            def get_or_create_category(name_or_slug):
                """Get existing category by slug or name, or create new one."""
                name_or_slug = name_or_slug.strip() if name_or_slug else None
                if not name_or_slug:
                    return None, False

                # Try to find by slug first
                category = Category.objects.filter(slug=slugify(name_or_slug)).first()
                if category:
                    return category, False

                # Try to find by name (case-insensitive)
                category = Category.objects.filter(name__iexact=name_or_slug).first()
                if category:
                    return category, False

                # Create new category
                category = Category.objects.create(
                    name=name_or_slug,
                    slug=slugify(name_or_slug)
                )
                return category, True

            # Helper function to get or create certification by name or slug
            def get_or_create_certification(name_or_slug, parent_category, difficulty='easy'):
                """Get existing certification by slug or name with difficulty level, or create new one."""
                name_or_slug = name_or_slug.strip() if name_or_slug else None
                if not name_or_slug:
                    return None, False

                if not parent_category:
                    raise ValidationError(f'Certification "{name_or_slug}" requires a parent category.')

                # Normalize difficulty level
                difficulty_map = {
                    'easy': 'easy',
                    'beginner': 'easy',
                    'medium': 'medium',
                    'intermediate': 'medium',
                    'hard': 'advanced',
                    'advanced': 'advanced'
                }
                normalized_difficulty = difficulty_map.get(difficulty.lower(), 'easy')

                # Generate slug with difficulty level
                base_slug = slugify(name_or_slug)
                expected_slug = f"{base_slug}-{normalized_difficulty}"

                # Try to find by slug with difficulty level
                certification = Certification.objects.filter(
                    slug=expected_slug,
                    category=parent_category,
                    difficulty_level=normalized_difficulty
                ).first()
                if certification:
                    return certification, False

                # Try to find by name and difficulty level (case-insensitive)
                certification = Certification.objects.filter(
                    name__iexact=name_or_slug,
                    category=parent_category,
                    difficulty_level=normalized_difficulty
                ).first()
                if certification:
                    return certification, False

                # Check if exists with same name but different difficulty (this is allowed)
                existing_same_name = Certification.objects.filter(
                    name__iexact=name_or_slug,
                    category=parent_category
                ).exclude(difficulty_level=normalized_difficulty).first()
                if existing_same_name:
                    # This is fine - same certification can exist with different difficulty
                    pass

                # Create new certification with difficulty level
                certification = Certification.objects.create(
                    name=name_or_slug,
                    slug=expected_slug,
                    category=parent_category,
                    difficulty_level=normalized_difficulty
                )
                return certification, True

            # Track what was created for feedback
            created_items = []

            # Process category first (required for certification)
            if has_category_field:
                category_value = test_bank_data['category']
                category, was_created = get_or_create_category(category_value)
                if category:
                    if was_created:
                        created_items.append(f'Category: "{category.name}" (created)')
                    else:
                        created_items.append(f'Category: "{category.name}" (existing)')

            # Process certification (requires category)
            if has_certification_field:
                if not category:
                    raise ValidationError('Certification requires a category. Please specify "category" in your JSON file.')
                certification_value = test_bank_data['certification']
                # Get difficulty level from test_bank_data for certification
                difficulty = test_bank_data.get('difficulty_level', 'easy').lower()
                certification, was_created = get_or_create_certification(certification_value, category, difficulty)
                if certification:
                    if was_created:
                        created_items.append(f'Certification: "{certification.name}" ({certification.get_difficulty_level_display()}) (created under {category.name})')
                    else:
                        created_items.append(f'Certification: "{certification.name}" ({certification.get_difficulty_level_display()}) (existing under {category.name})')

            # Validate at least one hierarchy level was successfully created/found
            if not category and not certification:
                raise ValidationError('Failed to create or find category or certification.')

            # Create or update test bank
            if update_existing:
                test_bank = update_existing
                test_bank.title = test_bank_data['title']
                test_bank.description = test_bank_data['description']
                test_bank.category = category
                test_bank.certification = certification
            else:
                # Generate slug from title
                slug = slugify(test_bank_data['title'])
                # Ensure slug is unique
                base_slug = slug
                counter = 1
                while TestBank.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                test_bank = TestBank(
                    title=test_bank_data['title'],
                    slug=slug,
                    description=test_bank_data['description'],
                    category=category,
                    certification=certification
                )

            # Set optional fields
            if 'difficulty_level' in test_bank_data:
                difficulty = test_bank_data['difficulty_level'].lower()
                # Map common variations to valid choices
                difficulty_map = {
                    'easy': 'easy',
                    'beginner': 'easy',
                    'medium': 'medium',
                    'intermediate': 'medium',
                    'hard': 'advanced',
                    'advanced': 'advanced'
                }
                test_bank.difficulty_level = difficulty_map.get(difficulty, 'easy')

            if 'price' in test_bank_data:
                test_bank.price = float(test_bank_data['price'])

            if 'is_active' in test_bank_data:
                test_bank.is_active = bool(test_bank_data['is_active'])

            # Set certification metadata fields
            if 'certification_domain' in test_bank_data:
                test_bank.certification_domain = test_bank_data['certification_domain'].strip() if test_bank_data['certification_domain'] else None

            if 'organization' in test_bank_data:
                test_bank.organization = test_bank_data['organization'].strip() if test_bank_data['organization'] else None

            if 'official_url' in test_bank_data:
                test_bank.official_url = test_bank_data['official_url'].strip() if test_bank_data['official_url'] else None

            if 'certification_details' in test_bank_data:
                test_bank.certification_details = test_bank_data['certification_details'].strip() if test_bank_data['certification_details'] else None

            test_bank.save()

            # If updating, clear existing questions
            if update_existing:
                Question.objects.filter(test_bank=test_bank).delete()

            # Import questions
            created_questions_count = 0
            for idx, question_data in enumerate(questions_data, start=1):
                try:
                    # Validate question data
                    if 'question_text' not in question_data:
                        errors.append(f'Question {idx}: Missing "question_text" field')
                        continue

                    if 'options' not in question_data or not question_data['options']:
                        errors.append(f'Question {idx}: Missing or empty "options" field')
                        continue

                    # Create question
                    question = Question(
                        test_bank=test_bank,
                        question_text=question_data['question_text'],
                        question_type=question_data.get('question_type', 'mcq_single'),
                        explanation=question_data.get('explanation', ''),
                        order=question_data.get('order', idx),
                        is_active=question_data.get('is_active', True)
                    )
                    question.save()

                    # Create answer options
                    for opt_idx, option_data in enumerate(question_data['options'], start=1):
                        if 'option_text' not in option_data:
                            errors.append(f'Question {idx}, Option {opt_idx}: Missing "option_text" field')
                            continue

                        AnswerOption.objects.create(
                            question=question,
                            option_text=option_data['option_text'],
                            is_correct=option_data.get('is_correct', False),
                            order=option_data.get('order', opt_idx)
                        )

                    created_questions_count += 1

                except Exception as e:
                    errors.append(f'Question {idx}: {str(e)}')
                    continue

            return test_bank, created_questions_count, errors, created_items

    except Exception as e:
        raise ValidationError(f'Error importing test bank: {str(e)}') from e


def parse_json_file(json_file):
    """
    Parse JSON file and return dictionary.

    Args:
        json_file: Django UploadedFile object

    Returns:
        Dictionary containing parsed JSON data

    Raises:
        ValidationError: If file cannot be parsed
    """
    try:
        # Read file content
        content = json_file.read()

        # Try to decode as UTF-8
        try:
            content_str = content.decode('utf-8')
        except UnicodeDecodeError as e:
            raise ValidationError('File must be UTF-8 encoded') from e

        # Parse JSON
        try:
            return json.loads(content_str)
        except json.JSONDecodeError as e:
            raise ValidationError(f'Invalid JSON format: {str(e)}') from e

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f'Error reading file: {str(e)}') from e

