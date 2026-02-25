"""
Practice app views for test practice sessions and results.

This module provides views for:
- Starting a practice session
- Displaying questions during practice
- Submitting answers and calculating scores
- Reviewing results and explanations
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from .models import UserTestSession, UserAnswer, UserTestAccess, Certificate
from catalog.models import TestBank, Question
import random
from django.db.models import Count, Q, Avg


@login_required
def start_practice(request, testbank_slug):
    """
    Start a new practice session for a test bank.
    
    This view:
    1. Verifies user has access to the test bank
    2. Creates a new UserTestSession
    3. Loads questions (randomized order)
    4. Redirects to practice session page
    
    Args:
        testbank_slug: Slug of the test bank to practice
    """
    test_bank = get_object_or_404(TestBank, slug=testbank_slug, is_active=True)
    user = request.user
    
    # Check if user has access
    access = UserTestAccess.objects.filter(
        user=user,
        test_bank=test_bank,
        is_active=True
    ).first()
    
    if not access or not access.is_valid():
        messages.error(request, 'You do not have access to this test bank. Please purchase it first.')
        return redirect('catalog:testbank_detail', slug=testbank_slug)
    
    # Get active questions
    questions = list(test_bank.questions.filter(is_active=True).order_by('order'))
    
    if not questions:
        messages.error(request, 'This test bank has no questions available.')
        return redirect('catalog:testbank_detail', slug=testbank_slug)
    
    # Randomize question order
    question_ids = [q.id for q in questions]
    random.shuffle(question_ids)
    
    # Initialize time remaining if test bank has time limit
    time_remaining = None
    if test_bank.time_limit_minutes:
        time_remaining = test_bank.time_limit_minutes * 60  # Convert to seconds
    
    # Create new practice session with randomized question order
    with transaction.atomic():
        session = UserTestSession.objects.create(
            user=user,
            test_bank=test_bank,
            status='in_progress',
            total_questions=len(questions),
            question_order=question_ids,
            time_remaining_seconds=time_remaining
        )
    
    # Redirect to practice session page
    return redirect('practice:practice_session', session_id=session.pk)


@login_required
def practice_session(request, session_id):
    """
    Display practice session with questions.
    
    Shows:
    - Current question with answer options
    - Navigation (Previous/Next)
    - Progress indicator
    - Submit button when on last question
    
    Args:
        session_id: Primary key of the UserTestSession
    """
    session = get_object_or_404(UserTestSession, pk=session_id, user=request.user)
    
    # Ensure session belongs to current user
    if session.user != request.user:
        messages.error(request, 'You do not have permission to access this session.')
        return redirect('accounts:dashboard')
    
    # Prevent access to completed sessions
    if session.status == 'completed':
        return redirect('practice:results', session_id=session_id)
    
    # Get questions in randomized order (stored in session)
    if session.question_order:
        # Use stored randomized order
        question_ids = session.question_order
        # Create a dict for quick lookup
        all_questions = {q.id: q for q in session.test_bank.questions.filter(is_active=True)}
        # Build questions list in randomized order
        questions = [all_questions[qid] for qid in question_ids if qid in all_questions]
    else:
        # Fallback: if no order stored, get questions and randomize (for old sessions)
        questions = list(session.test_bank.questions.filter(is_active=True).order_by('order'))
        random.shuffle(questions)
        # Save the order for future reference
        session.question_order = [q.id for q in questions]
        session.save(update_fields=['question_order'])
    
    if not questions:
        messages.error(request, 'No questions available.')
        return redirect('accounts:dashboard')
    
    # Get current question index from query parameter (default to first)
    current_index = int(request.GET.get('q', 0))
    if current_index < 0 or current_index >= len(questions):
        current_index = 0
    
    current_question = questions[current_index]
    
    # Get user's existing answer for this question (if any)
    existing_answer = UserAnswer.objects.filter(
        session=session,
        question=current_question
    ).first()
    
    # Get selected option IDs if answer exists
    selected_option_ids = []
    if existing_answer:
        selected_option_ids = [opt.id for opt in existing_answer.selected_options.all()]
    
    # Get answer options for current question and randomize them
    answer_options = list(current_question.answer_options.all().order_by('order'))
    random.shuffle(answer_options)
    
    # Get all answered question IDs for navigation box
    answered_question_ids = set(
        UserAnswer.objects.filter(session=session)
        .values_list('question_id', flat=True)
    )
    
    # Calculate completion percentage based on answered questions
    answered_count = len(answered_question_ids)
    total_questions_count = len(questions)
    completion_percent = int((answered_count / total_questions_count * 100)) if total_questions_count > 0 else 0
    
    # Get marked for review question IDs
    marked_question_ids = set(
        UserAnswer.objects.filter(session=session, marked_for_review=True)
        .values_list('question_id', flat=True)
    )
    
    # Timer data
    has_timer = session.test_bank.time_limit_minutes is not None
    time_remaining = session.time_remaining_seconds if has_timer else None
    
    return render(request, 'practice/practice_session.html', {
        'session': session,
        'questions': questions,
        'current_question': current_question,
        'current_index': current_index,
        'answer_options': answer_options,
        'selected_option_ids': selected_option_ids,
        'existing_answer': existing_answer,
        'total_questions': total_questions_count,
        'answered_question_ids': answered_question_ids,
        'marked_question_ids': marked_question_ids,
        'answered_count': answered_count,
        'completion_percent': completion_percent,
        'has_timer': has_timer,
        'time_remaining': time_remaining,
        'time_limit_minutes': session.test_bank.time_limit_minutes,
    })


@login_required
def save_answer(request, session_id):
    """
    Save user's answer to a question (AJAX endpoint).
    
    This view handles saving answers during practice without submitting the entire session.
    Allows users to navigate back and forth between questions.
    
    Args:
        session_id: Primary key of the UserTestSession
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    session = get_object_or_404(UserTestSession, pk=session_id, user=request.user)
    
    # Prevent saving to completed sessions
    if session.status == 'completed':
        return JsonResponse({'error': 'Session already completed'}, status=400)
    
    question_id = request.POST.get('question_id')
    selected_option_ids = request.POST.getlist('selected_options[]')
    
    if not question_id or not selected_option_ids:
        return JsonResponse({'error': 'Missing question_id or selected_options'}, status=400)
    
    question = get_object_or_404(Question, pk=question_id, test_bank=session.test_bank)
    
    # Validate that question belongs to session's test bank (security check)
    if question.test_bank != session.test_bank:
        return JsonResponse({'error': 'Question does not belong to this session'}, status=400)
    
    # Get selected answer options
    selected_options = question.answer_options.filter(pk__in=selected_option_ids)
    
    if not selected_options.exists():
        return JsonResponse({'error': 'Invalid option IDs'}, status=400)
    
    # Save or update answer
    with transaction.atomic():
        answer, created = UserAnswer.objects.get_or_create(
            session=session,
            question=question,
            defaults={
                'is_correct': False,  # Will be updated below
            }
        )
        
        # Update selected options
        answer.selected_options.set(selected_options)
        
        # Check correctness
        answer.is_correct = answer.check_correctness()
        answer.save()
    
    return JsonResponse({
        'success': True,
        'is_correct': answer.is_correct,
    })


