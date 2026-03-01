"""
Session Tracking Middleware
Automatically tracks user sessions and page visits for all requests
"""

from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .session_tracker import SessionTracker


class SessionTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track user sessions and page visits
    """

    # Paths to exclude from tracking
    EXCLUDE_PATHS = [
        '/admin/',
        '/static/',
        '/media/',
        '/__debug__/',
        '/favicon.ico',
        '/robots.txt',
        '/sitemap.xml',
    ]

    # Paths to exclude from detailed page visit tracking (but still track session)
    EXCLUDE_PAGE_TRACKING = [
        '/api/tokens/',  # High-frequency API calls
        '/api/health/',
        '/api/ping/',
    ]

    def process_request(self, request):
        """
        Track session and page visit for each request
        """
        # Skip excluded paths
        for excluded_path in self.EXCLUDE_PATHS:
            if request.path.startswith(excluded_path):
                return None

        # Get or create session for authenticated users
        if request.user and not isinstance(request.user, AnonymousUser):
            try:
                # Create or update session
                session = SessionTracker.create_or_update_session(
                    request=request,
                    user=request.user
                )

                # Attach session to request for use in views
                request.user_session = session

                # Track page visit for non-API requests
                should_track_page = True
                for excluded_path in self.EXCLUDE_PAGE_TRACKING:
                    if request.path.startswith(excluded_path):
                        should_track_page = False
                        break

                if should_track_page and request.method == 'GET':
                    SessionTracker.track_page_visit(
                        session=session,
                        request=request,
                        page_title=''  # Can be set from frontend via header
                    )

            except Exception as e:
                # Don't let tracking errors break the application
                print(f"⚠️ Session tracking error: {e}")

        return None


class SecurityTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to detect and log suspicious activity
    Can be used to automatically block or rate-limit suspicious IPs
    """

    # Threshold for high threat level
    THREAT_THRESHOLD = {
        'high': 'block',      # Block immediately
        'medium': 'monitor',  # Monitor closely
        'low': 'allow',       # Allow but log
    }

    def process_request(self, request):
        """
        Check for security threats and take action
        """
        # Only check for authenticated users
        if not request.user or isinstance(request.user, AnonymousUser):
            return None

        try:
            # Check if user has active session with high threat level
            from .models import UserSession

            recent_session = UserSession.objects.filter(
                user=request.user,
                is_active=True,
                threat_level='high'
            ).first()

            if recent_session:
                # Log suspicious activity
                print(f"⚠️ HIGH THREAT: User {request.user.username} from {recent_session.ip_address}")
                print(f"   VPN: {recent_session.is_vpn}, Proxy: {recent_session.is_proxy}, Tor: {recent_session.is_tor}")

                # In production, you might want to:
                # - Send alert to admins
                # - Require additional authentication
                # - Rate limit the user
                # - Block the request
                #
                # from django.http import HttpResponseForbidden
                # return HttpResponseForbidden("Suspicious activity detected")

        except Exception as e:
            print(f"⚠️ Security check error: {e}")

        return None