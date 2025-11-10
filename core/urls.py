from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from api import views
from django.conf import settings
from django.conf.urls.static import static

# Add this import so the AI AJAX endpoint can be reversed from templates
from cv_gen.views import ai_experience_summary

urlpatterns = [
    path('admin/', admin.site.urls),
<<<<<<< Updated upstream
    path('api/', include('api.urls')),
    
    # Redirect root to upload/signup page (preserve existing behaviour)
    path('', RedirectView.as_view(url='/api/signup/', permanent=False)),
    
    # Frontend pages (existing)
=======

    # API namespace
    path('api/', include('api.urls')),

    # Frontend pages (root-level)
>>>>>>> Stashed changes
    path('upload/', views.upload_page, name='upload'),
    path('skill-gap/<int:session_id>/', views.skill_gap_page, name='skill_gap'),
    path('practice/<int:session_id>/', views.practice_page, name='practice'),
    path('results/<int:session_id>/', views.results_page, name='results'),
<<<<<<< Updated upstream
    path('api/analyze-speech/', views.analyze_speech, name='analyze_speech'),
    path('api/analyze-video-emotions/', views.analyze_video_emotions, name='analyze_video_emotions'),

    path('cv-analysis/', views.cv_analysis_page, name='cv_analysis_page'),
=======

    # Auth pages (root-level)
>>>>>>> Stashed changes
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('finalize-cv-signup/', views.finalize_cv_signup, name='finalize_cv_signup'),

<<<<<<< Updated upstream
    path('api/sessions/<int:session_id>/generate-questions-xai/', views.generate_questions_with_xai, name='generate_questions_xai'),
    path('api/sessions/<int:session_id>/xai-explanations/', views.get_xai_explanations, name='get_xai_explanations'),
    path('api/sessions/<int:session_id>/judge-questions/', views.judge_questions_manual, name='judge_questions'),

    # CV Generator app routes (mounted at /cv/)
    path('cv/', include('cv_gen.urls')),

    # AI / AJAX endpoint used by cv_gen JS to generate experience summary
    path('ai/experience-summary/', ai_experience_summary, name='ai_experience_summary'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
=======
    # Home redirect
    path('', RedirectView.as_view(pattern_name='signup', permanent=False)),
]
>>>>>>> Stashed changes
