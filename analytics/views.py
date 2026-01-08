from django.shortcuts import render

# Create your views here.
"""
Analytics Views - Comprehensive analytics and reporting endpoints
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Count, Q, F
from django.utils import timezone
from datetime import timedelta

from .models import (
    DailyStats,
    AutomationPerformance,
    AIProviderMetrics,
    ContactEngagement,
    SystemEvent,
    WebhookLog
)
from .serializers import (
    DailyStatsSerializer,
    AutomationPerformanceSerializer,
    AIProviderMetricsSerializer,
    ContactEngagementSerializer,
    SystemEventSerializer,
    WebhookLogSerializer,
    DashboardOverviewSerializer,
    AutomationAnalyticsSerializer,
    AIUsageSerializer
)


class DailyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View daily statistics
    GET /api/analytics/daily-stats/
    """
    serializer_class = DailyStatsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by current user"""
        return DailyStats.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def current_month(self, request):
        """
        Get current month statistics
        GET /api/analytics/daily-stats/current_month/
        """
        today = timezone.now().date()
        first_day = today.replace(day=1)
        
        stats = self.get_queryset().filter(
            date__gte=first_day,
            date__lte=today
        )
        
        serializer = self.get_serializer(stats, many=True)
        return Response(serializer.data)


class AutomationPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View automation performance metrics
    GET /api/analytics/automation-performance/
    """
    serializer_class = AutomationPerformanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user's automations"""
        return AutomationPerformance.objects.filter(
            automation__instagram_account__user=self.request.user
        ).select_related('automation')


class AIProviderMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View AI provider usage and performance
    GET /api/analytics/ai-metrics/
    """
    serializer_class = AIProviderMetricsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by current user"""
        return AIProviderMetrics.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def usage_summary(self, request):
        """
        Get AI usage summary
        GET /api/analytics/ai-metrics/usage_summary/?days=30
        """
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        metrics = self.get_queryset().filter(date__gte=start_date)
        
        # Aggregate by model
        models_breakdown = metrics.values('model_used').annotate(
            total_requests=Sum('total_requests'),
            successful_requests=Sum('successful_requests'),
            failed_requests=Sum('failed_requests'),
            total_tokens=Sum('total_tokens_used'),
            total_cost=Sum('estimated_cost'),
            avg_response_time=Avg('avg_response_time')
        ).order_by('-total_requests')
        
        summary = {
            'period': f'{days}d',
            'total_requests': metrics.aggregate(Sum('total_requests'))['total_requests__sum'] or 0,
            'successful_requests': metrics.aggregate(Sum('successful_requests'))['successful_requests__sum'] or 0,
            'failed_requests': metrics.aggregate(Sum('failed_requests'))['failed_requests__sum'] or 0,
            'models_breakdown': list(models_breakdown),
            'total_cost': float(metrics.aggregate(Sum('estimated_cost'))['estimated_cost__sum'] or 0),
            'avg_response_time': float(metrics.aggregate(Avg('avg_response_time'))['avg_response_time__avg'] or 0)
        }
        
        serializer = AIUsageSerializer(summary)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def cost_breakdown(self, request):
        """
        Get cost breakdown by model
        GET /api/analytics/ai-metrics/cost_breakdown/?days=30
        """
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        costs = self.get_queryset().filter(date__gte=start_date).values(
            'model_used'
        ).annotate(
            total_cost=Sum('estimated_cost'),
            total_requests=Sum('total_requests')
        ).order_by('-total_cost')
        
        return Response({
            'period': f'{days}d',
            'breakdown': list(costs),
            'total': float(sum(c['total_cost'] for c in costs))
        })


class ContactEngagementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View contact engagement metrics
    GET /api/analytics/contact-engagement/
    """
    serializer_class = ContactEngagementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user's contacts"""
        return ContactEngagement.objects.filter(
            contact__instagram_account__user=self.request.user
        ).select_related('contact')


class SystemEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View system events and logs
    GET /api/analytics/system-events/
    """
    serializer_class = SystemEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by current user"""
        queryset = SystemEvent.objects.filter(user=self.request.user)
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def recent_errors(self, request):
        """
        Get recent error events
        GET /api/analytics/system-events/recent_errors/?limit=10
        """
        limit = int(request.query_params.get('limit', 10))
        
        errors = self.get_queryset().filter(
            severity__in=['error', 'critical']
        )[:limit]
        
        serializer = self.get_serializer(errors, many=True)
        return Response(serializer.data)


class WebhookLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View webhook logs
    GET /api/analytics/webhook-logs/
    """
    serializer_class = WebhookLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user's Instagram accounts"""
        return WebhookLog.objects.filter(
            instagram_account__user=self.request.user
        ).select_related('instagram_account')
    
    @action(detail=False, methods=['get'])
    def unprocessed(self, request):
        """
        Get unprocessed webhooks
        GET /api/analytics/webhook-logs/unprocessed/
        """
        unprocessed = self.get_queryset().filter(processed=False)
        serializer = self.get_serializer(unprocessed, many=True)
        return Response(serializer.data)


class DashboardViewSet(viewsets.ViewSet):
    """
    Dashboard overview and statistics
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Get dashboard overview
        GET /api/analytics/dashboard/overview/?period=30d
        """
        from automations.models import Automation, AutomationTrigger
        
        period = request.query_params.get('period', '30d')
        days = int(period.replace('d', ''))
        start_date = timezone.now() - timedelta(days=days)
        
        automations = Automation.objects.filter(
            instagram_account__user=request.user
        )
        
        triggers = AutomationTrigger.objects.filter(
            automation__instagram_account__user=request.user,
            created_at__gte=start_date
        )
        
        # Daily breakdown
        daily_breakdown = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=days-i-1)
            day_triggers = triggers.filter(created_at__date=date)
            
            daily_breakdown.append({
                'date': date.isoformat(),
                'triggers': day_triggers.count(),
                'dms_sent': day_triggers.filter(status='sent').count(),
                'ai_enhanced': day_triggers.filter(was_ai_enhanced=True).count()
            })
        
        stats = {
            'period': period,
            'total_automations': automations.count(),
            'active_automations': automations.filter(is_active=True).count(),
            'total_dms_sent': automations.aggregate(Sum('total_dms_sent'))['total_dms_sent__sum'] or 0,
            'total_triggers': triggers.count(),
            'today_triggers': triggers.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'success_rate': (
                triggers.filter(status='sent').count() / triggers.count() * 100
                if triggers.count() > 0 else 0
            ),
            'ai_enhancement_rate': (
                triggers.filter(was_ai_enhanced=True).count() / triggers.count() * 100
                if triggers.count() > 0 else 0
            ),
            'daily_breakdown': daily_breakdown
        }
        
        serializer = DashboardOverviewSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """
        Get top performing automations
        GET /api/analytics/dashboard/top_performers/?limit=10
        """
        from automations.models import Automation
        
        limit = int(request.query_params.get('limit', 10))
        
        automations = Automation.objects.filter(
            instagram_account__user=request.user
        ).annotate(
            success_rate=F('total_dms_sent') * 100.0 / F('total_triggers')
        ).order_by('-total_dms_sent')[:limit]
        
        performers = []
        for automation in automations:
            performers.append({
                'id': automation.id,
                'name': automation.name,
                'total_triggers': automation.total_triggers,
                'success_rate': automation.success_rate if automation.total_triggers > 0 else 0,
                'total_dms_sent': automation.total_dms_sent
            })
        
        return Response({
            'count': len(performers),
            'results': performers
        })
    
    @action(detail=False, methods=['get'])
    def realtime_stats(self, request):
        """
        Get real-time statistics (for WebSocket alternative)
        GET /api/analytics/dashboard/realtime_stats/
        """
        from automations.models import Automation, AutomationTrigger
        from django.core.cache import cache
        
        today = timezone.now().date()
        
        stats = {
            'timestamp': timezone.now().isoformat(),
            'active_automations': Automation.objects.filter(
                instagram_account__user=request.user,
                is_active=True
            ).count(),
            'triggers_today': AutomationTrigger.objects.filter(
                automation__instagram_account__user=request.user,
                created_at__date=today
            ).count(),
            'dms_sent_today': AutomationTrigger.objects.filter(
                automation__instagram_account__user=request.user,
                created_at__date=today,
                status='sent'
            ).count(),
            'current_queue_size': 0,  # Would need Celery inspect
            'ai_requests_today': AIProviderMetrics.objects.filter(
                user=request.user,
                date=today
            ).aggregate(Sum('total_requests'))['total_requests__sum'] or 0
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def export_report(self, request):
        """
        Export analytics report
        GET /api/analytics/dashboard/export_report/?format=csv&period=30d
        """
        format_type = request.query_params.get('format', 'json')
        period = request.query_params.get('period', '30d')
        
        # Get overview data
        overview_response = self.overview(request)
        
        if format_type == 'json':
            return overview_response
        elif format_type == 'csv':
            # TODO: Implement CSV export
            return Response({
                'message': 'CSV export not yet implemented',
                'data': overview_response.data
            })
        else:
            return Response({
                'error': 'Unsupported format'
            }, status=status.HTTP_400_BAD_REQUEST)