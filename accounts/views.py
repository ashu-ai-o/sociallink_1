# Create your views here.
"""
Authentication and User Management Views
"""

from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import User, InstagramAccount, UserSession
from .two_factor_utils import TwoFactorAuth, setup_2fa_for_user, disable_2fa_for_user
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    InstagramAccountSerializer,
    InstagramAccountConnectSerializer,
    UserProfileSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySetupSerializer,
    TwoFactorVerifyLoginSerializer,
    TwoFactorDisableSerializer,
    TwoFactorRegenerateBackupCodesSerializer
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import redirect
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone
import requests
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode
from .models import InstagramAccount, EmailVerificationToken
from .utils import send_verification_email
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


# class UserRegistrationView(generics.CreateAPIView):
#     """
#     User registration endpoint
#     POST /api/auth/register/
#     """ 
#     queryset = User.objects.all()
#     permission_classes = [AllowAny]
#     serializer_class = UserRegistrationSerializer
    
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()
        
#         # Generate JWT tokens
#         refresh = RefreshToken.for_user(user)
        
#         return Response({
#             'user': UserSerializer(user).data,
#             'tokens': {
#                 'refresh': str(refresh),
#                 'access': str(refresh.access_token),
#             },
#             'message': 'User registered successfully'
#         }, status=status.HTTP_201_CREATED)


# class UserLoginView(generics.GenericAPIView):
#     """
#     User login endpoint
#     POST /api/auth/login/
#     """
#     permission_classes = [AllowAny]
#     serializer_class = UserLoginSerializer
    
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         user = serializer.validated_data['user']
        
#         # Generate JWT tokens
#         refresh = RefreshToken.for_user(user)
        
#         return Response({
#             'user': UserSerializer(user).data,
#             'tokens': {
#                 'refresh': str(refresh),
#                 'access': str(refresh.access_token),
#             },
#             'message': 'Login successful'
#         })


# class UserLogoutView(generics.GenericAPIView):
#     """
#     User logout endpoint
#     POST /api/auth/logout/
#     """
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         try:
#             refresh_token = request.data.get('refresh_token')
#             if refresh_token:
#                 token = RefreshToken(refresh_token)
#                 token.blacklist()
            
#             return Response({
#                 'message': 'Logout successful'
#             }, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)


# class PasswordChangeView(generics.GenericAPIView):
#     """
#     Change user password
#     POST /api/auth/change-password/
#     """
#     permission_classes = [IsAuthenticated]
#     serializer_class = PasswordChangeSerializer
    
#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
        
#         return Response({
#             'message': 'Password changed successfully'
#         }, status=status.HTTP_200_OK)


# class UserProfileView(generics.RetrieveUpdateAPIView):
#     """
#     Get and update user profile
#     GET /api/auth/profile/
#     PATCH /api/auth/profile/
#     """
#     permission_classes = [IsAuthenticated]
#     serializer_class = UserProfileSerializer

#     def get_object(self):
#         return self.request.user

#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         return Response(serializer.data)

#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)

#         return Response({
#             'user': serializer.data,
#             'message': 'Profile updated successfully'
#         })


# class CompleteOnboardingView(generics.GenericAPIView):
#     """
#     Mark user onboarding as completed
#     POST /api/auth/complete-onboarding/
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = request.user
#         user.onboarding_completed = True
#         user.save(update_fields=['onboarding_completed'])

#         return Response({
#             'message': 'Onboarding completed successfully',
#             'onboarding_completed': True
#         }, status=status.HTTP_200_OK)


# class UserViewSet(viewsets.ModelViewSet):
#     """
#     User management viewset (admin only)
#     """
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         """Users can only see their own data unless they're staff"""
#         if self.request.user.is_staff:
#             return User.objects.all()
#         return User.objects.filter(id=self.request.user.id)
    
#     @action(detail=False, methods=['get'])
#     def me(self, request):
#         """
#         Get current user
#         GET /api/users/me/
#         """
#         serializer = UserProfileSerializer(request.user)
#         return Response(serializer.data)
    

#     @action(detail=False, methods=['get', 'patch'])
#     def email_preferences(self, request):
#         '''
#         Get or update email preferences
#         GET /api/users/email_preferences/
#         PATCH /api/users/email_preferences/
#         '''
#         user = request.user
        
#         if request.method == 'GET':
#             # Return current preferences with defaults
#             default_prefs = {
#                 'weekly_reports': True,
#                 'automation_alerts': True,
#                 'dm_failures': True,
#                 'account_issues': True
#             }
#             prefs = {**default_prefs, **user.email_preferences}
#             return Response(prefs)
        
#         elif request.method == 'PATCH':
#             # Update preferences
#             user.email_preferences = {
#                 **user.email_preferences,
#                 **request.data
#             }
#             user.save()
#             return Response(user.email_preferences)
    







class UserSearchView(APIView):
    """
    Search users by email or username (for adding collaborators)
    GET /api/users/search/?q=search_term
    Returns: [{id, username, email, first_name, last_name}]
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'results': [], 'error': 'Query required'}, status=400)

        users = User.objects.filter(
            Q(email__icontains=query) | Q(username__icontains=query)
        ).exclude(id=request.user.id)[:10]

        results = [
            {
                'id': str(u.id),
                'username': u.username,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name
            }
            for u in users
        ]
        return Response({'results': results})
    
class EmailPreferencesView(APIView):
    """
    Manage user email preferences
    GET /api/auth/email-preferences/
    PUT /api/auth/email-preferences/
    """
    permission_classes = [IsAuthenticated]

    DEFAULTS = {
        'payment_receipt': True,
        'payment_failure': True,
        'subscription_reminder': True,
        'marketing': False,
        'product_updates': True,
    }
    
    def get(self, request):
        """Get current email preferences"""
        user = request.user
        
        preferences = self.DEFAULTS.copy()
        if user.email_preferences:
            preferences.update(user.email_preferences)
        
        return Response({
            'success': True,
            'preferences': preferences,
            'marketing_opt_in': user.marketing_opt_in
        })
    
    def put(self, request):
        """Update email preferences"""
        user = request.user
        
        preferences = request.data.get('preferences', {})
        marketing_opt_in = request.data.get('marketing_opt_in')
        
        if preferences:
            # Critical emails cannot be disabled
            preferences['payment_receipt'] = True
            preferences['payment_failure'] = True
            
            if not isinstance(user.email_preferences, dict):
                user.email_preferences = {}
            user.email_preferences.update(preferences)
        
        if marketing_opt_in is not None:
            user.marketing_opt_in = marketing_opt_in
        
        user.save(update_fields=['email_preferences', 'marketing_opt_in', 'updated_at'])
        
        return Response({
            'success': True,
            'message': 'Email preferences updated successfully',
            'preferences': user.email_preferences,
            'marketing_opt_in': user.marketing_opt_in
        })
    
    def post(self, request):
        """Opt out of all non-critical emails"""
        user = request.user
        user.opt_out_all_emails()
        
        return Response({
            'success': True,
            'message': 'Opted out of all non-critical emails',
            'preferences': user.email_preferences
        })


class EmailHistoryView(APIView):
    """
    View email history
    GET /api/users/email-history/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's email history"""
        email_logs = EmailLog.objects.filter(
            user=request.user
        ).order_by('-created_at')[:50]
        
        history = []
        for log in email_logs:
            history.append({
                'id': str(log.id),
                'email_type': log.email_type,
                'subject': log.subject,
                'recipient': log.recipient,
                'status': log.status,
                'sent_at': log.sent_at.isoformat() if log.sent_at else None,
                'opened': log.open_rate,
                'clicked': log.click_rate,
                'payment_id': str(log.payment.id) if log.payment else None,
            })
        
        return Response({
            'success': True,
            'emails': history,
            'total': len(history)
        })


