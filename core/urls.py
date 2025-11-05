from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # Make sure this import exists
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # Redirect root to upload page
    path('', RedirectView.as_view(url='/upload/', permanent=False)),
    
    # Frontend pages
    path('upload/', views.upload_page, name='upload'),
    path('skill-gap/<int:session_id>/', views.skill_gap_page, name='skill_gap'),
    path('practice/<int:session_id>/', views.practice_page, name='practice'),
    path('results/<int:session_id>/', views.results_page, name='results'),
    path('api/analyze-speech/', views.analyze_speech, name='analyze_speech'),
    path('api/analyze-video-emotions/', views.analyze_video_emotions, name='analyze_video_emotions'),  # 👈 ADD THIS LINE


]