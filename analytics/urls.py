"""
URL Configuration for Analytics
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DailyStatsViewSet,
    AutomationPerformanceViewSet,
    AIProviderMetricsViewSet,
    ContactEngagementViewSet,
    SystemEventViewSet,
    WebhookLogViewSet,
    DashboardViewSet
)

# Create router
router = DefaultRouter()
router.register(r'daily-stats', DailyStatsViewSet, basename='daily-stats')
router.register(r'automation-performance', AutomationPerformanceViewSet, basename='automation-performance')
router.register(r'ai-metrics', AIProviderMetricsViewSet, basename='ai-metrics')
router.register(r'contact-engagement', ContactEngagementViewSet, basename='contact-engagement')
router.register(r'system-events', SystemEventViewSet, basename='system-events')
router.register(r'webhook-logs', WebhookLogViewSet, basename='webhook-logs')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]