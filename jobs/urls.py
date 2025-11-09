"""
URL configuration for jobs app.
"""
from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('preferences/', views.get_preferences, name='get_preferences'),
    path('preferences/update/', views.update_preferences, name='update_preferences'),
    path('trigger/', views.trigger_fetch_and_match, name='trigger_fetch'),
]
