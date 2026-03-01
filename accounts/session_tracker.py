"""
User Session Tracking Service
Automatically captures and stores user browsing information including:
- IP address and geolocation
- Device, browser, and OS information
- Page visits and user events
- Security flags (VPN, proxy, Tor detection)
"""

import hashlib
import secrets
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils import timezone
from django.db import models
from user_agents import parse as parse_user_agent
import ipaddress

from .models import UserSession, PageVisit, UserEvent


class SessionTracker:
    """
    Main service for tracking user sessions and browsing data
    """

    @staticmethod
    def get_client_ip(request: HttpRequest) -> Tuple[str, str]:
        """
        Extract client IP address from request, handling proxies and load balancers

        Returns:
            Tuple of (ip_address, proxy_ip)
        """
        # Check for common proxy headers
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP (client IP) from the chain
            ip = x_forwarded_for.split(',')[0].strip()
            proxy_ip = request.META.get('REMOTE_ADDR', '')
            return ip, proxy_ip

        # Check for Cloudflare
        cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_connecting_ip:
            return cf_connecting_ip, request.META.get('REMOTE_ADDR', '')

        # Check for other common headers
        for header in ['HTTP_X_REAL_IP', 'HTTP_CLIENT_IP', 'HTTP_X_CLUSTER_CLIENT_IP']:
            ip = request.META.get(header)
            if ip:
                return ip, request.META.get('REMOTE_ADDR', '')

        # Default to REMOTE_ADDR
        return request.META.get('REMOTE_ADDR', ''), ''

    @staticmethod
    def get_ip_version(ip: str) -> str:
        """Determine if IP is IPv4 or IPv6"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return f"IPv{ip_obj.version}"
        except ValueError:
            return 'unknown'

    @staticmethod
    def get_geolocation(ip: str) -> Dict[str, Any]:
        """
        Get geolocation data from IP address using ip-api.com (free, no API key)

        For production, consider:
        - MaxMind GeoIP2 (more accurate, local database)
        - IPinfo.io (paid, reliable)
        - ipstack.com (paid, comprehensive)

        Args:
            ip: IP address to lookup

        Returns:
            Dictionary with location data
        """
        try:
            # Skip private/local IPs
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback:
                return {
                    'country': 'Local',
                    'country_code': 'LOCAL',
                    'region': '',
                    'city': 'Local Network',
                    'postal_code': '',
                    'latitude': None,
                    'longitude': None,
                    'timezone': '',
                    'isp': 'Local Network',
                    'organization': '',
                    'asn': '',
                }

            # Call ip-api.com (free, 45 requests/minute limit)
            response = requests.get(
                f'http://ip-api.com/json/{ip}',
                params={
                    'fields': 'status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,proxy,hosting'
                },
                timeout=3
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'success':
                    return {
                        'country': data.get('country', ''),
                        'country_code': data.get('countryCode', ''),
                        'region': data.get('regionName', ''),
                        'city': data.get('city', ''),
                        'postal_code': data.get('zip', ''),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'timezone': data.get('timezone', ''),
                        'isp': data.get('isp', ''),
                        'organization': data.get('org', ''),
                        'asn': data.get('as', ''),
                        'is_proxy': data.get('proxy', False),
                        'is_datacenter': data.get('hosting', False),
                    }
        except Exception as e:
            print(f"⚠️ Geolocation lookup failed for {ip}: {e}")

        # Return empty data on failure
        return {
            'country': '',
            'country_code': '',
            'region': '',
            'city': '',
            'postal_code': '',
            'latitude': None,
            'longitude': None,
            'timezone': '',
            'isp': '',
            'organization': '',
            'asn': '',
        }

    @staticmethod
    def parse_user_agent(user_agent_string: str) -> Dict[str, Any]:
        """
        Parse user agent string to extract device, browser, and OS information

        Uses user-agents library (install: pip install user-agents)
        """
        ua = parse_user_agent(user_agent_string)

        # Determine device type
        if ua.is_bot:
            device_type = 'bot'
        elif ua.is_mobile:
            device_type = 'mobile'
        elif ua.is_tablet:
            device_type = 'tablet'
        elif ua.is_pc:
            device_type = 'desktop'
        else:
            device_type = 'unknown'

        return {
            # Browser
            'browser_name': ua.browser.family or '',
            'browser_version': ua.browser.version_string or '',

            # OS
            'os_name': ua.os.family or '',
            'os_version': ua.os.version_string or '',

            # Device
            'device_type': device_type,
            'device_brand': ua.device.brand or '',
            'device_model': ua.device.model or '',

            # Flags
            'is_mobile': ua.is_mobile,
            'is_tablet': ua.is_tablet,
            'is_pc': ua.is_pc,
            'is_bot': ua.is_bot,
            'is_touch_capable': ua.is_touch_capable,
        }

    @staticmethod
    def detect_vpn_tor(ip: str) -> Dict[str, Any]:
        """
        Detect if IP is from VPN, Tor, or proxy

        For basic detection, we can use:
        - ip-api.com proxy field
        - Known Tor exit node lists
        - VPN/proxy detection services (paid)

        Returns flags for security analysis
        """
        security_flags = {
            'is_vpn': False,
            'is_proxy': False,
            'is_tor': False,
            'is_datacenter': False,
            'threat_level': 'none',
        }

        try:
            # ip-api includes proxy and hosting detection
            response = requests.get(
                f'http://ip-api.com/json/{ip}',
                params={'fields': 'proxy,hosting'},
                timeout=2
            )

            if response.status_code == 200:
                data = response.json()
                security_flags['is_proxy'] = data.get('proxy', False)
                security_flags['is_datacenter'] = data.get('hosting', False)

                # Heuristic: datacenter IPs are often VPNs
                if data.get('hosting'):
                    security_flags['is_vpn'] = True

                # Set threat level based on flags
                if security_flags['is_tor']:
                    security_flags['threat_level'] = 'high'
                elif security_flags['is_vpn']:
                    security_flags['threat_level'] = 'medium'
                elif security_flags['is_proxy']:
                    security_flags['threat_level'] = 'low'

        except Exception as e:
            print(f"⚠️ Security check failed for {ip}: {e}")

        return security_flags

    @staticmethod
    def extract_utm_params(request: HttpRequest) -> Dict[str, str]:
        """Extract UTM campaign parameters from request"""
        return {
            'utm_source': request.GET.get('utm_source', ''),
            'utm_medium': request.GET.get('utm_medium', ''),
            'utm_campaign': request.GET.get('utm_campaign', ''),
            'utm_term': request.GET.get('utm_term', ''),
            'utm_content': request.GET.get('utm_content', ''),
        }

    @staticmethod
    def generate_session_token() -> str:
        """Generate a unique session token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_user_agent(user_agent: str) -> str:
        """Generate MD5 hash of user agent for quick comparison"""
        return hashlib.md5(user_agent.encode()).hexdigest()

    @staticmethod
    def create_or_update_session(
        request: HttpRequest,
        user: Optional[User] = None,
        login_method: str = ''
    ) -> UserSession:
        """
        Create a new session or update existing one

        Args:
            request: Django HttpRequest object
            user: Authenticated user (optional)
            login_method: How user logged in (e.g., 'password', 'oauth_google')

        Returns:
            UserSession instance
        """
        # Extract basic data
        ip_address, proxy_ip = SessionTracker.get_client_ip(request)
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')

        # Get detailed information
        ip_version = SessionTracker.get_ip_version(ip_address)
        geo_data = SessionTracker.get_geolocation(ip_address)
        ua_data = SessionTracker.parse_user_agent(user_agent_string)
        security_flags = SessionTracker.detect_vpn_tor(ip_address)
        utm_params = SessionTracker.extract_utm_params(request)

        # Check if we have an active session for this user/IP combination
        session = None
        if user:
            # Look for recent session (within last 30 minutes) from same IP
            recent_threshold = timezone.now() - timedelta(minutes=30)
            session = UserSession.objects.filter(
                user=user,
                ip_address=ip_address,
                is_active=True,
                last_activity__gte=recent_threshold
            ).first()

        # Create new session if none found
        if not session:
            session_token = SessionTracker.generate_session_token()
            ua_hash = SessionTracker.hash_user_agent(user_agent_string)

            session = UserSession.objects.create(
                user=user,
                session_key=request.session.session_key or '',
                session_token=session_token,

                # IP and Network
                ip_address=ip_address,
                ip_version=ip_version,
                proxy_ip=proxy_ip or None,

                # Geolocation
                country=geo_data.get('country', ''),
                country_code=geo_data.get('country_code', ''),
                region=geo_data.get('region', ''),
                city=geo_data.get('city', ''),
                postal_code=geo_data.get('postal_code', ''),
                latitude=geo_data.get('latitude'),
                longitude=geo_data.get('longitude'),
                timezone=geo_data.get('timezone', ''),

                # ISP
                isp=geo_data.get('isp', ''),
                organization=geo_data.get('organization', ''),
                asn=geo_data.get('asn', ''),

                # Browser
                browser_name=ua_data['browser_name'],
                browser_version=ua_data['browser_version'],
                browser_language=request.META.get('HTTP_ACCEPT_LANGUAGE', '')[:20],

                # OS
                os_name=ua_data['os_name'],
                os_version=ua_data['os_version'],

                # Device
                device_type=ua_data['device_type'],
                device_brand=ua_data['device_brand'],
                device_model=ua_data['device_model'],
                is_mobile=ua_data['is_mobile'],
                is_tablet=ua_data['is_tablet'],
                is_touch_capable=ua_data['is_touch_capable'],
                is_pc=ua_data['is_pc'],
                is_bot=ua_data['is_bot'],

                # User Agent
                user_agent=user_agent_string,
                user_agent_hash=ua_hash,

                # Referrer
                referrer_url=referrer,
                referrer_domain=SessionTracker._extract_domain(referrer),
                landing_page=request.path,

                # UTM params
                **utm_params,

                # Security
                is_vpn=security_flags['is_vpn'],
                is_proxy=security_flags['is_proxy'],
                is_tor=security_flags['is_tor'],
                is_datacenter=security_flags['is_datacenter'],
                threat_level=security_flags['threat_level'],

                # Session info
                login_method=login_method,
                is_active=True,
            )

            print(f"✅ Created new session {session.id} for {user.username if user else 'Anonymous'} from {ip_address}")
        else:
            # Update existing session
            session.page_views += 1
            session.last_activity = timezone.now()
            session.save()

            print(f"🔄 Updated session {session.id} for {user.username}")

        return session

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ''
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except Exception:
            return ''

    @staticmethod
    def track_page_visit(
        session: UserSession,
        request: HttpRequest,
        page_title: str = ''
    ) -> PageVisit:
        """
        Track a page visit

        Args:
            session: UserSession instance
            request: Django HttpRequest
            page_title: Page title (optional)

        Returns:
            PageVisit instance
        """
        referrer = request.META.get('HTTP_REFERER', '')
        is_internal = SessionTracker._extract_domain(referrer) == request.get_host()

        visit = PageVisit.objects.create(
            session=session,
            user=session.user,
            url=request.build_absolute_uri(),
            path=request.path,
            query_string=request.META.get('QUERY_STRING', ''),
            page_title=page_title,
            http_method=request.method,
            referrer=referrer,
            is_internal_referrer=is_internal,
        )

        # Update session page view count
        session.page_views += 1
        session.save()

        return visit

    @staticmethod
    def track_event(
        request: HttpRequest,
        event_type: str,
        event_name: str,
        user: Optional[User] = None,
        event_category: str = '',
        event_value: str = '',
        event_data: Optional[Dict] = None,
        success: bool = True,
        error_message: str = ''
    ) -> UserEvent:
        """
        Track a user event

        Args:
            request: Django HttpRequest
            event_type: Type of event (see UserEvent.event_type choices)
            event_name: Name/description of event
            user: User who triggered event (optional)
            event_category: Event category (optional)
            event_value: Event value (optional)
            event_data: Additional event data as dict (optional)
            success: Whether event was successful
            error_message: Error message if failed

        Returns:
            UserEvent instance
        """
        # Try to find active session
        session = None
        if user:
            session = UserSession.objects.filter(
                user=user,
                is_active=True
            ).order_by('-last_activity').first()

        event = UserEvent.objects.create(
            session=session,
            user=user,
            event_type=event_type,
            event_name=event_name,
            event_category=event_category,
            page_url=request.build_absolute_uri(),
            event_value=event_value,
            event_data=event_data or {},
            success=success,
            error_message=error_message,
        )

        # Update session actions count
        if session:
            session.actions_count += 1
            session.save()

        return event

    @staticmethod
    def end_session(session: UserSession):
        """Mark session as ended"""
        session.is_active = False
        session.session_ended_at = timezone.now()
        session.duration_seconds = int(
            (session.session_ended_at - session.created_at).total_seconds()
        )
        session.save()

        print(f"🛑 Ended session {session.id} (duration: {session.duration_seconds}s)")


