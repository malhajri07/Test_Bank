"""
URL configuration for practice app.

Routes for:
- Starting practice sessions
- Practice session page (with question navigation)
- Saving answers (AJAX)
- Submitting practice session
- Viewing results and review
"""

from django.urls import path
from . import views

app_name = 'practice'

urlpatterns = [
    # Start practice session
    path('start/<slug:testbank_slug>/', views.start_practice, name='start_practice'),
    
    # Practice session (with question navigation)
    path('session/<int:session_id>/', views.practice_session, name='practice_session'),
    
    # Save answer (AJAX endpoint)
    path('session/<int:session_id>/save-answer/', views.save_answer, name='save_answer'),
    
    # Save time remaining (AJAX endpoint)
    path('session/<int:session_id>/save-time/', views.save_time, name='save_time'),
    
    # Mark for review (AJAX endpoint)
    path('session/<int:session_id>/mark-review/', views.mark_for_review, name='mark_for_review'),
    
    # Submit practice session
    path('session/<int:session_id>/submit/', views.submit_practice, name='submit_practice'),
    
    # View results
    path('results/<int:session_id>/', views.practice_results, name='results'),
    
    # Certificate view
    path('certificate/<int:certificate_id>/', views.certificate_view, name='certificate_view'),
]

