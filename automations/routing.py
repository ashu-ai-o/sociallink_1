from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/automations/$', consumers.AutomationConsumer.as_asgi()),
    re_path(r'ws/automations/(?P<automation_id>[^/]+)/$', consumers.AutomationConsumer.as_asgi()),
    re_path(r'ws/dashboard/$', consumers.DashboardConsumer.as_asgi()),
]