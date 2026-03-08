"""
URL Configuration for Automations API
Maps endpoints to viewsets
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AutomationViewSet,
    AutomationTriggerViewSet,
    ContactViewSet,
    AIProviderViewSet,
    AnalyticsViewSet
)
from .webhooks import instagram_webhook, instagram_platform_webhook
from accounts.views import InstagramAccountViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'automations', AutomationViewSet, basename='automation')
router.register(r'triggers', AutomationTriggerViewSet, basename='trigger')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'ai-providers', AIProviderViewSet, basename='ai-provider')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'instagram-accounts', InstagramAccountViewSet, basename='instagram-account')

urlpatterns = [
    path('', include(router.urls)),
    # Facebook App (1673642834080199) webhook — configure this URL in the Facebook App dashboard
    path('webhooks/instagram/', instagram_webhook, name='instagram_webhook'),
    # Instagram Platform App (1630904951551567) webhook — configure THIS URL in the Instagram Platform App dashboard
    # Both point to the same handler; the handler verifies signatures with both app secrets.
    path('webhooks/instagram-platform/', instagram_platform_webhook, name='instagram_platform_webhook'),
]