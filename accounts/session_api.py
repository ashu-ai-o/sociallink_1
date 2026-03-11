"""
Session Tracking API Endpoints
Provides endpoints to view user session data and analytics
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg
from datetime import datetime, timedelta
from django.utils import timezone

from .models import UserSession, PageVisit, UserEvent
from .session_tracker import get_session_stats


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_sessions(request):
    """
    Get current user's browsing sessions

    Query params:
    - limit: Number of sessions (default: 20, max: 100)
    - active_only: Show only active sessions (default: false)

    Returns:
    {
        "success": true,
        "count": 15,
        "sessions": [
            {
                "id": "uuid",
                "ip_address": "192.168.1.1",
                "location": "San Francisco, CA, United States",
                "device": "iPhone 13",
                "platform": "iOS 16.0",
                "browser": "Safari 16.0",
                "created_at": "2024-01-15T10:30:00Z",
                "last_activity": "2024-01-15T12:45:00Z",
                "page_views": 25,
                "is_active": true
            },
            ...
        ]
    }
    """
    try:
        limit = min(int(request.GET.get('limit', 20)), 100)
        active_only = request.GET.get('active_only', 'true').lower() == 'true'
        all_history = request.GET.get('all_history', 'false').lower() == 'true'

        queryset = UserSession.objects.filter(user=request.user)

        if not all_history and active_only:
            queryset = queryset.filter(is_active=True)

        queryset = queryset.order_by('-created_at')[:limit]
        
        # Repair: If no active sessions exist for this user, track the current one
        # This fixes issues where session tracking might have failed during login/signup
        if not queryset.exists():
            from .session_tracker import track_login
            try:
                # We use 'session_repair' method to track this corrective action
                track_login(request, request.user, method='session_repair')
                # Re-fetch the queryset
                queryset = UserSession.objects.filter(user=request.user)
                if not all_history and active_only:
                    queryset = queryset.filter(is_active=True)
                queryset = queryset.order_by('-created_at')[:limit]
            except Exception as e:
                logger.warning(f"Failed to repair missing session: {e}")

        # Get current session info (from IP + user agent)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            current_ip = x_forwarded_for.split(',')[0].strip()
        else:
            current_ip = request.META.get('REMOTE_ADDR', '')
        current_ua = request.META.get('HTTP_USER_AGENT', '')

        sessions = []
        for session in queryset:
            is_current = (
                session.ip_address == current_ip and 
                session.user_agent == current_ua and
                session.is_active
            )

            sessions.append({
                'id': str(session.id),
                'ip_address': session.ip_address,
                'country': session.country,
                'city': session.city,
                'browser_name': session.browser_name,
                'os_name': session.os_name,
                'device_type': session.device_type,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'is_active': session.is_active,
                'is_current': is_current, 
                'is_vpn': session.is_vpn,
                'location': session.get_location_string(),
                'country_code': session.country_code,
                'device': session.get_device_string(),
                'platform': session.get_platform_string(),
                'browser': f"{session.browser_name} {session.browser_version}",
                'is_mobile': session.is_mobile,
                'is_proxy': session.is_proxy,
                'threat_level': session.threat_level,
                'page_views': session.page_views,
                'actions_count': session.actions_count,
                'duration_seconds': session.duration_seconds,
            })

        return Response({
            'success': True,
            'count': len(sessions),
            'sessions': sessions
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_details(request, session_id):
    """
    Get detailed information about a specific session

    Returns:
    {
        "success": true,
        "session": {
            "id": "uuid",
            "ip_address": "192.168.1.1",
            "location": {...},
            "device": {...},
            "browser": {...},
            "page_visits": [...],
            "events": [...],
            ...
        }
    }
    """
    try:
        session = UserSession.objects.get(id=session_id, user=request.user)

        # Get recent page visits
        page_visits = PageVisit.objects.filter(session=session).order_by('-visited_at')[:50]
        page_visits_data = [
            {
                'url': visit.url,
                'path': visit.path,
                'page_title': visit.page_title,
                'time_on_page_seconds': visit.time_on_page_seconds,
                'visited_at': visit.visited_at.isoformat(),
            }
            for visit in page_visits
        ]

        # Get recent events
        events = UserEvent.objects.filter(session=session).order_by('-created_at')[:50]
        events_data = [
            {
                'event_type': event.event_type,
                'event_name': event.event_name,
                'page_url': event.page_url,
                'success': event.success,
                'created_at': event.created_at.isoformat(),
            }
            for event in events
        ]

        session_data = {
            'id': str(session.id),
            'ip_address': session.ip_address,
            'ip_version': session.ip_version,
            'proxy_ip': session.proxy_ip,

            'location': {
                'country': session.country,
                'country_code': session.country_code,
                'region': session.region,
                'city': session.city,
                'postal_code': session.postal_code,
                'latitude': float(session.latitude) if session.latitude else None,
                'longitude': float(session.longitude) if session.longitude else None,
                'timezone': session.timezone,
            },

            'network': {
                'isp': session.isp,
                'organization': session.organization,
                'asn': session.asn,
            },

            'browser': {
                'name': session.browser_name,
                'version': session.browser_version,
                'language': session.browser_language,
            },

            'os': {
                'name': session.os_name,
                'version': session.os_version,
            },

            'device': {
                'type': session.device_type,
                'brand': session.device_brand,
                'model': session.device_model,
                'is_mobile': session.is_mobile,
                'is_tablet': session.is_tablet,
                'is_pc': session.is_pc,
                'is_bot': session.is_bot,
            },

            'screen': {
                'resolution': session.screen_resolution,
                'color_depth': session.color_depth,
                'pixel_ratio': float(session.pixel_ratio) if session.pixel_ratio else None,
            },

            'security': {
                'is_vpn': session.is_vpn,
                'is_proxy': session.is_proxy,
                'is_tor': session.is_tor,
                'is_datacenter': session.is_datacenter,
                'threat_level': session.threat_level,
            },

            'activity': {
                'page_views': session.page_views,
                'actions_count': session.actions_count,
                'duration_seconds': session.duration_seconds,
                'landing_page': session.landing_page,
                'referrer_url': session.referrer_url,
            },

            'utm': {
                'source': session.utm_source,
                'medium': session.utm_medium,
                'campaign': session.utm_campaign,
                'term': session.utm_term,
                'content': session.utm_content,
            },

            'is_active': session.is_active,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'session_ended_at': session.session_ended_at.isoformat() if session.session_ended_at else None,

            'page_visits': page_visits_data,
            'events': events_data,
        }

        return Response({
            'success': True,
            'session': session_data
        })

    except UserSession.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_analytics(request):
    """
    Get comprehensive session analytics for current user

    Returns:
    {
        "success": true,
        "analytics": {
            "total_sessions": 150,
            "active_sessions": 2,
            "total_page_views": 1250,
            "total_actions": 450,
            "avg_session_duration": 320,
            "top_locations": [...],
            "top_devices": [...],
            "top_browsers": [...],
            "device_breakdown": {...},
            "hourly_activity": [...],
        }
    }
    """
    try:
        stats = get_session_stats(request.user)

        # Additional analytics
        sessions = UserSession.objects.filter(user=request.user)

        # Device breakdown
        device_breakdown = {
            'desktop': sessions.filter(device_type='desktop').count(),
            'mobile': sessions.filter(device_type='mobile').count(),
            'tablet': sessions.filter(device_type='tablet').count(),
            'bot': sessions.filter(device_type='bot').count(),
        }

        # OS breakdown
        os_breakdown = sessions.values('os_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Average session duration
        avg_duration = sessions.filter(session_ended_at__isnull=False).aggregate(
            avg=Avg('duration_seconds')
        )['avg'] or 0

        # Recent 7 days activity
        seven_days_ago = timezone.now() - timedelta(days=7)
        daily_activity = []
        for i in range(7):
            day = seven_days_ago + timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0)
            day_end = day.replace(hour=23, minute=59, second=59)

            day_sessions = sessions.filter(
                created_at__gte=day_start,
                created_at__lte=day_end
            ).count()

            daily_activity.append({
                'date': day.date().isoformat(),
                'sessions': day_sessions
            })

        # Security stats
        security_stats = {
            'vpn_sessions': sessions.filter(is_vpn=True).count(),
            'proxy_sessions': sessions.filter(is_proxy=True).count(),
            'tor_sessions': sessions.filter(is_tor=True).count(),
            'high_threat': sessions.filter(threat_level='high').count(),
        }

        return Response({
            'success': True,
            'analytics': {
                **stats,
                'avg_session_duration_seconds': int(avg_duration),
                'device_breakdown': device_breakdown,
                'os_breakdown': list(os_breakdown),
                'daily_activity_7days': daily_activity,
                'security_stats': security_stats,
            }
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_events(request):
    """
    Get user events history

    Query params:
    - limit: Number of events (default: 50, max: 500)
    - event_type: Filter by event type
    - start_date: Filter from date (YYYY-MM-DD)
    - end_date: Filter to date (YYYY-MM-DD)

    Returns list of events with details
    """
    try:
        limit = min(int(request.GET.get('limit', 50)), 500)
        event_type = request.GET.get('event_type')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        queryset = UserEvent.objects.filter(user=request.user)

        if event_type:
            queryset = queryset.filter(event_type=event_type)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            queryset = queryset.filter(created_at__gte=start)

        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            queryset = queryset.filter(created_at__lte=end)

        queryset = queryset.order_by('-created_at')[:limit]

        events = []
        for event in queryset:
            events.append({
                'id': str(event.id),
                'event_type': event.event_type,
                'event_name': event.event_name,
                'event_category': event.event_category,
                'page_url': event.page_url,
                'event_value': event.event_value,
                'event_data': event.event_data,
                'success': event.success,
                'error_message': event.error_message if not event.success else None,
                'created_at': event.created_at.isoformat(),
            })

        return Response({
            'success': True,
            'count': len(events),
            'events': events
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_session(request, session_id):
    """
    Manually end a session (e.g., logout from specific device)
    """
    try:
        session = UserSession.objects.get(id=session_id, user=request.user)

        if not session.is_active:
            return Response({
                'success': False,
                'error': 'Session already ended'
            }, status=status.HTTP_400_BAD_REQUEST)

        from .session_tracker import SessionTracker
        SessionTracker.end_session(session)

        return Response({
            'success': True,
            'message': 'Session ended successfully'
        })

    except UserSession.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_custom_event(request):
    """
    Track a custom event from frontend

    Body:
    {
        "event_name": "Feature X Used",
        "event_category": "features",
        "event_value": "some value",
        "event_data": {
            "key": "value"
        }
    }
    """
    try:
        from .session_tracker import SessionTracker

        event_name = request.data.get('event_name', 'Custom Event')
        event_category = request.data.get('event_category', '')
        event_value = request.data.get('event_value', '')
        event_data = request.data.get('event_data', {})

        event = SessionTracker.track_event(
            request=request,
            event_type='custom',
            event_name=event_name,
            user=request.user,
            event_category=event_category,
            event_value=event_value,
            event_data=event_data,
        )

        return Response({
            'success': True,
            'event_id': str(event.id),
            'message': 'Event tracked successfully'
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
