from django.contrib import admin
from.models import DailyStats, AutomationPerformance, WebhookLog, SystemEvent, ContactEngagement, AIProviderMetrics
# Register your models here.



admin.site.register(DailyStats)
admin.site.register(AutomationPerformance)
admin.site.register(WebhookLog)
admin.site.register(SystemEvent)
admin.site.register(ContactEngagement)
admin.site.register(AIProviderMetrics)