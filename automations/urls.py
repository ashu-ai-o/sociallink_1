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

# Create router and register viewsets
router = DefaultRouter()
router.register(r'automations', AutomationViewSet, basename='automation')
router.register(r'triggers', AutomationTriggerViewSet, basename='trigger')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'ai-providers', AIProviderViewSet, basename='ai-provider')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
]