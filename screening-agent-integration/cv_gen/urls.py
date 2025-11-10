"""
CV Generator URL Routing
"""

from django.urls import path
from . import views

app_name = 'cv_gen'

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # CV Management
    path('list/', views.cv_list, name='cv_list'),
    path('create/', views.cv_create, name='cv_create'),
    path('<int:cv_id>/preview/', views.cv_preview, name='cv_preview'),
    path('<int:cv_id>/edit/', views.cv_edit, name='cv_edit'),
    path('<int:cv_id>/delete/', views.cv_delete, name='cv_delete'),
    path('<int:cv_id>/download/', views.cv_download, name='cv_download'),
    path('<int:cv_id>/download_latex_pdf/', views.cv_download_latex_pdf, name='cv_download_latex_pdf'),
    path('<int:cv_id>/download_latex/', views.cv_download_latex, name='cv_download_latex'),
    # Feedback
    path('<int:cv_id>/feedback/', views.cv_feedback, name='cv_feedback'),
]