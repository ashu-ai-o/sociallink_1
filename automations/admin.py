from django.contrib import admin
from .models import Automation, AutomationTrigger, Contact, AutomationVariant
# Register your models here.


admin.site.register(Automation)
admin.site.register(AutomationTrigger)
admin.site.register(Contact)
admin.site.register(AutomationVariant)
