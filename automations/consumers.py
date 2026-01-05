import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from .models import Automation, AutomationTrigger, InstagramAccount
from .serializers import AutomationSerializer, AutomationTriggerSerializer

class AutomationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time automation updates
    Handles 1000+ concurrent connections per instance
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create user-specific channel group
        self.user_group = f'user_{self.user.id}'
        
        # Join user group
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        await self.send_automations_list()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'get_automations':
                await self.send_automations_list()
            elif action == 'toggle_automation':
                automation_id = data.get('automation_id')
                await self.toggle_automation(automation_id)
            elif action == 'subscribe_automation':
                automation_id = data.get('automation_id')
                await self.subscribe_to_automation(automation_id)
        
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON')
    
    @database_sync_to_async
    def get_user_automations(self):
        """Get user's automations (async DB access)"""
        automations = Automation.objects.filter(
            instagram_account__user=self.user
        ).select_related('instagram_account')
        return list(automations)
    
    async def send_automations_list(self):
        """Send list of automations to client"""
        automations = await self.get_user_automations()
        
        # Serialize in async context
        automations_data = await database_sync_to_async(
            lambda: [AutomationSerializer(a).data for a in automations]
        )()
        
        await self.send(text_data=json.dumps({
            'type': 'automations_list',
            'data': automations_data
        }))
    
    @database_sync_to_async
    def toggle_automation_db(self, automation_id):
        """Toggle automation status (async DB access)"""
        automation = Automation.objects.get(
            id=automation_id,
            instagram_account__user=self.user
        )
        automation.is_active = not automation.is_active
        automation.save()
        return automation
    
    async def toggle_automation(self, automation_id):
        """Toggle automation and notify"""
        try:
            automation = await self.toggle_automation_db(automation_id)
            
            # Broadcast to all user's connections
            await self.channel_layer.group_send(
                self.user_group,
                {
                    'type': 'automation_updated',
                    'automation_id': str(automation.id),
                    'is_active': automation.is_active
                }
            )
        except Exception as e:
            await self.send_error(str(e))
    
    async def subscribe_to_automation(self, automation_id):
        """Subscribe to specific automation updates"""
        automation_group = f'automation_{automation_id}'
        await self.channel_layer.group_add(
            automation_group,
            self.channel_name
        )
    
    # Event handlers
    async def automation_updated(self, event):
        """Send automation update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'automation_updated',
            'automation_id': event['automation_id'],
            'is_active': event['is_active']
        }))
    
    async def automation_triggered(self, event):
        """Notify when automation is triggered"""
        await self.send(text_data=json.dumps({
            'type': 'automation_triggered',
            'automation_id': event['automation_id'],
            'trigger_data': event['trigger_data']
        }))
    
    async def dm_sent(self, event):
        """Notify when DM is sent"""
        await self.send(text_data=json.dumps({
            'type': 'dm_sent',
            'automation_id': event['automation_id'],
            'recipient': event['recipient'],
            'status': event['status']
        }))
    
    async def send_error(self, message):
        """Send error message"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))


class DashboardConsumer(AsyncWebsocketConsumer):
    """Real-time dashboard updates"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.dashboard_group = f'dashboard_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.dashboard_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Start sending real-time stats
        asyncio.create_task(self.send_stats_periodically())
    
    async def disconnect(self, close_code):
        if hasattr(self, 'dashboard_group'):
            await self.channel_layer.group_discard(
                self.dashboard_group,
                self.channel_name
            )
    
    async def send_stats_periodically(self):
        """Send dashboard stats every 5 seconds"""
        while True:
            try:
                stats = await self.get_dashboard_stats()
                await self.send(text_data=json.dumps({
                    'type': 'stats_update',
                    'data': stats
                }))
                await asyncio.sleep(5)
            except Exception as e:
                break
    
    @database_sync_to_async
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        
        automations = Automation.objects.filter(
            instagram_account__user=self.user
        )
        
        stats = {
            'total_automations': automations.count(),
            'active_automations': automations.filter(is_active=True).count(),
            'total_dms_sent': sum(a.total_dms_sent for a in automations),
            'total_triggers': sum(a.total_triggers for a in automations),
            'today_triggers': AutomationTrigger.objects.filter(
                automation__instagram_account__user=self.user,
                created_at__date=today
            ).count(),
        }
        
        return stats
