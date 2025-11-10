from django.urls import path
from django.views.generic import RedirectView  # ADD THIS IMPORT
from . import views

urlpatterns = [
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
    # NEW: WP2 Frontend Pages
    path('upload/', views.upload_page, name='upload'),
    path('skill-gap/<int:session_id>/', views.skill_gap_page, name='skill_gap'),
    path('practice/<int:session_id>/', views.practice_page, name='practice'),
    path('results/<int:session_id>/', views.results_page, name='results'),
    path('', RedirectView.as_view(url='/upload/', permanent=False)),
    path('api/analyze-speech/', views.analyze_speech, name='analyze_speech'),
    
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
    
    # Job Notification endpoints
    path('user-profiles/', views.create_user_profile, name='create_user_profile'),
    path('user-profiles/<str:email>/', views.manage_user_profile, name='manage_user_profile'),
    path('user-profiles/<str:email>/notifications/', views.get_user_notifications, name='get_user_notifications'),
    path('user-profiles/<str:email>/trigger-matching/', views.trigger_job_matching, name='trigger_job_matching'),
    path('jobs/search/', views.search_jobs_manually, name='search_jobs_manually'),
    path('jobs/recent/', views.get_recent_jobs, name='get_recent_jobs'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('email/test/', views.send_test_email, name='send_test_email'),
]