# Convenience functions for common operations

def track_login(request: HttpRequest, user: User, method: str = 'password') -> UserSession:
    """Track user login and create session"""
    session = SessionTracker.create_or_update_session(request, user, login_method=method)

    # Track login event
    SessionTracker.track_event(
        request=request,
        event_type='login',
        event_name=f'User logged in via {method}',
        user=user,
        event_category='authentication',
        event_value=method,
    )

    return session


def track_logout(request: HttpRequest, user: User):
    """Track user logout and end session"""
    # Find active session
    session = UserSession.objects.filter(
        user=user,
        is_active=True
    ).order_by('-last_activity').first()

    if session:
        SessionTracker.end_session(session)

        # Track logout event
        SessionTracker.track_event(
            request=request,
            event_type='logout',
            event_name='User logged out',
            user=user,
            event_category='authentication',
        )


def track_signup(request: HttpRequest, user: User, method: str = 'email'):
    """Track new user signup"""
    session = SessionTracker.create_or_update_session(request, user, login_method=method)

    SessionTracker.track_event(
        request=request,
        event_type='signup',
        event_name=f'New user signed up via {method}',
        user=user,
        event_category='authentication',
        event_value=method,
    )

    return session


def get_session_stats(user: User) -> Dict[str, Any]:
    """
    Get session statistics for a user

    Returns comprehensive analytics about user's sessions
    """
    sessions = UserSession.objects.filter(user=user)

    total_sessions = sessions.count()
    active_sessions = sessions.filter(is_active=True).count()
    total_page_views = sum(s.page_views for s in sessions)
    total_actions = sum(s.actions_count for s in sessions)

    # Get most common locations
    locations = sessions.values('city', 'country').annotate(
        count=models.Count('id')
    ).order_by('-count')[:5]

    # Get most common devices
    devices = sessions.values('device_type', 'os_name').annotate(
        count=models.Count('id')
    ).order_by('-count')[:5]

    # Get most common browsers
    browsers = sessions.values('browser_name').annotate(
        count=models.Count('id')
    ).order_by('-count')[:5]

    return {
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'total_page_views': total_page_views,
        'total_actions': total_actions,
        'top_locations': list(locations),
        'top_devices': list(devices),
        'top_browsers': list(browsers),
    }