class EmailTrackingView(APIView):
    """
    Track email opens and clicks
    GET /api/track/email/<email_id>/open/
    GET /api/track/email/<email_id>/click/
    """
    permission_classes = []  # Public endpoint
    
    def get(self, request, email_id, action):
        """Track email interaction"""
        try:
            email_log = EmailLog.objects.get(id=email_id)
            
            if action == 'open':
                email_log.mark_as_opened()
            elif action == 'click':
                email_log.mark_as_clicked()
            
            # Return 1x1 transparent pixel for open tracking
            if action == 'open':
                from django.http import HttpResponse
                pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
                return HttpResponse(pixel, content_type='image/gif')
            else:
                # Redirect to destination for click tracking
                destination = request.GET.get('url', '/')
                from django.shortcuts import redirect
                return redirect(destination)
                
        except EmailLog.DoesNotExist:
            from django.http import HttpResponse
            return HttpResponse(status=404)

class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint
    POST /api/auth/register/
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create email verification token
        token = secrets.token_urlsafe(32)
        verification_token = EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Send verification email (fail gracefully if SMTP not configured)
        try:
            send_verification_email(user, token)
        except Exception as e:
            logger.warning(f"Failed to send verification email to {user.email}: {e}")

        # Track signup session
        session_id = None
        try:
            session = track_signup(request, user, method='email')
            session_id = str(session.id)
        except Exception as e:
            logger.warning(f"Failed to track signup session: {e}")

        #   DON'T RETURN TOKENS
        return Response({
            'success': True,
            'message': 'Registration successful! Please check your email to verify your account.',
            'email': user.email,
            'session_id': session_id,
            'requires_verification': True
        }, status=status.HTTP_201_CREATED)


