# apps/users/cookie_consent_api.py
"""
Cookie Consent API Endpoints
Sync cookie preferences between frontend (localStorage) and backend (database)
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Count, Q
from .models import User, CookieConsent
import logging

logger = logging.getLogger(__name__)


# ==========================================
# SYNC COOKIE PREFERENCES (Logged-in Users)
# ==========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_cookie_preferences(request):
    """
    Sync cookie preferences from frontend to backend
    Called when logged-in user makes cookie choice
    
    POST /api/cookie-consent/sync/
    Body: {
        "essential": true,
        "analytics": false,
        "marketing": false,
        "preferences": false,
        "consent_type": "reject_all"  # or "accept_all" or "custom"
    }
    """
    try:
        user = request.user
        data = request.data
        
        # Update user's cookie preferences
        user.cookie_consent_given = True
        user.cookie_consent_date = timezone.now()
        user.cookie_preferences = {
            'essential': data.get('essential', True),
            'analytics': data.get('analytics', False),
            'marketing': data.get('marketing', False),
            'preferences': data.get('preferences', False),
        }
        user.save(update_fields=[
            'cookie_consent_given',
            'cookie_consent_date',
            'cookie_preferences'
        ])
        
        # Create detailed consent record
        CookieConsent.objects.create(
            user=user,
            essential=data.get('essential', True),
            analytics=data.get('analytics', False),
            marketing=data.get('marketing', False),
            preferences=data.get('preferences', False),
            consent_type=data.get('consent_type', 'custom'),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            page_url=request.META.get('HTTP_REFERER', ''),
        )
        
        # Deactivate old consents
        CookieConsent.objects.filter(
            user=user,
            is_active=True
        ).exclude(
            created_at=timezone.now()
        ).update(is_active=False)
        
        logger.info(f"✅ Synced cookie preferences for user {user.id}")
        
        return Response({
            'success': True,
            'message': 'Cookie preferences synced successfully',
            'preferences': user.cookie_preferences
        })
        
    except Exception as e:
        logger.error(f"Failed to sync cookie preferences: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# GET USER'S COOKIE PREFERENCES
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cookie_preferences(request):
    """
    Get user's saved cookie preferences from database
    Used to sync localStorage when user logs in from new device
    
    GET /api/cookie-consent/preferences/
    """
    try:
        user = request.user
        
        if not user.cookie_consent_given:
            return Response({
                'has_consent': False,
                'message': 'No cookie preferences saved'
            })
        
        return Response({
            'has_consent': True,
            'preferences': user.cookie_preferences,
            'consent_date': user.cookie_consent_date
        })
        
    except Exception as e:
        logger.error(f"Failed to get cookie preferences: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# ANONYMOUS TRACKING (For Analytics)
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
def track_anonymous_consent(request):
    """
    Track anonymous cookie consent (for analytics/compliance)
    No user account required
    
    POST /api/cookie-consent/track-anonymous/
    Body: {
        "consent_type": "accept_all",
        "analytics": true,
        "marketing": true,
        "preferences": true
    }
    """
    try:
        data = request.data
        
        # Create anonymous consent record
        CookieConsent.objects.create(
            user=None,  # Anonymous
            essential=True,
            analytics=data.get('analytics', False),
            marketing=data.get('marketing', False),
            preferences=data.get('preferences', False),
            consent_type=data.get('consent_type', 'custom'),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            page_url=request.META.get('HTTP_REFERER', ''),
        )
        
        return Response({
            'success': True,
            'message': 'Anonymous consent tracked'
        })
        
    except Exception as e:
        logger.error(f"Failed to track anonymous consent: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# ADMIN: CONSENT ANALYTICS
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consent_analytics(request):
    """
    Get aggregate consent statistics
    For compliance dashboard (admin only)
    
    GET /api/cookie-consent/analytics/
    """
    try:
        # Check if user is admin
        if not request.user.is_staff:
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get consent statistics
        total_consents = CookieConsent.objects.filter(is_active=True).count()
        
        consent_breakdown = CookieConsent.objects.filter(
            is_active=True
        ).values('consent_type').annotate(
            count=Count('id')
        )
        
        analytics_consent = CookieConsent.objects.filter(
            is_active=True,
            analytics=True
        ).count()
        
        marketing_consent = CookieConsent.objects.filter(
            is_active=True,
            marketing=True
        ).count()
        
        preferences_consent = CookieConsent.objects.filter(
            is_active=True,
            preferences=True
        ).count()
        
        # Calculate percentages
        analytics_percentage = (analytics_consent / total_consents * 100) if total_consents > 0 else 0
        marketing_percentage = (marketing_consent / total_consents * 100) if total_consents > 0 else 0
        
        return Response({
            'total_consents': total_consents,
            'consent_breakdown': list(consent_breakdown),
            'analytics': {
                'count': analytics_consent,
                'percentage': round(analytics_percentage, 2)
            },
            'marketing': {
                'count': marketing_consent,
                'percentage': round(marketing_percentage, 2)
            },
            'preferences': {
                'count': preferences_consent,
                'percentage': round((preferences_consent / total_consents * 100) if total_consents > 0 else 0, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get consent analytics: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# ADMIN: CONSENT HISTORY
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_consent_history(request, user_id):
    """
    Get full consent history for a specific user
    For compliance/audit purposes (admin only)
    
    GET /api/cookie-consent/history/<user_id>/
    """
    try:
        # Check if user is admin
        if not request.user.is_staff:
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        consents = CookieConsent.objects.filter(
            user_id=user_id
        ).order_by('-created_at')
        
        history = []
        for consent in consents:
            history.append({
                'id': str(consent.id),
                'consent_type': consent.consent_type,
                'essential': consent.essential,
                'analytics': consent.analytics,
                'marketing': consent.marketing,
                'preferences': consent.preferences,
                'ip_address': consent.ip_address,
                'created_at': consent.created_at,
                'is_active': consent.is_active
            })
        
        return Response({
            'user_id': user_id,
            'consent_history': history
        })
        
    except Exception as e:
        logger.error(f"Failed to get consent history: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip