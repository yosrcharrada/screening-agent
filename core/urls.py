from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # Make sure this import exists
from api import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # Redirect root to upload page
    path('', RedirectView.as_view(url='/api/signup/', permanent=False)),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('finalize-cv-signup/', views.finalize_cv_signup, name='finalize_cv_signup'),
    # PDF Report endpoints
    path('api/generate-real-pdf/<int:session_id>/', views.generate_real_pdf, name='generate_real_pdf'),
    path('api/sessions/<int:session_id>/report/', views.generate_report, name='generate_report'),
    path('api/report/<int:session_id>/download.pdf', views.serve_mock_pdf, name='serve_pdf'),

    # Frontend pages
    path('upload/', views.upload_page, name='upload'),
    path('skill-gap/<int:session_id>/', views.skill_gap_page, name='skill_gap'),
    path('practice/<int:session_id>/', views.practice_page, name='practice'),
    path('results/<int:session_id>/', views.results_page, name='results'),
     path('api/analyze-speech/', views.analyze_speech, name='analyze_speech'),
     path('api/sessions/<int:session_id>/generate-questions/', views.generate_questions, name='generate-questions'),
    path('api/sessions/<int:session_id>/questions/', views.get_questions, name='get-questions'),
# CV Analysis endpoints
    path('api/analyze-cv/', views.analyze_cv_standalone, name='analyze_cv_standalone'),
    path('api/analyze-cv-with-jd/', views.analyze_cv_with_jd, name='analyze_cv_with_jd'),
    path('api/cv-analysis-report/<int:session_id>/', views.get_cv_analysis_report, name='get_cv_analysis_report'),
    path('cv-analysis/', views.cv_analysis_page, name='cv_analysis_page'),
]