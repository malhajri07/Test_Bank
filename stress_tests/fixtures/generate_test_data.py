"""
Test data generator for stress testing.

Generates realistic test data using Faker:
- Categories, certifications
- Test banks with varying question counts
- User accounts and access records
- Practice sessions and answers

Usage:
    python manage.py shell < stress_tests/fixtures/generate_test_data.py
    OR
    python manage.py shell
    >>> exec(open('stress_tests/fixtures/generate_test_data.py').read())
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testbank_platform.settings')
django.setup()

from faker import Faker
from django.contrib.auth import get_user_model
from catalog.models import Category, Certification, TestBank, Question, AnswerOption
from practice.models import UserTestAccess, UserTestSession, UserAnswer
from decimal import Decimal
import random

fake = Faker()
User = get_user_model()


def generate_categories(count=20):
    """Generate categories."""
    categories = []
    for i in range(count):
        name = fake.word().capitalize() + " " + fake.word().capitalize()
        slug = name.lower().replace(' ', '-')
        
        category = Category.objects.create(
            name=name,
            slug=slug,
            description=fake.text(max_nb_chars=200)
        )
        categories.append(category)
        print(f"Created category: {category.name}")
    
    return categories


def generate_test_banks(categories, count_per_category=10):
    """Generate test banks for categories."""
    test_banks = []
    difficulty_levels = ['easy', 'medium', 'advanced']
    
    for category in categories:
        for i in range(count_per_category):
            title = fake.sentence(nb_words=4).rstrip('.')
            slug = title.lower().replace(' ', '-').replace(',', '').replace("'", '')
            
            test_bank = TestBank.objects.create(
                category=category,
                title=title,
                slug=slug,
                description=fake.text(max_nb_chars=500),
                price=Decimal(str(random.choice([0, 9.99, 19.99, 29.99, 49.99]))),
                difficulty_level=random.choice(difficulty_levels),
                is_active=True
            )
            test_banks.append(test_bank)
            print(f"Created test bank: {test_bank.title}")
    
    return test_banks


def generate_questions(test_banks, questions_per_testbank=20):
    """Generate questions for test banks."""
    question_types = ['mcq_single', 'mcq_multi', 'true_false']
    
    for test_bank in test_banks:
        for i in range(questions_per_testbank):
            question = Question.objects.create(
                test_bank=test_bank,
                question_text=fake.sentence(nb_words=10) + "?",
                question_type=random.choice(question_types),
                explanation=fake.text(max_nb_chars=200),
                order=i+1
            )
            
            # Generate answer options
            num_options = 4 if question.question_type != 'true_false' else 2
            
            correct_index = random.randint(0, num_options - 1)
            
            for j in range(num_options):
                AnswerOption.objects.create(
                    question=question,
                    option_text=fake.sentence(nb_words=5),
                    is_correct=(j == correct_index),
                    order=j+1
                )
        
        print(f"Created {questions_per_testbank} questions for {test_bank.title}")


def generate_users(count=50):
    """Generate test users."""
    users = []
    for i in range(count):
        username = fake.user_name() + str(i)
        email = fake.email()
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )
        users.append(user)
        print(f"Created user: {user.username}")
    
    return users


def generate_access_records(users, test_banks, access_percentage=0.3):
    """Generate access records for users."""
    access_count = 0
    for user in users:
        # Each user gets access to random test banks
        num_access = random.randint(1, int(len(test_banks) * access_percentage))
        selected_test_banks = random.sample(test_banks, min(num_access, len(test_banks)))
        
        for test_bank in selected_test_banks:
            UserTestAccess.objects.create(
                user=user,
                test_bank=test_bank,
                is_active=True
            )
            access_count += 1
    
    print(f"Created {access_count} access records")


def generate_practice_sessions(users, test_banks, sessions_per_user=2):
    """Generate practice sessions."""
    session_count = 0
    for user in users:
        # Get user's accessible test banks
        accessible_test_banks = TestBank.objects.filter(
            user_accesses__user=user,
            user_accesses__is_active=True
        ).distinct()
        
        if accessible_test_banks.exists():
            selected_test_banks = random.sample(
                list(accessible_test_banks),
                min(sessions_per_user, accessible_test_banks.count())
            )
            
            for test_bank in selected_test_banks:
                questions = list(Question.objects.filter(test_bank=test_bank))
                if questions:
                    question_ids = [q.id for q in questions]
                    random.shuffle(question_ids)
                    
                    session = UserTestSession.objects.create(
                        user=user,
                        test_bank=test_bank,
                        status=random.choice(['in_progress', 'completed']),
                        question_order=question_ids
                    )
                    
                    # Answer some questions
                    answered_questions = random.sample(
                        questions,
                        min(random.randint(5, len(questions)), len(questions))
                    )
                    
                    for question in answered_questions:
                        correct_option = AnswerOption.objects.filter(
                            question=question,
                            is_correct=True
                        ).first()
                        
                        if correct_option:
                            answer = UserAnswer.objects.create(
                                session=session,
                                question=question
                            )
                            answer.selected_options.set([correct_option])
                    
                    session_count += 1
    
    print(f"Created {session_count} practice sessions")


def main():
    """Main function to generate all test data."""
    print("=" * 60)
    print("Generating test data for stress testing...")
    print("=" * 60)
    
    # Generate categories
    print("\n1. Generating categories...")
    categories = generate_categories(count=20)
    
    # Generate test banks
    print("\n2. Generating test banks...")
    test_banks = generate_test_banks(categories, count_per_category=10)
    
    # Generate questions
    print("\n3. Generating questions...")
    generate_questions(test_banks, questions_per_testbank=20)
    
    # Generate users
    print("\n4. Generating users...")
    users = generate_users(count=50)
    
    # Generate access records
    print("\n5. Generating access records...")
    generate_access_records(users, test_banks, access_percentage=0.3)
    
    # Generate practice sessions
    print("\n6. Generating practice sessions...")
    generate_practice_sessions(users, test_banks, sessions_per_user=2)
    
    print("\n" + "=" * 60)
    print("Test data generation complete!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"- Categories: {Category.objects.count()}")
    print(f"- Test Banks: {TestBank.objects.count()}")
    print(f"- Questions: {Question.objects.count()}")
    print(f"- Users: {User.objects.count()}")
    print(f"- Access Records: {UserTestAccess.objects.count()}")
    print(f"- Practice Sessions: {UserTestSession.objects.count()}")
    print(f"- Answers: {UserAnswer.objects.count()}")


if __name__ == '__main__':
    main()