class CheckUsernameView(APIView):
    """
    Check if a username is available
    GET /api/auth/check-username/?username=...
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        username = request.query_params.get('username')
        
        if not username:
             return Response({'error': 'Username parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user with this username already exists
        is_taken = User.objects.filter(username__iexact=username).exists()
        
        return Response({
            'available': not is_taken,
            'username': username
        }, status=status.HTTP_200_OK)


from .session_tracker import track_login, track_signup
class LoginView(APIView):
    """
    User login endpoint
    POST /api/auth/login/
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        from .models import UserSession
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        session_id = None
        try:
            session = track_login(request, user, method='password')
            session_id = str(session.id)
        except Exception as e:
            logger.warning(f"Failed to track login session: {e}")

        if not user.is_email_verified and not user.is_superuser:
            return Response({
                'success': False,
                'error': 'Please verify your email before logging in.',
                'email': user.email,
                'requires_verification': True
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if 2FA is enabled
        if user.two_factor_enabled:
            return Response({
                'success': True,
                'message': 'Password verified. 2FA required.',
                'requires_2fa': True,
                'user_id': user.id,
                'email': user.email
            })

        # We now simply rely on onboarding_completed
        is_new_user = not user.onboarding_completed

        user.update_last_login()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        if session_id:
            try:
                session = UserSession.objects.get(id=session_id)
                session.refresh_jti = refresh.get('jti')
                session.save(update_fields=['refresh_jti'])
            except UserSession.DoesNotExist:
                pass

        return Response({
            'success': True,
            'message': 'Login successful',
            'user': UserProfileSerializer(user).data,
            'is_new_user': is_new_user,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'session_id': session_id

        })




class CompleteOnboardingView(APIView):
    """
    Mark user onboarding as completed
    POST /api/auth/complete-onboarding/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.onboarding_completed = True
        user.save(update_fields=['onboarding_completed'])

        return Response({
            'success': True,
            'message': 'Onboarding completed successfully',
            'onboarding_completed': True
        }, status=status.HTTP_200_OK)


class OnboardingStepView(APIView):
    """
    Save the current user onboarding step
    POST /api/auth/onboarding-step/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        step = request.data.get('step', 0)
        
        try:
            step = int(step)
            user.onboarding_step = step
            user.save(update_fields=['onboarding_step'])
            return Response({
                'success': True,
                'message': 'Onboarding step saved',
                'onboarding_step': step
            }, status=status.HTTP_200_OK)
        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid step value'
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Enhanced logout - blacklists token AND deactivates session
    POST /api/auth/logout/
    
    Body:
    {
        "refresh_token": "your_refresh_token"
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            
            if not refresh_token:
                # No refresh token provided, but still return success
                # User is logged out on frontend regardless
                return Response({
                    'success': True,
                    'message': 'Logout successful (no token to blacklist)'
                }, status=status.HTTP_200_OK)
            

            try:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()
                
                # Deactivate the corresponding session
                current_ip, _ = self._get_client_ip(request)
                current_ua = request.META.get('HTTP_USER_AGENT', '')
                
                UserSession.objects.filter(
                    user=request.user,
                    ip_address=current_ip,
                    user_agent=current_ua,
                    is_active=True
                ).update(
                    is_active=False,
                    session_ended_at=timezone.now()
                )
            
                return Response({
                    'success': True,
                    'message': 'Logout successful'
                }, status=status.HTTP_200_OK)
            

            except Exception as e:
                # Token already blacklisted or invalid
                # Still return success because user is logging out
                return Response({
                    'success': True,
                    'message': 'Logout successful (token already invalid)'
                }, status=status.HTTP_200_OK)

            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update user profile
    GET/PUT/PATCH /api/auth/profile/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user







class RequestPasswordChangeOTPView(APIView):
    """
    Request OTP for password change
    POST /api/auth/request-password-change-otp/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        import random
        from .models import PasswordChangeOTP
        from .utils import send_password_change_otp

        user = request.user

        # Generate 6-digit OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # Invalidate old OTPs
        PasswordChangeOTP.objects.filter(user=user, is_used=False).update(is_used=True)

        # Create new OTP with 10 minute expiry
        otp = PasswordChangeOTP.objects.create(
            user=user,
            otp_code=otp_code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Send email with OTP
        try:
            send_password_change_otp(user, otp_code)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to send OTP email: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': True,
            'message': 'OTP sent to your email. Please check your inbox.',
            'expires_in': 600  # 10 minutes in seconds
        })


class VerifyOTPAndChangePasswordView(APIView):
    """
    Verify OTP and change password
    POST /api/auth/verify-otp-and-change-password/
    Body: { "otp_code": "123456", "new_password": "newpass123" }
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        from .models import PasswordChangeOTP

        user = request.user
        otp_code = request.data.get('otp_code')
        new_password = request.data.get('new_password')

        if not otp_code or not new_password:
            return Response({
                'success': False,
                'message': 'OTP code and new password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate password strength (minimum 8 characters)
        if len(new_password) < 8:
            return Response({
                'success': False,
                'message': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Find valid OTP
        try:
            otp = PasswordChangeOTP.objects.filter(
                user=user,
                otp_code=otp_code,
                is_used=False
            ).latest('created_at')
        except PasswordChangeOTP.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid or expired OTP code'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP is valid
        if not otp.is_valid():
            if otp.attempts >= 3:
                return Response({
                    'success': False,
                    'message': 'Maximum attempts exceeded. Please request a new OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                otp.increment_attempts()
                return Response({
                    'success': False,
                    'message': 'Invalid or expired OTP code',
                    'attempts_remaining': 3 - otp.attempts
                }, status=status.HTTP_400_BAD_REQUEST)

        # Change password
        user.set_password(new_password)
        user.save()

        # Mark OTP as used
        otp.mark_as_used()

        # Keep user logged in after password change
        update_session_auth_hash(request, user)

        return Response({
            'success': True,
            'message': 'Password changed successfully'
        })


class RequestForgotPasswordOTPView(APIView):
    """
    Request OTP for forgot password
    POST /api/auth/forgot-password/
    Body: { "email": "user@example.com" }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import random
        from .models import ForgotPasswordOTP
        from .utils import send_forgot_password_otp

        email = request.data.get('email')

        if not email:
            return Response({
                'success': False,
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            # Generate 6-digit OTP
            otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            # Invalidate old OTPs
            ForgotPasswordOTP.objects.filter(user=user, is_used=False).update(is_used=True)

            # Create new OTP with 10 minute expiry
            otp = ForgotPasswordOTP.objects.create(
                user=user,
                otp_code=otp_code,
                expires_at=timezone.now() + timedelta(minutes=10)
            )

            # Send email with OTP
            try:
                send_forgot_password_otp(user, otp_code)
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Failed to send OTP email: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                'success': True,
                'message': 'OTP sent to your email. Please check your inbox.',
                'expires_in': 600  # 10 minutes in seconds
            })

        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            return Response({
                'success': True,
                'message': 'If an account with this email exists, an OTP has been sent.'
            })


class VerifyForgotPasswordOTPView(APIView):
    """
    Verify OTP and reset password for forgot password
    POST /api/auth/forgot-password/verify/
    Body: { "email": "user@example.com", "otp_code": "123456", "new_password": "newpass123" }
    Or for verification only: { "email": "user@example.com", "otp_code": "123456", "verify_only": true }
    """
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        from .models import ForgotPasswordOTP

        email = request.data.get('email')
        otp_code = request.data.get('otp_code')
        new_password = request.data.get('new_password')
        verify_only = request.data.get('verify_only', False)

        if not email or not otp_code:
            return Response({
                'success': False,
                'message': 'Email and OTP code are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not verify_only and not new_password:
            return Response({
                'success': False,
                'message': 'New password is required for password reset'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not verify_only:
            # Validate password strength (minimum 8 characters)
            if len(new_password) < 8:
                return Response({
                    'success': False,
                    'message': 'Password must be at least 8 characters long'
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid email address'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Find valid OTP
        try:
            otp = ForgotPasswordOTP.objects.filter(
                user=user,
                otp_code=otp_code,
                is_used=False
            ).latest('created_at')
        except ForgotPasswordOTP.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid or expired OTP code'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP is valid
        if not otp.is_valid():
            if otp.attempts >= 3:
                return Response({
                    'success': False,
                    'message': 'Maximum attempts exceeded. Please request a new OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                otp.increment_attempts()
                return Response({
                    'success': False,
                    'message': 'Invalid or expired OTP code',
                    'attempts_remaining': 3 - otp.attempts
                }, status=status.HTTP_400_BAD_REQUEST)

        if verify_only:
            # Just verify the OTP, don't reset password or mark as used
            return Response({
                'success': True,
                'message': 'OTP verified successfully'
            })
        else:
            # Reset password
            user.set_password(new_password)
            user.save()

            # Mark OTP as used
            otp.mark_as_used()

            return Response({
                'success': True,
                'message': 'Password reset successful. You can now login with your new password.'
            })


class DeleteAccountView(APIView):
    """
    Delete user account
    DELETE /api/auth/delete-account/
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        user = request.user

        # Get user details before deletion for response
        user_data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined
        }

        # Blacklist all user's tokens
        try:
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception as e:
            pass  # Continue even if token blacklisting fails

        # Delete user (will cascade to related objects based on model definitions)
        user.delete()

        return Response({
            'success': True,
            'message': 'Account deleted successfully',
            'user_data': user_data
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """
    Request password reset email
    POST /api/auth/password-reset/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)

            # Create password reset token
            token = secrets.token_urlsafe(32)
            reset_token = PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(hours=24)
            )

            # Send password reset email
            send_password_reset_email(user, token)

            return Response({
                'success': True,
                'message': 'Password reset email sent. Please check your inbox.'
            })

        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            return Response({
                'success': True,
                'message': 'Password reset email sent. Please check your inbox.'
            })


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token
    POST /api/auth/password-reset/confirm/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            reset_token = PasswordResetToken.objects.get(token=token)

            if not reset_token.is_valid():
                return Response({
                    'success': False,
                    'error': 'Invalid or expired token'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Reset password
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            # Mark token as used
            reset_token.mark_as_used()

            return Response({
                'success': True,
                'message': 'Password reset successful. You can now login with your new password.'
            })

        except PasswordResetToken.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """
    Verify email with token via link click
    GET /api/auth/verify-email/?token=xxx

    User clicks link in email → Backend verifies → Redirects to frontend with result
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.shortcuts import redirect
        from urllib.parse import quote

        token = request.GET.get('token')
        frontend_url = settings.FRONTEND_URL

        if not token:
            # Redirect to frontend with error
            return redirect(f'{frontend_url}/verify-email?status=error&message={quote("Missing verification token")}')

        try:
            verification_token = EmailVerificationToken.objects.get(token=token)

            if not verification_token.is_valid():
                # Token expired or already used
                return redirect(f'{frontend_url}/verify-email?status=error&message={quote("Token expired or already used")}')

            # Verify email
            user = verification_token.user
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])

            # Mark token as used
            verification_token.mark_as_used()

            # Redirect to frontend with success
            return redirect(f'{frontend_url}/verify-email?status=success&message={quote("Email verified successfully")}')

        except EmailVerificationToken.DoesNotExist:
            # Invalid token
            return redirect(f'{frontend_url}/verify-email?status=error&message={quote("Invalid verification token")}')



class VerifyTokenView(APIView):
    """
    Verify if JWT token is still valid
    GET /api/auth/verify-token/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return Response({
                'valid': False,
                'error': 'No token provided'
            }, status=400)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Validate token
            from rest_framework_simplejwt.tokens import AccessToken
            from rest_framework_simplejwt.exceptions import TokenError
            
            AccessToken(token)
            return Response({
                'valid': True,
                'message': 'Token is valid'
            })
        except TokenError:
            return Response({
                'valid': False,
                'error': 'Token is invalid or expired'
            }, status=401)


            
class ResendVerificationEmailView(APIView):
    """
    Resend email verification
    POST /api/auth/resend-verification/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.is_email_verified:
            return Response({
                'success': False,
                'error': 'Email is already verified'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new verification token
        token = secrets.token_urlsafe(32)
        verification_token = EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Send verification email
        send_verification_email(user, token)

        return Response({
            'success': True,
            'message': 'Verification email sent. Please check your inbox.'
        })



class GoogleAuthView(APIView):
    """
    Google OAuth authentication
    POST /api/auth/google/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        google_token = serializer.validated_data['google_token']

          # ✅ ADD THIS LOGGING
        # print(f"🔍 Google OAuth Debug:")
        # print(f"   - Token received: {google_token[:50]}...")
        # print(f"   - CLIENT_ID configured: {bool(settings.GOOGLE_OAUTH_CLIENT_ID)}")
        # print(f"   - CLIENT_ID value: {settings.GOOGLE_OAUTH_CLIENT_ID[:20]}...")


        try:
            # Verify Google token
            idinfo = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID
            )


            # print(f"✅ Google token verified successfully")
            # print(f"   - Email: {idinfo.get('email')}")
            # print(f"   - Name: {idinfo.get('name')}")

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            google_id = idinfo['sub']
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            profile_picture = idinfo.get('picture', '')

            # ✅ VALIDATE EMAIL DOMAIN (Gmail and Yahoo only)
            import re
            email_lower = email.lower()
            allowed_domains_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail\.com|yahoo\.com)$'

            if not re.match(allowed_domains_pattern, email_lower):
                return Response({
                    'success': False,
                    'error': 'Only Gmail (@gmail.com) and Yahoo (@yahoo.com) email addresses are allowed for registration.'
                }, status=status.HTTP_403_FORBIDDEN)

            # Try to get user by google_id first
            try:
                user = User.objects.get(google_id=google_id)
                created = False

                # Update profile picture if changed
                if user.profile_picture != profile_picture:
                    user.profile_picture = profile_picture
                    user.save(update_fields=['profile_picture'])

            except User.DoesNotExist:
                # Try to get user by email
                try:
                    user = User.objects.get(email=email)
                    created = False

                    # Link Google account to existing user
                    user.google_id = google_id
                    user.profile_picture = profile_picture
                    user.is_email_verified = True
                    user.save(update_fields=['google_id', 'profile_picture', 'is_email_verified'])

                except User.DoesNotExist:
                    # Create new user
                    user = User.objects.create_user(
                        email=email,
                        username= email.split('@')[0][:8] + google_id[:4],          #email.split('@')[0]+ google_id[:6],
                        first_name=first_name,
                        last_name=last_name,
                        google_id=google_id,
                        profile_picture=profile_picture,
                        is_email_verified=True,
                    )
                    created = True

            user.update_last_login()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            session = UserSession.objects.filter(
                user=user, 
                is_active=True
            ).order_by('-last_activity').first()
            
            if session:
                session.refresh_jti = refresh.get('jti')
                session.save(update_fields=['refresh_jti'])

            return Response({
                'success': True,
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'is_new_user': created,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })

        except ValueError as e:
            # print(f"❌ ❌ ❌ TOKEN VERIFICATION FAILED!")
            # print(f"   Error: {str(e)}")
            # print(f"   This usually means:")
            # print(f"   1. Frontend CLIENT_ID ≠ Backend CLIENT_ID")
            # print(f"   2. Wrong CLIENT_ID type (use Web client, not iOS/Android)")
            # print(f"   3. Token expired or invalid")
            
            return Response({
                'success': False,
                'error': f'Google token verification failed: {str(e)}'
            }, status=400)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Authentication failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

























#for two-factor auth

class TwoFactorSetupView(APIView):
    """
    Initialize 2FA setup - Generate QR code and backup codes
    POST /api/auth/2fa/setup/

    Returns:
        - QR code (base64 image)
        - Secret key (to save temporarily)
        - 10 backup codes (show to user once)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Check if 2FA is already enabled
        if user.two_factor_enabled:
            return Response({
                'success': False,
                'error': '2FA is already enabled for this account'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate 2FA credentials with error handling
        try:
            setup_data = setup_2fa_for_user(user)

            return Response({
                'success': True,
                'message': 'Scan this QR code with Google Authenticator',
                'qr_code': setup_data['qr_code'],
                'secret': setup_data['secret'],  # Return to frontend (will need for verification)
                'backup_codes': setup_data['backup_codes'],
                'instructions': [
                    '1. Install Google Authenticator app on your phone',
                    '2. Scan the QR code with the app',
                    '3. Enter the 6-digit code from the app to verify',
                    '4. Save your backup codes in a secure place'
                ]
            })
        except ImportError as e:
            return Response({
                'success': False,
                'error': f'2FA dependencies not installed: {str(e)}. Please install pyotp and qrcode libraries.',
                'details': 'Run: pip install pyotp qrcode[pil]'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            import traceback
            return Response({
                'success': False,
                'error': f'Failed to setup 2FA: {str(e)}',
                'details': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TwoFactorVerifySetupView(APIView):
    """
    Verify 2FA setup and enable it
    POST /api/auth/2fa/verify-setup/

    Body:
        {
            "token": "123456",  // 6-digit code from authenticator app
            "secret": "BASE32SECRET"  // Secret from setup step
        }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorVerifySetupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid input data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        token = serializer.validated_data['token']
        secret = serializer.validated_data['secret']

        # Check if 2FA is already enabled
        if user.two_factor_enabled:
            return Response({
                'success': False,
                'error': '2FA is already enabled for this account'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify the token
        if not TwoFactorAuth.verify_token(secret, token):
            return Response({
                'success': False,
                'error': 'Invalid verification code. Please check your authenticator app and try again.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate backup codes
        hashed_codes, plain_codes = TwoFactorAuth.generate_backup_codes()

        # Enable 2FA for the user
        enable_2fa_for_user(user, secret, hashed_codes)

        return Response({
            'success': True,
            'message': '2FA has been successfully enabled for your account',
            'backup_codes': plain_codes,
            'instructions': [
                '⚠️ Save these backup codes in a secure place',
                'Each code can only be used once',
                'If you lose access to your authenticator app, use these codes to login',
                'You can generate new backup codes later if needed'
            ]
        })


class TwoFactorVerifyLoginView(APIView):
    """
    Verify 2FA code during login
    POST /api/auth/2fa/verify/
    
    Body:
        {
            "email": "user@example.com",
            "password": "password123",
            "token": "123456"  // 6-digit code from authenticator app OR backup code
        }
    
    OR after temporary token:
        {
            "token": "123456"
        }
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        from .models import UserSession
        serializer = TwoFactorVerifyLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get user from email/password or from auth token
        if 'email' in request.data and 'password' in request.data:
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            # Authenticate user
            from .models import User
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            user = authenticate(username=username, password=password)
            
            if not user:
                return Response({
                    'success': False,
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            # User already authenticated (from middleware)
            user = request.user
        
        # Check if 2FA is enabled
        if not user.two_factor_enabled:
            return Response({
                'success': False,
                'error': '2FA is not enabled for this account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        token = serializer.validated_data['token']
        
        # Try verifying as TOTP token first
        is_valid_totp = TwoFactorAuth.verify_token(user.two_factor_secret, token)
        
        if is_valid_totp:
            # Generate full JWT tokens
            refresh = RefreshToken.for_user(user)
            user.update_last_login()
            
            # Since TwoFactorAuth handles intermediate logins, track_login might have already
            # created a session, or we might need to find it by time/IP. For now, try to find
            # the latest active session for this user.
            session = UserSession.objects.filter(
                user=user, 
                is_active=True
            ).order_by('-last_activity').first()
            if session:
                session.refresh_jti = refresh.get('jti')
                session.save(update_fields=['refresh_jti'])

            from .serializers import UserProfileSerializer
            return Response({
                'success': True,
                'message': '2FA verification successful',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        
        # Try as backup code
        is_valid_backup, remaining_codes = TwoFactorAuth.verify_backup_code(
            user.backup_codes, token
        )
        
        if is_valid_backup:
            # Update backup codes (remove used one)
            user.backup_codes = remaining_codes
            user.save(update_fields=['backup_codes'])
            
            # Generate full JWT tokens
            refresh = RefreshToken.for_user(user)
            user.update_last_login()
            
            session = UserSession.objects.filter(
                user=user, 
                is_active=True
            ).order_by('-last_activity').first()
            if session:
                session.refresh_jti = refresh.get('jti')
                session.save(update_fields=['refresh_jti'])


            from .serializers import UserProfileSerializer
            return Response({
                'success': True,
                'message': '2FA verification successful (backup code used)',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'warning': f'You have {len(remaining_codes)} backup codes remaining'
            })
        
        # Both failed
        return Response({
            'success': False,
            'error': 'Invalid verification code or backup code'
        }, status=status.HTTP_401_UNAUTHORIZED)


class TwoFactorDisableView(APIView):
    """
    Disable 2FA
    POST /api/auth/2fa/disable/
    
    Body:
        {
            "password": "user_password",  // Require password for security
            "token": "123456"  // Current TOTP token or backup code
        }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = TwoFactorDisableSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        token = serializer.validated_data['token']
        
        # Check if 2FA is enabled
        if not user.two_factor_enabled:
            return Response({
                'success': False,
                'error': '2FA is not enabled for this account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify token or backup code
        is_valid_totp = TwoFactorAuth.verify_token(user.two_factor_secret, token)
        is_valid_backup, _ = TwoFactorAuth.verify_backup_code(user.backup_codes, token)
        
        if not (is_valid_totp or is_valid_backup):
            return Response({
                'success': False,
                'error': 'Invalid verification code'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Disable 2FA
        disable_2fa_for_user(user)
        
        return Response({
            'success': True,
            'message': '2FA has been disabled successfully'
        })


class TwoFactorBackupCodesView(APIView):
    """
    Get current backup codes status
    GET /api/auth/2fa/backup-codes/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not user.two_factor_enabled:
            return Response({
                'success': False,
                'error': '2FA is not enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        remaining_count = len(user.backup_codes)
        
        return Response({
            'success': True,
            'backup_codes_remaining': remaining_count,
            'warning': 'Backup codes are hashed and cannot be retrieved. Generate new ones if needed.'
        })


class TwoFactorRegenerateBackupCodesView(APIView):
    """
    Regenerate backup codes
    POST /api/auth/2fa/regenerate-backup/

    Body:
        {
            "token": "123456"  // Current TOTP token
        }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorRegenerateBackupCodesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        token = serializer.validated_data['token']

        if not user.two_factor_enabled:
            return Response({
                'success': False,
                'error': '2FA is not enabled'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify token
        if not TwoFactorAuth.verify_token(user.two_factor_secret, token):
            return Response({
                'success': False,
                'error': 'Invalid verification code'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Generate new backup codes
        hashed_codes, plain_codes = TwoFactorAuth.generate_backup_codes()

        # Update user
        user.backup_codes = hashed_codes
        user.save(update_fields=['backup_codes'])

        return Response({
            'success': True,
            'message': 'New backup codes generated',
            'backup_codes': plain_codes,
            'warning': 'Save these codes now - old codes are invalidated!'
        })


class TwoFactorStatusView(APIView):
    """
    Get 2FA status for current user
    GET /api/auth/2fa/status/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        return Response({
            'success': True,
            'two_factor_enabled': user.two_factor_enabled,
            'enabled_at': user.two_factor_enabled_at.isoformat() if user.two_factor_enabled_at else None,
            'backup_codes_remaining': len(user.backup_codes) if user.two_factor_enabled else 0
        })
    
















#for logout from all devices

class ActiveSessionsView(APIView):
    """
    Get all active sessions for current user
    GET /api/auth/sessions/active/
    
    Shows all devices/locations where user is currently logged in
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get all active sessions for this user
        active_sessions = UserSession.objects.filter(
            user=user,
            is_active=True
        ).order_by('-last_activity')
        
        # Get current session (from IP + user agent)
        current_ip, _ = self._get_client_ip(request)
        current_ua = request.META.get('HTTP_USER_AGENT', '')
        
        sessions_data = []
        for session in active_sessions:
            is_current = (
                session.ip_address == current_ip and 
                session.user_agent == current_ua
            )
            
            sessions_data.append({
                'id': str(session.id),
                'device': session.get_device_string(),
                'device_type': session.device_type,
                'browser': f"{session.browser_name} {session.browser_version}",
                'os': f"{session.os_name} {session.os_version}",
                'location': session.get_location_string(),
                'ip_address': session.ip_address,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'is_current': is_current,
                'page_views': session.page_views,
                'duration_seconds': session.duration_seconds,
                'threat_level': session.threat_level,
                'is_vpn': session.is_vpn,
            })
        
        return Response({
            'success': True,
            'total_sessions': len(sessions_data),
            'sessions': sessions_data
        })
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip, ''


class LogoutAllDevicesView(APIView):
    """
    Logout from all devices by blacklisting all refresh tokens
    POST /api/auth/logout-all-devices/
    
    Body (optional):
    {
        "keep_current": true  // Keep current device logged in (default: true)
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        user = request.user
        keep_current = request.data.get('keep_current', True)
        
        # Get current refresh token JTI if keeping current session
        current_jti = None
        if keep_current:
            current_refresh = request.data.get('refresh_token')
            if current_refresh:
                try:
                    token = RefreshToken(current_refresh)
                    current_jti = str(token['jti'])
                except Exception as e:
                    print(f"Could not extract JTI: {e}")
        
        # Blacklist all outstanding tokens for this user
        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        blacklisted_count = 0
        
        for token in outstanding_tokens:
            # Skip current token if keeping session
            if keep_current and current_jti and token.jti == current_jti:
                continue
            
            # Blacklist if not already blacklisted
            if not BlacklistedToken.objects.filter(token=token).exists():
                BlacklistedToken.objects.create(token=token)
                blacklisted_count += 1
        
        # Deactivate all UserSessions except current
        if keep_current:
            if current_jti:
                deactivated = UserSession.objects.filter(
                    user=user,
                    is_active=True
                ).exclude(
                    refresh_jti=current_jti
                ).update(
                    is_active=False,
                    session_ended_at=timezone.now()
                )
            else:
                current_ip, _ = self._get_client_ip(request)
                current_ua = request.META.get('HTTP_USER_AGENT', '')
                
                # Deactivate all sessions except current device
                deactivated = UserSession.objects.filter(
                    user=user,
                    is_active=True
                ).exclude(
                    Q(ip_address=current_ip) & Q(user_agent=current_ua)
                ).update(
                    is_active=False,
                    session_ended_at=timezone.now()
                )
        else:
            # Deactivate ALL sessions
            deactivated = UserSession.objects.filter(
                user=user,
                is_active=True
            ).update(
                is_active=False,
                session_ended_at=timezone.now()
            )
        
        return Response({
            'success': True,
            'message': f'Logged out from {blacklisted_count} device(s)',
            'tokens_blacklisted': blacklisted_count,
            'sessions_ended': deactivated,
            'current_session_kept': keep_current
        })
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip, ''


class LogoutSpecificDeviceView(APIView):
    """
    Logout from a specific device/session
    POST /api/auth/logout-device/{session_id}/
    
    Blacklists the token and deactivates the session
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, session_id):
        user = request.user
        
        try:
            # Get the specific session
            session = UserSession.objects.get(id=session_id, user=user, is_active=True)
            
            # Find and blacklist associated refresh token
            if session.refresh_jti:
                try:
                    token = OutstandingToken.objects.get(jti=session.refresh_jti)
                    BlacklistedToken.objects.get_or_create(token=token)
                    blacklisted += 1
                except OutstandingToken.DoesNotExist:
                    pass
            else:
                session_time = session.created_at
                
                # Fallback to time-based approach if refresh_jti is not populated
                tokens = OutstandingToken.objects.filter(
                    user=user,
                    created_at__gte=session_time - timezone.timedelta(minutes=5),
                    created_at__lte=session_time + timezone.timedelta(minutes=5)
                )
                
                for token in tokens:
                    if not BlacklistedToken.objects.filter(token=token).exists():
                        BlacklistedToken.objects.create(token=token)
                        blacklisted += 1
            
            # Deactivate the session
            session.is_active = False
            session.session_ended_at = timezone.now()
            session.save()
            
            return Response({
                'success': True,
                'message': f'Logged out from {session.get_device_string()}',
                'session_id': str(session_id),
                'tokens_blacklisted': blacklisted
            })
            
        except UserSession.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Session not found or already logged out'
            }, status=status.HTTP_404_NOT_FOUND)


class SessionSecurityView(APIView):
    """
    Get session security information
    GET /api/auth/sessions/security/
    
    Shows suspicious sessions, VPN usage, multiple locations, etc.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get all active sessions
        active_sessions = UserSession.objects.filter(user=user, is_active=True)
        
        # Security analysis
        total_sessions = active_sessions.count()
        vpn_sessions = active_sessions.filter(is_vpn=True).count()
        tor_sessions = active_sessions.filter(is_tor=True).count()
        high_threat = active_sessions.filter(threat_level='high').count()
        
        # Unique locations
        unique_countries = active_sessions.values('country').distinct().count()
        unique_cities = active_sessions.values('city').distinct().count()
        
        # Device types
        device_breakdown = {}
        for device_type in ['mobile', 'desktop', 'tablet', 'bot']:
            count = active_sessions.filter(device_type=device_type).count()
            if count > 0:
                device_breakdown[device_type] = count
        
        # Recent suspicious activity
        suspicious_sessions = active_sessions.filter(
            Q(threat_level__in=['medium', 'high']) | Q(is_vpn=True) | Q(is_tor=True)
        ).values(
            'id', 'ip_address', 'country', 'city', 
            'threat_level', 'is_vpn', 'is_tor', 'last_activity'
        )
        
        return Response({
            'success': True,
            'summary': {
                'total_active_sessions': total_sessions,
                'vpn_sessions': vpn_sessions,
                'tor_sessions': tor_sessions,
                'high_threat_sessions': high_threat,
                'unique_countries': unique_countries,
                'unique_cities': unique_cities,
                'device_breakdown': device_breakdown
            },
            'suspicious_sessions': list(suspicious_sessions),
            'recommendations': self._get_security_recommendations(
                total_sessions, vpn_sessions, tor_sessions, high_threat, unique_countries
            )
        })
    
    @staticmethod
    def _get_security_recommendations(total, vpn, tor, high_threat, countries):
        """Generate security recommendations"""
        recommendations = []
        
        if tor > 0:
            recommendations.append({
                'level': 'critical',
                'message': f'{tor} session(s) detected using Tor. Consider logging out all devices.'
            })
        
        if high_threat > 0:
            recommendations.append({
                'level': 'high',
                'message': f'{high_threat} high-threat session(s) detected. Review and logout suspicious devices.'
            })
        
        if vpn > total * 0.5 and total > 2:
            recommendations.append({
                'level': 'medium',
                'message': 'Multiple VPN sessions detected. Ensure these are your devices.'
            })
        
        if countries > 3:
            recommendations.append({
                'level': 'medium',
                'message': f'Sessions active in {countries} different countries. Verify all locations are correct.'
            })
        
        if total > 10:
            recommendations.append({
                'level': 'low',
                'message': f'{total} active sessions detected. Consider logging out unused devices.'
            })
        
        if not recommendations:
            recommendations.append({
                'level': 'good',
                'message': 'No security concerns detected. All sessions appear normal.'
            })
        
        return recommendations

























from .models import EnterpriseContact
from .serializers import EnterpriseContactSerializer
from .utils import send_enterprise_contact_email

class EnterpriseContactView(APIView):
    """
    Enterprise contact form submission
    POST /api/auth/contact/enterprise/
    
    Public endpoint - no authentication required
    Saves contact to database and sends email notification
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Handle contact form submission
        
        Expected fields:
        - first_name (required)
        - last_name (required)
        - email (required)
        - phone (optional)
        - company_name (required)
        - company_size (required)
        - job_title (optional)
        - project_details (required)
        - budget_range (optional)
        - timeline (optional)
        """
        serializer = EnterpriseContactSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get IP address
            ip_address = self._get_client_ip(request)
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Save contact
            contact = serializer.save(
                ip_address=ip_address,
                user_agent=user_agent,
                source='website'
            )
            
            # Send email notification to your team
            try:
                send_enterprise_contact_email(contact)
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to send contact notification email: {e}")
            
            return Response({
                'success': True,
                'message': 'Thank you for your interest! Our team will contact you within 24 hours.',
                'contact_id': str(contact.id)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error saving contact: {e}")
            return Response({
                'success': False,
                'error': 'An error occurred. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    









class NotificationPreferencesView(APIView):
    """
    Manage user notification preferences (in-app/push)
    GET /api/auth/notification-preferences/
    PUT /api/auth/notification-preferences/
    """
    permission_classes = [IsAuthenticated]

    DEFAULTS = {
        # Email notification preferences (used by Settings > Account)
        'weekly_reports': True,
        'automation_alerts': True,
        'dm_failures': True,
        'account_issues': True,
        # General notification preferences
        'marketing_emails': True,
        'account_notifications': True,
        'security_alerts': True,
        'product_updates': True,
    }
    
    def get(self, request):
        """Get current notification preferences"""
        user = request.user
        
        final_preferences = self.DEFAULTS.copy()
        if user.notification_preferences:
            final_preferences.update(user.notification_preferences)
        
        return Response({
            'success': True,
            'preferences': final_preferences
        })
    
    def put(self, request):
        """Update notification preferences"""
        user = request.user
        
        # Accept both nested { preferences: {...} } and flat payload { key: value }
        preferences = request.data.get('preferences', None)
        if preferences is None:
            # Frontend sends flat payload directly
            preferences = {k: v for k, v in request.data.items() if k in self.DEFAULTS or k in (user.notification_preferences or {})}
        
        if preferences:
            # Force security alerts to always be enabled
            if 'security_alerts' in preferences:
                preferences['security_alerts'] = True
            
            if not isinstance(user.notification_preferences, dict):
                user.notification_preferences = {}
                
            user.notification_preferences.update(preferences)
            user.save(update_fields=['notification_preferences', 'updated_at'])
        
        # Return the full merged preferences
        final_preferences = self.DEFAULTS.copy()
        if user.notification_preferences:
            final_preferences.update(user.notification_preferences)
        
        return Response({
            'success': True,
            'message': 'Notification preferences updated successfully',
            'preferences': final_preferences
        })













class FeedbackView(APIView):
    """
    Submit user feedback.

    POST /api/auth/feedback/  – auth optional (anonymous allowed)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from .models import Feedback
        from .serializers import FeedbackSerializer

        serializer = FeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user if request.user.is_authenticated else None

        # Derive email / name from the authenticated user so the fields
        # are never left blank in the database.
        save_kwargs = {
            'user': user,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
        }
        if user:
            save_kwargs['email'] = user.email
            save_kwargs['name'] = user.username

        feedback = serializer.save(**save_kwargs)

        return Response(
            {'id': str(feedback.id), 'message': 'Thank you for your feedback!'},
            status=status.HTTP_201_CREATED,
        )


class FeedbackListView(APIView):
    """List the authenticated user's own feedback submissions."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import Feedback
        from .serializers import FeedbackSerializer

        qs = Feedback.objects.filter(user=request.user).order_by('-created_at')[:50]
        return Response(FeedbackSerializer(qs, many=True).data)















@api_view(['GET'])
@permission_classes([IsAuthenticated])
def instagram_oauth_initiate(request):
    """
    Step 1: Generate Facebook OAuth URL for Instagram permissions

    GET /api/auth/instagram/oauth/

    Returns JSON with the OAuth URL so the frontend can open it in a popup.
    The frontend must call this with JWT auth header, then open the returned
    URL in a popup window.
    """

    facebook_app_id = settings.FACEBOOK_APP_ID
    # redirect_uri must point to the BACKEND callback endpoint
    backend_url = settings.BACKEND_URL.rstrip('/')
    redirect_uri = f"{backend_url}/api/auth/instagram/callback/"

    # Required Instagram permissions
    scope = ",".join([
        "instagram_basic",  # Basic profile info
        "instagram_manage_messages",  # Send/receive DMs
        "instagram_manage_comments",  # Reply to comments
        "pages_show_list",  # List Facebook pages
        "pages_read_engagement",  # Read page data
    ])

    # Generate a cryptographically secure random state token
    # Store the user association in cache (expires in 10 minutes)
    state_token = secrets.token_urlsafe(32)
    cache.set(
        f"instagram_oauth_state:{state_token}",
        str(request.user.id),
        timeout=600  # 10 minutes
    )

    # Build OAuth URL
    oauth_params = urlencode({
        'client_id': facebook_app_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'response_type': 'code',
        'state': state_token,
    })
    oauth_url = f"https://www.facebook.com/v21.0/dialog/oauth?{oauth_params}"

    logger.info(f"Initiating Instagram OAuth for user {request.user.id}")

    return Response({'oauth_url': oauth_url})


@api_view(['GET'])
@permission_classes([AllowAny])
def instagram_oauth_callback(request):
    """
    Step 2: Handle OAuth callback from Facebook

    GET /api/auth/instagram/callback/?code=...&state=...

    This exchanges the code for access token and saves Instagram account.
    Returns an HTML page that notifies the parent window and auto-closes.
    """

    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    frontend_url = settings.FRONTEND_URL.rstrip('/')

    def _popup_response(success, message=''):
        """Return HTML that notifies the opener window and closes the popup."""
        status_val = 'success' if success else 'error'
        return HttpResponse(
            f"""<!DOCTYPE html><html><body><script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'instagram_oauth',
                    status: '{status_val}',
                    message: '{message}'
                }}, '{frontend_url}');
            }}
            window.close();
            </script><p>{'Connected! This window will close.' if success else f'Error: {message}. Closing...'}</p></body></html>""",
            content_type='text/html'
        )

    # Handle errors from Facebook
    if error:
        error_description = request.GET.get('error_description', 'Unknown error')
        logger.error(f"OAuth error: {error} - {error_description}")
        return _popup_response(False, 'oauth_failed')

    if not code:
        logger.error("No code received from OAuth")
        return _popup_response(False, 'no_code')

    if not state:
        logger.error("No state received from OAuth")
        return _popup_response(False, 'invalid_state')

    # Verify state token from cache (CSRF protection)
    cache_key = f"instagram_oauth_state:{state}"
    user_id = cache.get(cache_key)
    if not user_id:
        logger.error(f"Invalid or expired state token: {state}")
        return _popup_response(False, 'invalid_state')

    # Delete the state token so it cannot be reused
    cache.delete(cache_key)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User not found for id: {user_id}")
        return _popup_response(False, 'invalid_state')

    # Exchange code for access token
    try:
        token_data = exchange_code_for_token(code)

        if not token_data:
            raise Exception("Failed to exchange code for token")

        # Get Instagram account info (includes page_access_token)
        instagram_data = get_instagram_account_info(token_data['access_token'])

        if not instagram_data:
            raise Exception("Failed to fetch Instagram account info")

        # Save to database using page access token (required for Graph API)
        instagram_account = save_instagram_account(
            user=user,
            access_token=instagram_data['page_access_token'],
            expires_in=token_data.get('expires_in', 5183944),  # ~60 days
            instagram_data=instagram_data
        )

        logger.info(
            f"Successfully connected Instagram account "
            f"@{instagram_account.username} for user {user.id}"
        )

        return _popup_response(True)

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return _popup_response(False, 'connection_failed')


def exchange_code_for_token(code):
    """
    Exchange authorization code for access token
    """
    backend_url = settings.BACKEND_URL.rstrip('/')
    redirect_uri = f"{backend_url}/api/auth/instagram/callback/"
    
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


def save_instagram_account(user, access_token, expires_in, instagram_data, connection_method='facebook_graph'):
    """
    Save or update Instagram account in database.

    Args:
        access_token: The access token depending on the connection_method
    """
    expires_at = datetime.now() + timedelta(seconds=expires_in)

    # Base payload
    defaults={
        'user': user,
        'username': instagram_data['username'],
        'access_token': access_token,
        'token_expires_at': expires_at,
        'profile_picture_url': instagram_data.get('profile_picture_url', ''),
        'followers_count': instagram_data.get('followers_count', 0),
        'connection_method': connection_method,
        'is_active': True
    }

    if connection_method == 'facebook_graph':
        defaults['page_id'] = instagram_data.get('page_id')
        instagram_account, created = InstagramAccount.objects.update_or_create(
            instagram_user_id=instagram_data['instagram_user_id'],
            defaults=defaults
        )
    else:
        defaults['platform_id'] = instagram_data.get('platform_id')
        instagram_account, created = InstagramAccount.objects.update_or_create(
            platform_id=instagram_data['platform_id'],
            # We also set instagram_user_id to platform_id here because it's required and unique.
            # Ideally the schema would decouple them better, but for now this satisfies the unique constraint.
            defaults={**defaults, 'instagram_user_id': instagram_data['platform_id']}
        )
    
    if created:
        logger.info(f"Created new Instagram account: @{instagram_account.username}")
    else:
        logger.info(f"Updated existing Instagram account: @{instagram_account.username}")
    
    return instagram_account


# ============================================================================
# INSTAGRAM PLATFORM API (DIRECT LOGIN) - NEW
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def instagram_platform_oauth_initiate(request):
    """
    Step 1: Generate Instagram Platform OAuth URL (Direct Login)
    GET /api/auth/instagram-direct/oauth/
    """
    client_id = settings.INSTAGRAM_CLIENT_ID
    backend_url = settings.BACKEND_URL.rstrip('/')
    
    # We must match the trailing slash exactly as it is configured in the Meta Dashboard
    redirect_uri = f"{backend_url}/api/auth/instagram-direct/callback/"

    # Required permissions for Platform API
    scope = ",".join([
        "instagram_business_basic",
        "instagram_business_manage_messages",
        "instagram_business_manage_comments",
    ])

    state_token = secrets.token_urlsafe(32)
    cache.set(f"instagram_direct_state:{state_token}", str(request.user.id), timeout=600)

    oauth_params = urlencode({
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'response_type': 'code',
        'state': state_token,
    })
    
    # Use www.instagram.com as shown in the dashboard Embed URL
    oauth_url = f"https://www.instagram.com/oauth/authorize?{oauth_params}"
    logger.info(f"Initiating Instagram Platform OAuth for user {request.user.id}")

    return Response({'oauth_url': oauth_url})


@api_view(['GET'])
@permission_classes([AllowAny])
def instagram_platform_oauth_callback(request):
    """
    Step 2: Handle OAuth callback from independent Instagram Platform
    GET /api/auth/instagram-direct/callback/
    """
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    frontend_url = settings.FRONTEND_URL.rstrip('/')

    def _popup_response(success, message=''):
        status_val = 'success' if success else 'error'
        return HttpResponse(
            f"""<!DOCTYPE html><html><body><script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'instagram_oauth',
                    status: '{status_val}',
                    message: '{message}'
                }}, '{frontend_url}');
            }}
            window.close();
            </script><p>{'Connected!' if success else f'Error: {message}'}</p></body></html>""",
            content_type='text/html'
        )

    if error:
        return _popup_response(False, 'oauth_failed')
    if not code or not state:
        return _popup_response(False, 'invalid_request')

    cache_key = f"instagram_direct_state:{state}"
    user_id = cache.get(cache_key)
    if not user_id:
        return _popup_response(False, 'invalid_state')
    cache.delete(cache_key)

    try:
        user = User.objects.get(id=user_id)
        
        # 1. Exchange code for short-lived access token
        backend_url = settings.BACKEND_URL.rstrip('/')
        redirect_uri = f"{backend_url}/api/auth/instagram-direct/callback/"
        
        token_response = requests.post("https://api.instagram.com/oauth/access_token", data={
            'client_id': settings.INSTAGRAM_CLIENT_ID,
            'client_secret': settings.INSTAGRAM_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': code
        })
        token_response.raise_for_status()
        token_data = token_response.json()
        short_lived_token = token_data['access_token']
        platform_user_id = token_data['user_id']
        
        # 2. Exchange for long-lived token
        ll_response = requests.get("https://graph.instagram.com/access_token", params={
            'grant_type': 'ig_exchange_token',
            'client_secret': settings.INSTAGRAM_CLIENT_SECRET,
            'access_token': short_lived_token
        })
        ll_response.raise_for_status()
        ll_data = ll_response.json()
        long_lived_token = ll_data['access_token']
        expires_in = ll_data.get('expires_in', 5184000) # ~60 days

        # 3. Get User Profile Information
        profile_response = requests.get(f"https://graph.instagram.com/v21.0/{platform_user_id}", params={
            'fields': 'id,username,name,profile_picture_url,followers_count',
            'access_token': long_lived_token
        })
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        # Build payload for save method
        instagram_data = {
            'platform_id': str(platform_user_id),
            'username': profile_data.get('username', f"ig_{platform_user_id}"),
            'profile_picture_url': profile_data.get('profile_picture_url', ''),
            'followers_count': profile_data.get('followers_count', 0)
        }

        # 4. Save to Database
        save_instagram_account(
            user=user,
            access_token=long_lived_token,
            expires_in=expires_in,
            instagram_data=instagram_data,
            connection_method='instagram_platform'
        )

        return _popup_response(True)

    except Exception as e:
        logger.error(f"Platform OAuth error: {str(e)}")
        return _popup_response(False, 'connection_failed')


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
        """Filter by current user — only return active accounts."""
        return InstagramAccount.objects.filter(user=self.request.user, is_active=True)

    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """
        Fetch Instagram posts for post targeting.
        GET /api/instagram-accounts/{id}/posts/
        Handles both connection methods:
          - instagram_platform: uses graph.instagram.com/me/media
          - facebook_graph: uses graph.facebook.com/{ig_user_id}/media
        """
        try:
            account = self.get_object()
            import requests as req

            # Choose correct base URL based on connection method
            if account.connection_method == 'instagram_platform':
                media_url = 'https://graph.instagram.com/v21.0/me/media'
                params = {
                    'access_token': account.access_token,
                    'fields': 'id,caption,media_type,thumbnail_url,media_url,timestamp,permalink',
                    'limit': 20,
                }
            else:
                media_url = f'https://graph.facebook.com/v21.0/{account.instagram_user_id}/media'
                params = {
                    'access_token': account.access_token,
                    'fields': 'id,caption,media_type,thumbnail_url,media_url,timestamp,permalink',
                    'limit': 20,
                }

            response = req.get(media_url, params=params, timeout=15)
            data = response.json()

            if 'error' in data:
                logger.error(f"Posts fetch error for {account.username}: {data['error']}")
                return Response({'error': data['error'].get('message', 'API error')}, status=400)

            posts = []
            for item in data.get('data', []):
                thumbnail = item.get('thumbnail_url') or item.get('media_url', '')
                posts.append({
                    'id': item['id'],
                    'caption': (item.get('caption', '') or '')[:100],
                    'media_type': item.get('media_type', 'IMAGE'),
                    'thumbnail_url': thumbnail,
                    'timestamp': item.get('timestamp', ''),
                    'permalink': item.get('permalink', ''),
                })

            return Response({'posts': posts, 'total': len(posts)})

        except Exception as e:
            logger.error(f"Failed to fetch Instagram posts: {str(e)}")
            return Response({'error': 'Failed to fetch posts', 'detail': str(e)}, status=500)


    @action(detail=True, methods=['get'])
    def profile_stats(self, request, pk=None):
        """
        Fetch live Instagram profile stats (followers + post count).
        GET /api/instagram-accounts/{id}/profile_stats/
        Handles both instagram_platform (graph.instagram.com) and
        facebook_graph (graph.facebook.com) connection methods.
        """
        account = self.get_object()
        import requests as req

        token = account.access_token
        is_platform = account.connection_method == 'instagram_platform'

        followers = account.followers_count
        media_count = account.media_count
        username = account.username
        profile_picture_url = account.profile_picture_url

        # ── Step 1: Fetch profile (followers, username) ───────────────────────
        try:
            if is_platform:
                profile_url = 'https://graph.instagram.com/v21.0/me'
                profile_fields = 'followers_count,username,profile_picture_url,media_count'
            else:
                ig_id = account.instagram_user_id
                profile_url = f'https://graph.facebook.com/v21.0/{ig_id}'
                profile_fields = 'followers_count,username,profile_picture_url'

            profile_resp = req.get(
                profile_url,
                params={'access_token': token, 'fields': profile_fields},
                timeout=15,
            )
            profile_data = profile_resp.json()

            if 'error' in profile_data:
                logger.error(f"[profile_stats] Profile error: {profile_data['error']}")
            else:
                followers = profile_data.get('followers_count') or followers
                username = profile_data.get('username') or username
                profile_picture_url = profile_data.get('profile_picture_url') or profile_picture_url
                # For platform accounts, media_count is reliably returned
                if is_platform and profile_data.get('media_count'):
                    media_count = profile_data['media_count']
                logger.info(f"[profile_stats] profile OK: followers={followers}, media_count={media_count}")
        except Exception as e:
            logger.error(f"[profile_stats] Profile fetch failed: {e}")

        # ── Step 2: Count posts from /media list (always for non-platform) ────
        # For instagram_platform we already have media_count from the profile;
        # for facebook_graph we count from the media list as a fallback.
        if not is_platform or media_count == 0:
            try:
                counted = 0
                if is_platform:
                    next_url: str | None = 'https://graph.instagram.com/v21.0/me/media'
                else:
                    ig_id = account.instagram_user_id
                    next_url = f'https://graph.facebook.com/v21.0/{ig_id}/media'

                next_params: dict = {'access_token': token, 'fields': 'id', 'limit': 100}

                while next_url:
                    media_resp = req.get(next_url, params=next_params, timeout=15)
                    media_data = media_resp.json()

                    if 'error' in media_data:
                        logger.error(f"[profile_stats] Media error: {media_data['error']}")
                        break

                    items = media_data.get('data', [])
                    counted += len(items)

                    paging = media_data.get('paging', {})
                    cursors = paging.get('cursors', {})
                    if paging.get('next') and cursors.get('after'):
                        next_params = {'access_token': token, 'fields': 'id', 'limit': 100, 'after': cursors['after']}
                    else:
                        next_url = None

                if counted > 0:
                    media_count = counted
                logger.info(f"[profile_stats] counted media_count={media_count}")
            except Exception as e:
                logger.error(f"[profile_stats] Media count failed: {e}")

        # ── Step 3: Persist ───────────────────────────────────────────────────
        try:
            account.followers_count = followers
            account.media_count = media_count
            account.save(update_fields=['followers_count', 'media_count', 'last_synced'])
        except Exception as e:
            logger.error(f"[profile_stats] DB save failed: {e}")

        return Response({
            'username': username,
            'profile_picture_url': profile_picture_url,
            'followers_count': followers,
            'media_count': media_count,
            'last_synced': account.last_synced,
        })



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
        Disconnect Instagram account:
        1. Revoke the token from Meta/Instagram so the app truly loses access.
        2. Delete the local DB record so it disappears from the UI.
        POST /api/instagram-accounts/{id}/disconnect/
        """
        import requests as req
        instagram_account = self.get_object()
        token = instagram_account.access_token
        connection_method = instagram_account.connection_method

        # ── 1. Revoke token from Meta / Instagram ──────────────────────────
        try:
            if connection_method == 'instagram_platform':
                # Instagram Platform API — revoke via graph.instagram.com
                req.delete(
                    f'https://graph.instagram.com/{instagram_account.instagram_user_id}/permissions',
                    params={'access_token': token},
                    timeout=10,
                )
            else:
                # Facebook Graph API — revoke via graph.facebook.com
                req.delete(
                    f'https://graph.facebook.com/{instagram_account.instagram_user_id}/permissions',
                    params={'access_token': token},
                    timeout=10,
                )
        except Exception as e:
            # Log but don't block the disconnect — local cleanup must still happen
            logger.warning(f"Token revocation failed for @{instagram_account.username}: {e}")

        # ── 2. Delete local record ─────────────────────────────────────────
        username = instagram_account.username
        instagram_account.delete()
        logger.info(f"Disconnected & deleted Instagram account @{username} for user {request.user.id}")

        return Response({'message': 'Instagram account disconnected successfully'})
    
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
    












