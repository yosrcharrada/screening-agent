from django.urls import path
from django.views.generic import RedirectView  # ADD THIS IMPORT
from . import views

urlpatterns = [
     # ADD THESE AUTH ROUTES
    path('test-llm/', views.test_llm_directly, name='test_llm'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('finalize-cv-signup/', views.finalize_cv_signup, name='finalize_cv_signup'),
    path('parse/', views.parse_documents, name='parse_documents'),
    path('analyze-direct/', views.analyze_direct, name='analyze_direct'),
    path('parse/', views.parse_cv_jd, name='parse'),
    path('sessions/<int:session_id>/skills/', views.get_skills, name='skills'),
    path('sessions/<int:session_id>/questions/', views.get_questions, name='questions'),
    path('transcribe/', views.transcribe_audio, name='transcribe'),
    path('score/', views.calculate_score, name='score'),
    path('sessions/<int:session_id>/report/', views.generate_report, name='report'),
    path('report/<int:session_id>/download.pdf', views.serve_mock_pdf, name='serve_pdf'),
    path('test/', views.test_page, name='test_page'),
     # NEW: Test scoring system
    path('test-scoring/<int:session_id>/', views.test_scoring_system, name='test_scoring'),
    # NEW: WP2 Frontend Pages
    path('upload/', views.upload_page, name='upload'),
    path('skill-gap/<int:session_id>/', views.skill_gap_page, name='skill_gap'),
    path('practice/<int:session_id>/', views.practice_page, name='practice'),
    path('results/<int:session_id>/', views.results_page, name='results'),
    path('', RedirectView.as_view(url='/upload/', permanent=False)),
    path('api/analyze-speech/', views.analyze_speech, name='analyze_speech'),
    path('api/sessions/<int:session_id>/generate-questions/', views.generate_questions, name='generate-questions'),
    path('api/sessions/<int:session_id>/questions/', views.get_questions, name='get-questions'),
    path('api/sessions/<int:session_id>/practice-questions/', views.get_session_questions, name='get_session_questions'),
    path('api/sessions/<int:session_id>/generate-more-questions/', views.generate_more_questions, name='generate_more_questions'),
    
    # Practice page
    path('practice/<int:session_id>/', views.practice_view, name='practice_view'),
    path('api/debug/sessions/<int:session_id>/questions/', views.debug_questions, name='debug_questions'),

    path('api/sessions/<int:session_id>/questions/', views.get_questions, name='get_questions'),
    path('api/sessions/<int:session_id>/generate-questions/', views.generate_questions, name='generate_questions'),
    
    # Practice page
    path('practice/<int:session_id>/', views.practice_view, name='practice_view'),

    # CV Analysis endpoints
    path('api/analyze-cv/', views.analyze_cv_standalone, name='analyze_cv_standalone'),
    path('api/analyze-cv-with-jd/', views.analyze_cv_with_jd, name='analyze_cv_with_jd'),
    path('api/cv-analysis-report/<int:session_id>/', views.get_cv_analysis_report, name='get_cv_analysis_report'),
    path('cv-analysis/', views.cv_analysis_page, name='cv_analysis_page'),
]