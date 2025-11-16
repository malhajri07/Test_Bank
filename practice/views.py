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
from .models import UserTestSession, UserAnswer, UserTestAccess
from catalog.models import TestBank, Question
import random


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
    
    # Create new practice session
    with transaction.atomic():
        session = UserTestSession.objects.create(
            user=user,
            test_bank=test_bank,
            status='in_progress',
            total_questions=len(questions)
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
    
    # Get all questions for this test bank
    questions = list(session.test_bank.questions.filter(is_active=True).order_by('order'))
    
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
    
    # Get answer options for current question
    answer_options = current_question.answer_options.all().order_by('order')
    
    return render(request, 'practice/practice_session.html', {
        'session': session,
        'questions': questions,
        'current_question': current_question,
        'current_index': current_index,
        'answer_options': answer_options,
        'selected_option_ids': selected_option_ids,
        'existing_answer': existing_answer,
        'total_questions': len(questions),
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
    
    # Prepare review data
    review_data = []
    for answer in answers:
        correct_options = answer.question.get_correct_answers()
        review_data.append({
            'question': answer.question,
            'user_answer': answer,
            'selected_options': answer.selected_options.all(),
            'correct_options': correct_options,
            'is_correct': answer.is_correct,
        })
    
    return render(request, 'practice/practice_results.html', {
        'session': session,
        'review_data': review_data,
        'total_questions': session.total_questions,
        'correct_answers': session.correct_answers,
        'incorrect_answers': session.total_questions - session.correct_answers,
    })
