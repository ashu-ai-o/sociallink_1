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