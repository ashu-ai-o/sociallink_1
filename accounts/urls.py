"""
URL patterns for user authentication
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    CompleteOnboardingView, OnboardingStepView, EmailHistoryView, EmailPreferencesView, EmailTrackingView, NotificationPreferencesView, RegisterView, LoginView, LogoutView, RequestForgotPasswordOTPView, UserProfileView,
    RequestPasswordChangeOTPView, UserSearchView, VerifyForgotPasswordOTPView, VerifyOTPAndChangePasswordView, DeleteAccountView, PasswordResetRequestView, PasswordResetConfirmView,
    EmailVerificationView, ResendVerificationEmailView, GoogleAuthView, VerifyTokenView,
    FeedbackView, FeedbackListView, CheckUsernameView,
    instagram_oauth_initiate, instagram_oauth_callback,
    instagram_platform_oauth_initiate, instagram_platform_oauth_callback
    )

from .views import (
    TwoFactorSetupView,

    TwoFactorVerifySetupView,
    TwoFactorVerifyLoginView,
    TwoFactorDisableView,
    TwoFactorBackupCodesView,
    TwoFactorRegenerateBackupCodesView,
    TwoFactorStatusView,
    LogoutAllDevicesView,
    LogoutSpecificDeviceView,
    EnterpriseContactView
)


from . import session_api
from . import cookie_consent_api  

app_name = 'users'
 
urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('check-username/', CheckUsernameView.as_view(), name='check_username'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout-all-devices/', LogoutAllDevicesView.as_view(), name='logout-all-devices'),
    path('logout-device/<uuid:session_id>/', LogoutSpecificDeviceView.as_view(), name='logout-specific-device'),

    # JWT Token Management
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # User profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('complete-onboarding/', CompleteOnboardingView.as_view(), name='complete_onboarding'),
    path('onboarding-step/', OnboardingStepView.as_view(), name='onboarding_step'),

    # Password management - OTP-based password change
    path('request-password-change-otp/', RequestPasswordChangeOTPView.as_view(), name='request_password_change_otp'),
    path('verify-otp-and-change-password/', VerifyOTPAndChangePasswordView.as_view(), name='verify_otp_and_change_password'),

    # Forgot password - OTP-based reset
    path('forgot-password/', RequestForgotPasswordOTPView.as_view(), name='forgot_password'),
    path('forgot-password/verify/', VerifyForgotPasswordOTPView.as_view(), name='forgot_password_verify'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # Email verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),

    # Social authentication
    path('google/', GoogleAuthView.as_view(), name='google_auth'),

    # Facebook Graph API (Legacy Meta Login)
    path('instagram/oauth/', instagram_oauth_initiate, name='instagram_oauth_initiate'),
    path('instagram/callback/', instagram_oauth_callback, name='instagram_oauth_callback'),

    # Instagram Platform API (Direct Login)
    path('instagram-direct/oauth/', instagram_platform_oauth_initiate, name='instagram_platform_oauth_initiate'),
    path('instagram-direct/callback/', instagram_platform_oauth_callback, name='instagram_platform_oauth_callback'),
    
   
    # Token verification endpoint
    path('verify-token/', VerifyTokenView.as_view(), name='verify_token'),
    # ========================================================================

   

  
    # Email Preferences
    path('email-preferences/', EmailPreferencesView.as_view(), name='email_preferences'),
    path('notification-preferences/', NotificationPreferencesView.as_view(), name='notification_preferences'),
    path('email-history/', EmailHistoryView.as_view(), name='email_history'),
    
    # Email Tracking (public)
    path('track/email/<uuid:email_id>/<str:action>/', EmailTrackingView.as_view(), name='email_tracking'),


    #  Enterprise contact
    path('contact/enterprise/', EnterpriseContactView.as_view(), name='enterprise_contact'),



    # Two-Factor Authentication (NEW)
    path('2fa/setup/', TwoFactorSetupView.as_view(), name='2fa-setup'),
    path('2fa/verify-setup/', TwoFactorVerifySetupView.as_view(), name='2fa-verify-setup'),
    path('2fa/verify-login/', TwoFactorVerifyLoginView.as_view(), name='2fa-verify-login'),
    path('2fa/disable/', TwoFactorDisableView.as_view(), name='2fa-disable'),
    path('2fa/status/', TwoFactorStatusView.as_view(), name='2fa-status'),
    path('2fa/backup-codes/', TwoFactorBackupCodesView.as_view(), name='2fa-backup-codes'),
    path('2fa/regenerate-backup/', TwoFactorRegenerateBackupCodesView.as_view(), name='2fa-regenerate-backup'),


     # ========================================================================
    # SESSION TRACKING & ANALYTICS
    # ========================================================================

    # Get user's browsing sessions
    path('sessions/my-sessions/', session_api.get_my_sessions, name='my_sessions'),

    # Get detailed session information
    path('sessions/<uuid:session_id>/', session_api.get_session_details, name='session_details'),

    # # Get session analytics
    # path('sessions/analytics/', session_api.get_session_analytics, name='session_analytics'),

    # # Get user events history
    # path('sessions/events/', session_api.get_my_events, name='my_events'),

    # End a specific session
    path('sessions/<uuid:session_id>/end/', session_api.end_session, name='end_session'),

    # Track custom event from frontend
    path('sessions/track-event/', session_api.track_custom_event, name='track_custom_event'),



    #  ADD COOKIE CONSENT ROUTES:
    path('cookie-consent/sync/', cookie_consent_api.sync_cookie_preferences),
    path('cookie-consent/preferences/', cookie_consent_api.get_cookie_preferences),
    path('cookie-consent/track-anonymous/', cookie_consent_api.track_anonymous_consent),
    path('cookie-consent/analytics/', cookie_consent_api.get_consent_analytics),
    path('cookie-consent/history/<int:user_id>/', cookie_consent_api.get_user_consent_history),


    # Feedback
    path('feedback/', FeedbackView.as_view(), name='feedback_submit'),
    path('feedback/mine/', FeedbackListView.as_view(), name='feedback_list'),

   ]