@login_required
def save_time(request, session_id):
    """
    Save time remaining for a practice session (AJAX endpoint).
    
    Args:
        session_id: Primary key of the UserTestSession
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    session = get_object_or_404(UserTestSession, pk=session_id, user=request.user)
    
    # Prevent saving to completed sessions
    if session.status == 'completed':
        return JsonResponse({'error': 'Session already completed'}, status=400)
    
    try:
        import json
        data = json.loads(request.body)
        time_remaining = data.get('time_remaining')
        
        if time_remaining is None:
            return JsonResponse({'error': 'Missing time_remaining'}, status=400)
        
        # Update time remaining
        session.time_remaining_seconds = int(time_remaining)
        session.save(update_fields=['time_remaining_seconds'])
        
        return JsonResponse({'success': True})
    except (ValueError, KeyError) as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def mark_for_review(request, session_id):
    """
    Mark or unmark a question for review (AJAX endpoint).
    
    Args:
        session_id: Primary key of the UserTestSession
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    session = get_object_or_404(UserTestSession, pk=session_id, user=request.user)
    
    # Prevent marking in completed sessions
    if session.status == 'completed':
        return JsonResponse({'error': 'Session already completed'}, status=400)
    
    try:
        import json
        data = json.loads(request.body)
        question_id = data.get('question_id')
        marked = data.get('marked', False)
        
        if not question_id:
            return JsonResponse({'error': 'Missing question_id'}, status=400)
        
        question = get_object_or_404(Question, pk=question_id, test_bank=session.test_bank)
        
        # Get or create answer
        answer, created = UserAnswer.objects.get_or_create(
            session=session,
            question=question,
            defaults={
                'is_correct': False,
                'marked_for_review': marked,
            }
        )
        
        # Update mark for review status
        answer.marked_for_review = marked
        answer.save(update_fields=['marked_for_review'])
        
        return JsonResponse({'success': True, 'marked': marked})
    except (ValueError, KeyError) as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def submit_practice(request, session_id):
    """
    Submit practice session and calculate final score.
    
    This view:
    1. Evaluates all answers
    2. Calculates score percentage
    3. Updates session status to 'completed'
    4. Redirects to results page
    
    Args:
        session_id: Primary key of the UserTestSession
    """
    session = get_object_or_404(UserTestSession, pk=session_id, user=request.user)
    
    # Ensure session belongs to current user
    if session.user != request.user:
        messages.error(request, 'You do not have permission to submit this session.')
        return redirect('accounts:dashboard')
    
    # Prevent resubmission
    if session.status == 'completed':
        return redirect('practice:results', session_id=session_id)
    
    # Calculate score
    with transaction.atomic():
        # Get all answers for this session
        answers = UserAnswer.objects.filter(session=session)
        
        # Count correct answers
        correct_count = answers.filter(is_correct=True).count()
        total_count = answers.count()
        
        # Update session
        session.correct_answers = correct_count
        session.total_questions = total_count
        
        # Calculate score percentage
        if total_count > 0:
            session.score = (correct_count / total_count) * 100
        else:
            session.score = 0
        
        # Mark as completed
        session.status = 'completed'
        session.completed_at = timezone.now()
        
        # Calculate duration if started_at exists
        if session.started_at:
            duration = timezone.now() - session.started_at
            session.duration_seconds = int(duration.total_seconds())
        
        session.save()
        
        # Generate certificate if score meets passing threshold (default 70%)
        passing_threshold = 70.00  # Can be made configurable per test bank
        if session.score and session.score >= passing_threshold:
            # Check if certificate already exists for this session
            if not Certificate.objects.filter(session=session).exists():
                certificate_number = Certificate.generate_certificate_number(session.user, session.test_bank)
                Certificate.objects.create(
                    user=session.user,
                    test_bank=session.test_bank,
                    session=session,
                    certificate_number=certificate_number,
                    score=session.score,
                    passing_threshold=passing_threshold
                )
    
    messages.success(request, 'Practice session completed! View your results below.')
    return redirect('practice:results', session_id=session_id)


