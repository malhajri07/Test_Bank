"""
Utility functions for catalog app, including JSON import functionality.
"""

import json
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import TestBank, Question, AnswerOption, Category, SubCategory, Certification
from django.utils.text import slugify


def import_test_bank_from_json(json_data, update_existing=None):
    """
    Import a test bank with questions and answers from JSON data.
    
    Args:
        json_data: Dictionary containing test bank and questions data
        update_existing: Optional TestBank instance to update instead of creating new
        
    Returns:
        Tuple of (test_bank, created_questions_count, errors)
        
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
            # Get or create category/subcategory/certification
            category = None
            subcategory = None
            certification = None
            
            # Track if any hierarchy field was provided (even if invalid)
            has_category_field = 'category' in test_bank_data and test_bank_data.get('category')
            has_subcategory_field = 'subcategory' in test_bank_data and test_bank_data.get('subcategory')
            has_certification_field = 'certification' in test_bank_data and test_bank_data.get('certification')
            
            # Check if at least one hierarchy field was provided
            if not has_category_field and not has_subcategory_field and not has_certification_field:
                # Get available options for better error message
                available_categories = Category.objects.values_list('slug', 'name')[:10]
                available_subcategories = SubCategory.objects.values_list('slug', 'name')[:10]
                available_certifications = Certification.objects.values_list('slug', 'name')[:10]
                
                error_msg = 'At least one of category, subcategory, or certification must be specified in the JSON file.\n\n'
                if available_categories:
                    error_msg += 'Available categories: ' + ', '.join([f'{name} (slug: {slug})' for slug, name in available_categories]) + '\n'
                if available_subcategories:
                    error_msg += 'Available subcategories: ' + ', '.join([f'{name} (slug: {slug})' for slug, name in available_subcategories]) + '\n'
                if available_certifications:
                    error_msg += 'Available certifications: ' + ', '.join([f'{name} (slug: {slug})' for slug, name in available_certifications]) + '\n'
                raise ValidationError(error_msg)
            
            # Try to get category
            if has_category_field:
                category_slug = test_bank_data['category'].strip() if test_bank_data['category'] else None
                if category_slug:
                    try:
                        category = Category.objects.get(slug=category_slug)
                    except Category.DoesNotExist:
                        available = Category.objects.values_list('slug', flat=True)[:10]
                        error_msg = f'Category with slug "{category_slug}" not found.'
                        if available:
                            error_msg += f' Available category slugs: {", ".join(available)}'
                        errors.append(error_msg)
            
            # Try to get subcategory
            if has_subcategory_field:
                subcategory_slug = test_bank_data['subcategory'].strip() if test_bank_data['subcategory'] else None
                if subcategory_slug:
                    try:
                        subcategory = SubCategory.objects.get(slug=subcategory_slug)
                    except SubCategory.DoesNotExist:
                        available = SubCategory.objects.values_list('slug', flat=True)[:10]
                        error_msg = f'SubCategory with slug "{subcategory_slug}" not found.'
                        if available:
                            error_msg += f' Available subcategory slugs: {", ".join(available)}'
                        errors.append(error_msg)
            
            # Try to get certification
            if has_certification_field:
                certification_slug = test_bank_data['certification'].strip() if test_bank_data['certification'] else None
                if certification_slug:
                    try:
                        certification = Certification.objects.get(slug=certification_slug)
                    except Certification.DoesNotExist:
                        available = Certification.objects.values_list('slug', flat=True)[:10]
                        error_msg = f'Certification with slug "{certification_slug}" not found.'
                        if available:
                            error_msg += f' Available certification slugs: {", ".join(available)}'
                        errors.append(error_msg)
            
            # Validate at least one hierarchy level was successfully found
            if not category and not subcategory and not certification:
                # If we have errors, they were already added above
                if not errors:
                    raise ValidationError('At least one of category, subcategory, or certification must be specified and must exist in the database.')
                else:
                    # Combine all errors into one message
                    raise ValidationError('\n'.join(errors))
            
            # Create or update test bank
            if update_existing:
                test_bank = update_existing
                test_bank.title = test_bank_data['title']
                test_bank.description = test_bank_data['description']
                test_bank.category = category
                test_bank.subcategory = subcategory
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
                    subcategory=subcategory,
                    certification=certification
                )
            
            # Set optional fields
            if 'difficulty_level' in test_bank_data:
                test_bank.difficulty_level = test_bank_data['difficulty_level']
            
            if 'price' in test_bank_data:
                test_bank.price = float(test_bank_data['price'])
            
            if 'is_active' in test_bank_data:
                test_bank.is_active = bool(test_bank_data['is_active'])
            
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
            
            return test_bank, created_questions_count, errors
            
    except Exception as e:
        raise ValidationError(f'Error importing test bank: {str(e)}')


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
        except UnicodeDecodeError:
            raise ValidationError('File must be UTF-8 encoded')
        
        # Parse JSON
        try:
            return json.loads(content_str)
        except json.JSONDecodeError as e:
            raise ValidationError(f'Invalid JSON format: {str(e)}')
            
    except Exception as e:
        raise ValidationError(f'Error reading file: {str(e)}')

