from django.urls import path
from django.views.generic import RedirectView  # ADD THIS IMPORT
from . import views
from .views import analyze_video_emotions


urlpatterns = [
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
    # NEW: WP2 Frontend Pages
    path('upload/', views.upload_page, name='upload'),
    path('skill-gap/<int:session_id>/', views.skill_gap_page, name='skill_gap'),
    path('practice/<int:session_id>/', views.practice_page, name='practice'),
    path('results/<int:session_id>/', views.results_page, name='results'),
    path('', RedirectView.as_view(url='/upload/', permanent=False)),
    path('api/analyze-speech/', views.analyze_speech, name='analyze_speech'),
    path("analyze-video-emotions/", analyze_video_emotions, name="analyze_video_emotions"),    
]