@login_required
def practice_results(request, session_id):
    """
    Display practice session results and review.
    
    Shows:
    - Score and statistics
    - Total questions and correct/incorrect counts
    - Review of each question with:
      - Correct answer
      - User's answer
      - Explanation
    
    Args:
        session_id: Primary key of the UserTestSession
    """
    session = get_object_or_404(UserTestSession, pk=session_id, user=request.user)
    
    # Ensure session belongs to current user
    if session.user != request.user:
        messages.error(request, 'You do not have permission to view this session.')
        return redirect('accounts:dashboard')
    
    # Get all answers with related data
    answers = UserAnswer.objects.filter(
        session=session
    ).select_related('question').prefetch_related('selected_options', 'question__answer_options')
    
    # Create a dict of answers by question ID for quick lookup
    answers_dict = {answer.question.id: answer for answer in answers}
    
    # Prepare review data in randomized order (if stored) or original order
    review_data = []
    if session.question_order:
        # Use stored randomized order
        for question_id in session.question_order:
            if question_id in answers_dict:
                answer = answers_dict[question_id]
                correct_options = answer.question.get_correct_answers()
                review_data.append({
                    'question': answer.question,
                    'user_answer': answer,
                    'selected_options': answer.selected_options.all(),
                    'correct_options': correct_options,
                    'is_correct': answer.is_correct,
                    'marked_for_review': answer.marked_for_review,
                })
    else:
        # Fallback: use answers in their natural order
        for answer in answers:
            correct_options = answer.question.get_correct_answers()
            review_data.append({
                'question': answer.question,
                'user_answer': answer,
                'selected_options': answer.selected_options.all(),
                'correct_options': correct_options,
                'is_correct': answer.is_correct,
                'marked_for_review': answer.marked_for_review,
            })
    
    # Calculate weak area insights based on question categories
    # Group answers by test bank category to identify weak areas
    weak_areas = []
    if review_data:
        # Group by category (using test bank's category)
        category_performance = {}
        for review in review_data:
            category = review['question'].test_bank.category
            if category:
                category_name = category.name
                if category_name not in category_performance:
                    category_performance[category_name] = {'correct': 0, 'total': 0}
                category_performance[category_name]['total'] += 1
                if review['is_correct']:
                    category_performance[category_name]['correct'] += 1
        
        # Calculate percentage for each category and identify weak areas (< 60%)
        for category_name, stats in category_performance.items():
            if stats['total'] > 0:
                percentage = (stats['correct'] / stats['total']) * 100
                if percentage < 60:  # Weak area threshold
                    weak_areas.append({
                        'category': category_name,
                        'percentage': round(percentage, 1),
                        'correct': stats['correct'],
                        'total': stats['total']
                    })
        
        # Sort by percentage (lowest first)
        weak_areas.sort(key=lambda x: x['percentage'])
    
    # Check if certificate was generated
    certificate = None
    try:
        certificate = Certificate.objects.get(session=session)
    except Certificate.DoesNotExist:
        pass
    
    return render(request, 'practice/practice_results.html', {
        'session': session,
        'review_data': review_data,
        'total_questions': session.total_questions,
        'correct_answers': session.correct_answers,
        'incorrect_answers': session.total_questions - session.correct_answers,
        'weak_areas': weak_areas,
        'certificate': certificate,
    })


@login_required
def certificate_view(request, certificate_id):
    """
    Display certificate view page.
    
    Shows:
    - Certificate details
    - Certificate number
    - Score achieved
    - Issue date
    - Download option (if PDF available)
    
    Args:
        certificate_id: Primary key of the Certificate
    """
    certificate = get_object_or_404(Certificate, pk=certificate_id, user=request.user)
    
    # Ensure certificate belongs to current user
    if certificate.user != request.user:
        messages.error(request, 'You do not have permission to view this certificate.')
        return redirect('accounts:dashboard')
    
    return render(request, 'practice/certificate_view.html', {
        'certificate': certificate,
    })
