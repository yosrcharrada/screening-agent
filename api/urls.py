from django.urls import path
from django.views.generic import RedirectView  # ADD THIS IMPORT
from . import views
from .views import analyze_video_emotions


urlpatterns = [
    path('test-llm/', views.test_llm_directly, name='test_llm'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('finalize-cv-signup/', views.finalize_cv_signup, name='finalize_cv_signup'),
    path('parse/', views.parse_documents, name='parse_documents'),
    path('analyze-direct/', views.analyze_direct, name='analyze_direct'),
    path('parse/', views.parse_cv_jd, name='parse'),
    path('sessions/<int:session_id>/skills/', views.get_skills, name='skills'),
    path('sessions/<int:session_id>/questions/', views.get_session_questions, name='get_questions'),
    path('sessions/<int:session_id>/generate-questions/', views.generate_questions, name='generate_questions'),
    path('sessions/<int:session_id>/generate-more-questions/', views.generate_more_questions, name='generate_more_questions'),    path('transcribe/', views.transcribe_audio, name='transcribe'),
    path('score/', views.calculate_score, name='score'),
    path('sessions/<int:session_id>/report/', views.generate_report, name='report'),
    path('report/<int:session_id>/download.pdf', views.serve_mock_pdf, name='serve_pdf'),
    path('test/', views.test_page, name='test_page'),
    path('sessions/<int:session_id>/latest-score/', views.get_latest_score, name='get_latest_score'),
    path('results/<int:session_id>/', views.results_page, name='results_page'),
    # NEW: WP2 Frontend Pages
    path('upload/', views.upload_page, name='upload'),
    path('skill-gap/<int:session_id>/', views.skill_gap_page, name='skill_gap'),
    path('practice/<int:session_id>/', views.practice_page, name='practice'),
    path('', RedirectView.as_view(url='/upload/', permanent=False)),
    path('api/analyze-speech/', views.analyze_speech, name='analyze_speech'),
    path("analyze-video-emotions/", analyze_video_emotions, name="analyze_video_emotions"),    


    path('sessions/<int:session_id>/generate-questions-xai/', views.generate_questions_with_xai, name='generate_questions_xai'),
    path('sessions/<int:session_id>/xai-explanations/', views.get_xai_explanations, name='get_xai_explanations'),
    path('sessions/<int:session_id>/judge-questions/', views.judge_questions_manual, name='judge_questions'),

    path('api/sessions/<int:session_id>/generate-questions/', views.generate_questions, name='generate_questions'),
    path('api/sessions/<int:session_id>/questions/', views.get_questions, name='get_questions'),

    # CV Analysis endpoints
    path('cv-analysis/', views.cv_analysis_page, name='cv_analysis_page'),
    path('analyze-cv/', views.analyze_cv_standalone, name='analyze_cv_standalone'),
    path('analyze-cv-with-jd/', views.analyze_cv_with_jd, name='analyze_cv_with_jd'),
    path('cv-analysis-report/<int:session_id>/', views.get_cv_analysis_report, name='get_cv_analysis_report'),


]