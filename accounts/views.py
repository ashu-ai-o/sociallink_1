from django.shortcuts import render

# Create your views here.
"""
Authentication and User Management Views
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .models import User, InstagramAccount
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    PasswordChangeSerializer,
    InstagramAccountSerializer,
    InstagramAccountConnectSerializer,
    UserProfileSerializer
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import redirect
from django.conf import settings
import requests
from datetime import datetime, timedelta
from .models import InstagramAccount
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    """
    User login endpoint
    POST /api/auth/login/
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Login successful'
        })


class UserLogoutView(generics.GenericAPIView):
    """
    User logout endpoint
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(generics.GenericAPIView):
    """
    Change user password
    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update user profile
    GET /api/auth/profile/
    PATCH /api/auth/profile/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'user': serializer.data,
            'message': 'Profile updated successfully'
        })


class UserViewSet(viewsets.ModelViewSet):
    """
    User management viewset (admin only)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own data unless they're staff"""
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user
        GET /api/users/me/
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    

    @action(detail=False, methods=['get', 'patch'])
    def email_preferences(self, request):
        '''
        Get or update email preferences
        GET /api/users/email_preferences/
        PATCH /api/users/email_preferences/
        '''
        user = request.user
        
        if request.method == 'GET':
            # Return current preferences with defaults
            default_prefs = {
                'weekly_reports': True,
                'automation_alerts': True,
                'dm_failures': True,
                'account_issues': True
            }
            prefs = {**default_prefs, **user.email_preferences}
            return Response(prefs)
        
        elif request.method == 'PATCH':
            # Update preferences
            user.email_preferences = {
                **user.email_preferences,
                **request.data
            }
            user.save()
            return Response(user.email_preferences)
    























@api_view(['GET'])
@permission_classes([IsAuthenticated])
def instagram_oauth_initiate(request):
    """
    Step 1: Redirect user to Facebook OAuth for Instagram permissions
    
    GET /api/auth/instagram/oauth/
    
    This opens Instagram OAuth popup with required permissions
    """
    
    # Facebook App credentials (add to settings.py)
    facebook_app_id = settings.FACEBOOK_APP_ID
    redirect_uri = f"{settings.FRONTEND_URL}/auth/instagram/callback"
    
    # Required Instagram permissions
    scope = ",".join([
        "instagram_basic",  # Basic profile info
        "instagram_manage_messages",  # Send/receive DMs
        "instagram_manage_comments",  # Reply to comments
        "pages_show_list",  # List Facebook pages
        "pages_read_engagement",  # Read page data
    ])
    
    # Store user ID in state for security
    state = f"user_{request.user.id}"
    
    # Build OAuth URL
    oauth_url = (
        f"https://www.facebook.com/v21.0/dialog/oauth?"
        f"client_id={facebook_app_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=code"
        f"&state={state}"
    )
    
    logger.info(f"Initiating Instagram OAuth for user {request.user.id}")
    
    return redirect(oauth_url)


@api_view(['GET'])
def instagram_oauth_callback(request):
    """
    Step 2: Handle OAuth callback from Facebook
    
    GET /api/auth/instagram/callback?code=...&state=...
    
    This exchanges the code for access token and saves Instagram account
    """
    
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    # Handle errors
    if error:
        error_description = request.GET.get('error_description', 'Unknown error')
        logger.error(f"OAuth error: {error} - {error_description}")
        return redirect(f"{settings.FRONTEND_URL}/dashboard?error=oauth_failed")
    
    if not code:
        logger.error("No code received from OAuth")
        return redirect(f"{settings.FRONTEND_URL}/dashboard?error=no_code")
    
    # Verify state (extract user_id)
    try:
        user_id = state.split('_')[1]
        user = User.objects.get(id=user_id)
    except (IndexError, User.DoesNotExist):
        logger.error(f"Invalid state: {state}")
        return redirect(f"{settings.FRONTEND_URL}/dashboard?error=invalid_state")
    
    # Exchange code for access token
    try:
        token_data = exchange_code_for_token(code)
        
        if not token_data:
            raise Exception("Failed to exchange code for token")
        
        # Get Instagram account info
        instagram_data = get_instagram_account_info(token_data['access_token'])
        
        if not instagram_data:
            raise Exception("Failed to fetch Instagram account info")
        
        # Save to database
        instagram_account = save_instagram_account(
            user=user,
            access_token=token_data['access_token'],
            expires_in=token_data.get('expires_in', 5183944),  # ~60 days default
            instagram_data=instagram_data
        )
        
        logger.info(f"Successfully connected Instagram account @{instagram_account.username} for user {user.id}")
        
        return redirect(f"{settings.FRONTEND_URL}/dashboard?instagram_connected=true")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return redirect(f"{settings.FRONTEND_URL}/dashboard?error=connection_failed")


