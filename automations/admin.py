from django.contrib import admin
from .models import Automation, AutomationTrigger, Contact, AutomationVariant
from accounts.admin import SoftDeleteAdminMixin
# Register your models here.


@admin.register(Automation)
class AutomationAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'get_user', 'instagram_account', 'is_active', 'trigger_type', 'is_deleted', 'created_at')
    list_filter = ('trigger_type', 'is_active', 'is_deleted', 'created_at')
    search_fields = ('name', 'instagram_account__username', 'instagram_account__user__username')
    actions = ['restore_selected', 'soft_delete_selected']

    def get_user(self, obj):
        return obj.instagram_account.user
    get_user.short_description = 'User'

admin.site.register(AutomationTrigger)
admin.site.register(Contact)
admin.site.register(AutomationVariant)
