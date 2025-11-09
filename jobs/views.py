"""
API views for job preferences and matching.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings

from .models import UserJobPreference
from .serializers import UserJobPreferenceSerializer
from .services.fetcher import fetch_all_sources
from .services.matcher import match_and_notify

import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_preferences(request):
    """Get or create job preferences for the authenticated user."""
    preference, created = UserJobPreference.objects.get_or_create(
        user=request.user
    )
    
    serializer = UserJobPreferenceSerializer(preference)
    
    return Response({
        'preference': serializer.data,
        'created': created
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    """Update job preferences for the authenticated user."""
    preference, _ = UserJobPreference.objects.get_or_create(
        user=request.user
    )
    
    serializer = UserJobPreferenceSerializer(
        preference,
        data=request.data,
        partial=True
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_fetch_and_match(request):
    """
    Manually trigger job fetching and matching (development only).
    Should be disabled in production or restricted to admin users.
    """
    # Check if in development mode
    if not getattr(settings, 'DEBUG', False):
        return Response({
            'error': 'This endpoint is only available in development mode'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Fetch jobs
        fetch_results = fetch_all_sources()
        total_fetched = sum(fetch_results.values())
        
        # Match and notify
        match_results = match_and_notify()
        
        return Response({
            'success': True,
            'fetched': {
                'total': total_fetched,
                'by_source': fetch_results
            },
            'matched': {
                'users_processed': match_results['users_processed'],
                'jobs_matched': match_results['jobs_matched'],
                'emails_sent': match_results['emails_sent'],
                'errors': match_results.get('errors', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in trigger_fetch_and_match: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