def exchange_code_for_token(code):
    """
    Exchange authorization code for access token
    """
    redirect_uri = f"{settings.FRONTEND_URL}/auth/instagram/callback"
    
    url = "https://graph.facebook.com/v21.0/oauth/access_token"
    params = {
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'redirect_uri': redirect_uri,
        'code': code
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Exchange for long-lived token (60 days)
        long_lived_token = exchange_for_long_lived_token(data['access_token'])
        
        return {
            'access_token': long_lived_token or data['access_token'],
            'expires_in': 5183944  # 60 days in seconds
        }
        
    except Exception as e:
        logger.error(f"Token exchange error: {str(e)}")
        return None


def exchange_for_long_lived_token(short_lived_token):
    """
    Exchange short-lived token (1 hour) for long-lived token (60 days)
    """
    url = "https://graph.facebook.com/v21.0/oauth/access_token"
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'fb_exchange_token': short_lived_token
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('access_token')
    except Exception as e:
        logger.error(f"Long-lived token exchange error: {str(e)}")
        return None


def get_instagram_account_info(access_token):
    """
    Fetch Instagram account information using access token
    """
    # First, get connected Facebook pages
    url = "https://graph.facebook.com/v21.0/me/accounts"
    params = {
        'access_token': access_token,
        'fields': 'id,name,access_token'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        pages = response.json().get('data', [])
        
        if not pages:
            logger.error("No Facebook pages found")
            return None
        
        # Get Instagram account connected to first page
        page = pages[0]
        page_id = page['id']
        page_access_token = page['access_token']
        
        # Get Instagram Business Account
        ig_url = f"https://graph.facebook.com/v21.0/{page_id}"
        ig_params = {
            'access_token': page_access_token,
            'fields': 'instagram_business_account'
        }
        
        ig_response = requests.get(ig_url, params=ig_params, timeout=10)
        ig_response.raise_for_status()
        ig_business_account = ig_response.json().get('instagram_business_account')
        
        if not ig_business_account:
            logger.error("No Instagram Business Account found")
            return None
        
        instagram_user_id = ig_business_account['id']
        
        # Get Instagram account details
        details_url = f"https://graph.facebook.com/v21.0/{instagram_user_id}"
        details_params = {
            'access_token': page_access_token,
            'fields': 'id,username,profile_picture_url,followers_count'
        }
        
        details_response = requests.get(details_url, params=details_params, timeout=10)
        details_response.raise_for_status()
        instagram_details = details_response.json()
        
        return {
            'instagram_user_id': instagram_user_id,
            'username': instagram_details.get('username'),
            'profile_picture_url': instagram_details.get('profile_picture_url', ''),
            'followers_count': instagram_details.get('followers_count', 0),
            'page_id': page_id,
            'page_access_token': page_access_token
        }
        
    except Exception as e:
        logger.error(f"Instagram info fetch error: {str(e)}")
        return None


def save_instagram_account(user, access_token, expires_in, instagram_data):
    """
    Save or update Instagram account in database
    """
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    instagram_account, created = InstagramAccount.objects.update_or_create(
        instagram_user_id=instagram_data['instagram_user_id'],
        defaults={
            'user': user,
            'username': instagram_data['username'],
            'access_token': access_token,  # Store the long-lived token
            'token_expires_at': expires_at,
            'page_id': instagram_data['page_id'],
            'profile_picture_url': instagram_data.get('profile_picture_url', ''),
            'followers_count': instagram_data.get('followers_count', 0),
            'is_active': True
        }
    )
    
    if created:
        logger.info(f"Created new Instagram account: @{instagram_account.username}")
    else:
        logger.info(f"Updated existing Instagram account: @{instagram_account.username}")
    
    return instagram_account


# ============================================================================
# DISCONNECT ENDPOINT
# ============================================================================

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def disconnect_instagram_account(request, account_id):
    """
    Disconnect (deactivate) an Instagram account
    
    DELETE /api/instagram-accounts/{id}/disconnect/
    """
    try:
        account = InstagramAccount.objects.get(
            id=account_id,
            user=request.user
        )
        
        account.is_active = False
        account.save()
        
        logger.info(f"Disconnected Instagram account @{account.username} for user {request.user.id}")
        
        return Response({
            'message': 'Instagram account disconnected successfully'
        })
        
    except InstagramAccount.DoesNotExist:
        return Response(
            {'error': 'Instagram account not found'},
            status=404
        )


# ============================================================================
# REFRESH STATS ENDPOINT
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_instagram_stats(request, account_id):
    """
    Refresh Instagram account statistics
    
    POST /api/instagram-accounts/{id}/refresh_stats/
    """
    try:
        account = InstagramAccount.objects.get(
            id=account_id,
            user=request.user
        )
        
        # Fetch latest stats
        url = f"https://graph.facebook.com/v21.0/{account.instagram_user_id}"
        params = {
            'access_token': account.access_token,
            'fields': 'followers_count,profile_picture_url'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Update account
        account.followers_count = data.get('followers_count', account.followers_count)
        account.profile_picture_url = data.get('profile_picture_url', account.profile_picture_url)
        account.save()
        
        logger.info(f"Refreshed stats for @{account.username}")
        
        return Response({
            'message': 'Stats refreshed successfully',
            'followers_count': account.followers_count
        })
        
    except InstagramAccount.DoesNotExist:
        return Response({'error': 'Account not found'}, status=404)
    except Exception as e:
        logger.error(f"Stats refresh error: {str(e)}")
        return Response({'error': 'Failed to refresh stats'}, status=500)












class InstagramAccountViewSet(viewsets.ModelViewSet):
    """
    Instagram Account management
    """
    serializer_class = InstagramAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by current user"""
        return InstagramAccount.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        Connect new Instagram account
        POST /api/instagram-accounts/
        """
        serializer = InstagramAccountConnectSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        instagram_account = serializer.save()
        
        return Response({
            'instagram_account': InstagramAccountSerializer(instagram_account).data,
            'message': 'Instagram account connected successfully'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """
        Disconnect Instagram account
        POST /api/instagram-accounts/{id}/disconnect/
        """
        instagram_account = self.get_object()
        instagram_account.is_active = False
        instagram_account.save()
        
        return Response({
            'message': 'Instagram account disconnected'
        })
    
    @action(detail=True, methods=['post'])
    def reconnect(self, request, pk=None):
        """
        Reconnect Instagram account
        POST /api/instagram-accounts/{id}/reconnect/
        """
        instagram_account = self.get_object()
        
        # Update tokens
        access_token = request.data.get('access_token')
        token_expires_at = request.data.get('token_expires_at')
        
        if access_token and token_expires_at:
            instagram_account.access_token = access_token
            instagram_account.token_expires_at = token_expires_at
            instagram_account.is_active = True
            instagram_account.save()
            
            return Response({
                'instagram_account': InstagramAccountSerializer(instagram_account).data,
                'message': 'Instagram account reconnected'
            })
        else:
            return Response({
                'error': 'access_token and token_expires_at are required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def refresh_stats(self, request, pk=None):
        """
        Refresh Instagram account stats
        POST /api/instagram-accounts/{id}/refresh_stats/
        """
        instagram_account = self.get_object()
        
        # TODO: Call Instagram API to refresh stats
        # For now, just return current data
        
        return Response({
            'instagram_account': InstagramAccountSerializer(instagram_account).data,
            'message': 'Stats refresh initiated'
        })
    
    @action(detail=False, methods=['get'])
    def check_token_expiry(self, request):
        """
        Check which accounts have expiring tokens
        GET /api/instagram-accounts/check_token_expiry/
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Accounts expiring in next 7 days
        expiring_soon = self.get_queryset().filter(
            token_expires_at__lte=timezone.now() + timedelta(days=7),
            token_expires_at__gte=timezone.now(),
            is_active=True
        )
        
        return Response({
            'expiring_soon': InstagramAccountSerializer(expiring_soon, many=True).data,
            'count': expiring_soon.count()
        })
    













