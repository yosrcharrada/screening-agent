# api/urls.py
from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Document processing
    path('parse/', views.parse_documents, name='parse_documents'),
    path('analyze-direct/', views.analyze_direct, name='analyze_direct'),
    
    # Session endpoints
    path('sessions/<int:session_id>/skills/', views.get_skills, name='skills'),
    path('sessions/<int:session_id>/report/', views.generate_report, name='report'),
    
    # Speech and scoring
    path('transcribe/', views.transcribe_audio, name='transcribe'),
    path('score/', views.calculate_score, name='score'),
    path('analyze-speech/', views.analyze_speech, name='analyze_speech'),
    
    # Questions endpoints - FIXED: Use get_session_questions for auto-generation
    path('sessions/<int:session_id>/questions/', views.get_session_questions, name='get_questions'),
    path('sessions/<int:session_id>/generate-questions/', views.generate_questions, name='generate_questions'),
    path('sessions/<int:session_id>/generate-more-questions/', views.generate_more_questions, name='generate_more_questions'),
    
    # CV Analysis endpoints
    path('analyze-cv/', views.analyze_cv_standalone, name='analyze_cv_standalone'),
    path('analyze-cv-with-jd/', views.analyze_cv_with_jd, name='analyze_cv_with_jd'),
    path('cv-analysis-report/<int:session_id>/', views.get_cv_analysis_report, name='get_cv_analysis_report'),
    
    # Debug endpoints
    path('debug/sessions/<int:session_id>/questions/', views.debug_questions, name='debug_questions'),
    
    # Frontend pages
    path('upload/', views.upload_page, name='upload'),
    path('skill-gap/<int:session_id>/', views.skill_gap_page, name='skill_gap'),
    path('practice/<int:session_id>/', views.practice_page, name='practice'),
    path('results/<int:session_id>/', views.results_page, name='results'),
    path('cv-analysis/', views.cv_analysis_page, name='cv_analysis_page'),
    path('', RedirectView.as_view(url='/upload/', permanent=False)),

    path('api/sessions/<int:session_id>/generate-questions-xai/', views.generate_questions_with_xai, name='generate_questions_xai'),
    path('api/sessions/<int:session_id>/xai-explanations/', views.get_xai_explanations, name='get_xai_explanations'),
    path('api/sessions/<int:session_id>/judge-questions/', views.judge_questions_manual, name='judge_questions'),

    path('api/sessions/<int:session_id>/generate-questions/', views.generate_questions, name='generate_questions'),
    path('api/sessions/<int:session_id>/questions/', views.get_questions, name='get_questions'),

    # XAI endpoints - ADD THESE
    path('sessions/<int:session_id>/generate-questions-xai/', views.generate_questions_with_xai, name='generate_questions_xai'),
    path('sessions/<int:session_id>/xai-explanations/', views.get_xai_explanations, name='get_xai_explanations'),
    path('sessions/<int:session_id>/judge-questions/', views.judge_questions_manual, name='judge_questions'),
]