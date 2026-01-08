"""
URL Configuration for Accounts and Authentication
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    PasswordChangeView,
    UserProfileView,
    UserViewSet,
    InstagramAccountViewSet
)

# Create router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'instagram-accounts', InstagramAccountViewSet, basename='instagram-account')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', UserLoginView.as_view(), name='login'),
    path('auth/logout/', UserLogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    
    # Router URLs
    path('', include(router.urls)),
]