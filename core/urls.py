from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # Make sure this import exists
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # Redirect root to upload page
    path('', RedirectView.as_view(url='/api/signup/', permanent=False)),
    
    # Frontend pages
    path('upload/', views.upload_page, name='upload'),
    path('skill-gap/<int:session_id>/', views.skill_gap_page, name='skill_gap'),
    path('practice/<int:session_id>/', views.practice_page, name='practice'),
    path('results/<int:session_id>/', views.results_page, name='results'),
    path('api/analyze-speech/', views.analyze_speech, name='analyze_speech'),
    path('api/analyze-video-emotions/', views.analyze_video_emotions, name='analyze_video_emotions'),  # 👈 ADD THIS LINE

    path('cv-analysis/', views.cv_analysis_page, name='cv_analysis_page'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('finalize-cv-signup/', views.finalize_cv_signup, name='finalize_cv_signup'),

    path('api/sessions/<int:session_id>/generate-questions-xai/', views.generate_questions_with_xai, name='generate_questions_xai'),
    path('api/sessions/<int:session_id>/xai-explanations/', views.get_xai_explanations, name='get_xai_explanations'),
    path('api/sessions/<int:session_id>/judge-questions/', views.judge_questions_manual, name='judge_questions'),

]