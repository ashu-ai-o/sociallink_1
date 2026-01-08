from django.shortcuts import render

# Create your views here.
"""
REST API Views for Automations with OpenRouter AI
Provides endpoints for testing and managing AI-enhanced automations
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
import asyncio
from asgiref.sync import async_to_sync

from .models import Automation, AutomationTrigger, Contact
from .serializers import (
    AutomationSerializer, 
    AutomationTriggerSerializer, 
    ContactSerializer
)
from .services.ai_service_async import (
    AIServiceOpenRouter,
    AIServiceOpenRouterSync
)
from .tasks import process_automation_trigger_async


class AutomationViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing automations
    Includes AI enhancement testing
    """
    serializer_class = AutomationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter automations by user's Instagram accounts"""
        return Automation.objects.filter(
            instagram_account__user=self.request.user
        ).select_related('instagram_account')
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """
        Toggle automation on/off
        POST /api/automations/{id}/toggle/
        """
        automation = self.get_object()
        automation.is_active = not automation.is_active
        automation.save()
        
        return Response({
            'id': str(automation.id),
            'name': automation.name,
            'is_active': automation.is_active,
            'message': f"Automation {'activated' if automation.is_active else 'deactivated'}"
        })
    
    @action(detail=True, methods=['post'])
    def test_trigger(self, request, pk=None):
        """
        Test automation trigger manually
        POST /api/automations/{id}/test_trigger/
        
        Body:
        {
            "comment_text": "I want this!",
            "instagram_username": "test_user",
            "instagram_user_id": "123456"
        }
        """
        automation = self.get_object()
        
        # Create test trigger
        trigger = AutomationTrigger.objects.create(
            automation=automation,
            instagram_user_id=request.data.get('instagram_user_id', '999999'),
            instagram_username=request.data.get('instagram_username', 'test_user'),
            comment_text=request.data.get('comment_text', 'Test comment'),
            status='pending'
        )
        
        # Queue for processing
        process_automation_trigger_async.delay(str(trigger.id))
        
        return Response({
            'success': True,
            'trigger_id': str(trigger.id),
            'message': 'Test trigger created and queued for processing',
            'automation': automation.name,
            'will_use_ai': automation.use_ai_enhancement
        })
    
    @action(detail=False, methods=['post'])
    def test_ai_enhancement(self, request):
        """
        Test AI message enhancement without creating automation
        POST /api/automations/test_ai_enhancement/
        
        Body:
        {
            "base_message": "Thanks for your comment!",
            "business_context": "We sell premium coffee",
            "user_comment": "This looks amazing!",
            "username": "coffee_lover"
        }
        """
        # Use synchronous version for REST API
        ai_service = AIServiceOpenRouterSync(
            api_key=settings.OPENROUTER_API_KEY,
            site_url=settings.OPENROUTER_SITE_URL
        )
        
        result = ai_service.enhance_dm_message(
            base_message=request.data.get('base_message', ''),
            business_context=request.data.get('business_context', ''),
            user_comment=request.data.get('user_comment', ''),
            username=request.data.get('username', 'user')
        )
        
        return Response({
            'success': result['success'],
            'original_message': result['original_message'],
            'enhanced_message': result['enhanced_message'],
            'model_used': result.get('model_name', 'N/A'),
            'provider': result.get('provider', 'openrouter'),
            'error': result.get('error')
        })
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """
        Get analytics for specific automation
        GET /api/automations/{id}/analytics/?days=30
        """
        automation = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Q
        
        start_date = timezone.now() - timedelta(days=days)
        
        triggers = AutomationTrigger.objects.filter(
            automation=automation,
            created_at__gte=start_date
        )
        
        analytics = {
            'automation_id': str(automation.id),
            'automation_name': automation.name,
            'period_days': days,
            'total_triggers': triggers.count(),
            'triggers_by_status': {
                'sent': triggers.filter(status='sent').count(),
                'failed': triggers.filter(status='failed').count(),
                'skipped': triggers.filter(status='skipped').count(),
                'pending': triggers.filter(status='pending').count(),
            },
            'ai_enhanced_count': triggers.filter(was_ai_enhanced=True).count(),
            'success_rate': automation.total_dms_sent / automation.total_triggers * 100 
                           if automation.total_triggers > 0 else 0,
            'total_dms_sent': automation.total_dms_sent,
            'total_triggers': automation.total_triggers,
        }
        
        return Response(analytics)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate an automation
        POST /api/automations/{id}/duplicate/
        """
        automation = self.get_object()
        
        # Create copy
        new_automation = Automation.objects.create(
            instagram_account=automation.instagram_account,
            name=f"{automation.name} (Copy)",
            trigger_type=automation.trigger_type,
            trigger_keywords=automation.trigger_keywords,
            trigger_match_type=automation.trigger_match_type,
            target_posts=automation.target_posts,
            dm_message=automation.dm_message,
            dm_buttons=automation.dm_buttons,
            require_follow=automation.require_follow,
            follow_check_message=automation.follow_check_message,
            use_ai_enhancement=automation.use_ai_enhancement,
            ai_context=automation.ai_context,
            max_triggers_per_user=automation.max_triggers_per_user,
            cooldown_minutes=automation.cooldown_minutes,
            is_active=False,  # Start inactive
            priority=automation.priority,
        )
        
        serializer = self.get_serializer(new_automation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AutomationTriggerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for viewing automation triggers
    Read-only - triggers are created automatically
    """
    serializer_class = AutomationTriggerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter triggers by user's automations"""
        return AutomationTrigger.objects.filter(
            automation__instagram_account__user=self.request.user
        ).select_related('automation').order_by('-created_at')


class ContactViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for viewing contacts
    """
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter contacts by user's Instagram accounts"""
        return Contact.objects.filter(
            instagram_account__user=self.request.user
        ).select_related('instagram_account')
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search contacts by username
        GET /api/contacts/search/?q=username
        """
        query = request.query_params.get('q', '')
        contacts = self.get_queryset().filter(
            instagram_username__icontains=query
        )[:20]
        
        serializer = self.get_serializer(contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Export contacts to CSV/XLSX
        GET /api/contacts/export/?format=csv
        """
        format_type = request.query_params.get('format', 'csv')
        
        # This would generate CSV/XLSX file
        # For now, return JSON
        contacts = self.get_queryset()
        serializer = self.get_serializer(contacts, many=True)
        
        return Response({
            'format': format_type,
            'count': contacts.count(),
            'data': serializer.data,
            'message': 'Export functionality - implement with pandas or openpyxl'
        })


class AIProviderViewSet(viewsets.ViewSet):
    """
    API endpoints for testing AI providers
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get status of all AI providers/models
        GET /api/ai-providers/status/
        """
        from .services.ai_service_async import AIServiceOpenRouter
        
        models_info = AIServiceOpenRouter.MODELS
        
        return Response({
            'provider': 'OpenRouter',
            'api_url': settings.OPENROUTER_API_URL,
            'models_configured': len(models_info),
            'models': [
                {
                    'id': m['id'],
                    'name': m['name'],
                    'cost': m['cost'],
                    'speed': m['speed'],
                    'use_case': m['use_case']
                }
                for m in models_info
            ]
        })
    
    @action(detail=False, methods=['post'])
    def test(self, request):
        """
        Test AI provider with custom message
        POST /api/ai-providers/test/
        
        Body:
        {
            "prompt": "Your test prompt",
            "model": "anthropic/claude-3.5-sonnet"  // optional
        }
        """
        ai_service = AIServiceOpenRouterSync(
            api_key=settings.OPENROUTER_API_KEY,
            site_url=settings.OPENROUTER_SITE_URL
        )
        
        prompt = request.data.get('prompt', 'Hello, how are you?')
        model = request.data.get('model')
        
        # Test generation
        import time
        start_time = time.time()
        
        result = ai_service._generate(
            prompt=prompt,
            model=model or ai_service.MODELS[0]['id']
        )
        
        elapsed = time.time() - start_time
        
        return Response({
            'success': result['success'],
            'response': result.get('text', 'N/A'),
            'model': model or ai_service.MODELS[0]['id'],
            'response_time': f"{elapsed:.2f}s",
            'error': result.get('error')
        })


class AnalyticsViewSet(viewsets.ViewSet):
    """
    API endpoints for analytics and dashboard stats
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Get dashboard statistics
        GET /api/analytics/dashboard/?period=30d
        """
        from django.db.models import Sum, Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
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
        
        stats = {
            'period': period,
            'total_automations': automations.count(),
            'active_automations': automations.filter(is_active=True).count(),
            'total_dms_sent': automations.aggregate(
                total=Sum('total_dms_sent')
            )['total'] or 0,
            'total_triggers': triggers.count(),
            'today_triggers': triggers.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'success_rate': (
                triggers.filter(status='sent').count() / triggers.count() * 100
                if triggers.count() > 0 else 0
            ),
            'ai_enhanced_rate': (
                triggers.filter(was_ai_enhanced=True).count() / triggers.count() * 100
                if triggers.count() > 0 else 0
            ),
            'daily_breakdown': self._get_daily_breakdown(triggers, days)
        }
        
        return Response(stats)
    
    def _get_daily_breakdown(self, triggers, days):
        """Get daily breakdown of triggers"""
        from django.utils import timezone
        from datetime import timedelta
        
        breakdown = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=days-i-1)
            day_triggers = triggers.filter(created_at__date=date)
            
            breakdown.append({
                'date': date.isoformat(),
                'triggers': day_triggers.count(),
                'dms_sent': day_triggers.filter(status='sent').count(),
                'ai_enhanced': day_triggers.filter(was_ai_enhanced=True).count()
            })
        
        return breakdown
    
    @action(detail=False, methods=['get'])
    def automations(self, request):
        """
        Get performance metrics for all automations
        GET /api/analytics/automations/
        """
        automations = Automation.objects.filter(
            instagram_account__user=request.user
        )
        
        performance = []
        for automation in automations:
            performance.append({
                'id': str(automation.id),
                'name': automation.name,
                'is_active': automation.is_active,
                'total_triggers': automation.total_triggers,
                'total_dms_sent': automation.total_dms_sent,
                'success_rate': (
                    automation.total_dms_sent / automation.total_triggers * 100
                    if automation.total_triggers > 0 else 0
                ),
                'conversions': automation.total_dms_sent  # Placeholder
            })
        
        return Response({
            'count': len(performance),
            'top_automations': sorted(
                performance, 
                key=lambda x: x['total_dms_sent'], 
                reverse=True
            )[:10]
        })