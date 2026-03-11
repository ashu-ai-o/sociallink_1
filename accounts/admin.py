


"""
Admin configuration for users app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from .models import User, InstagramAccount, EmailVerificationToken, PasswordResetToken, Feedback, UserSession, PageVisit, UserEvent, EnterpriseContact

class SoftDeleteAdminMixin:
    """Mixin to provide soft delete support in Django Admin"""
    
    def get_queryset(self, request):
        return self.model.all_objects.all()

    @admin.action(description='Restore selected items')
    def restore_selected(self, request, queryset):
        count = 0
        for obj in queryset.filter(is_deleted=True):
            obj.restore()
            count += 1
        self.message_user(request, f'Restored {count} item(s)')

    @admin.action(description='Soft delete selected items')
    def soft_delete_selected(self, request, queryset):
        count = 0
        for obj in queryset.filter(is_deleted=False):
            obj.delete()
            count += 1
        self.message_user(request, f'Soft deleted {count} item(s)')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_name', 'get_user_email', 'category', 'title', 'priority', 'status', 'rating', 'created_at']
    list_filter = ['category', 'priority', 'status', 'created_at']
    search_fields = ['title', 'message', 'user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'page_url', 'user_agent']

    fieldsets = (
        ('Submission', {
            'fields': ('id', 'user', 'category', 'title', 'message', 'rating')
        }),
        ('Status', {
            'fields': ('priority', 'status', 'admin_notes'),
        }),
        ('Meta', {
            'fields': ('page_url', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.username
        return obj.name or '—'
    get_user_name.short_description = 'Username'
    get_user_name.admin_order_field = 'user__username'

    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email
        return obj.email or '—'
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'

    def save_model(self, request, obj, form, change):
        """Auto-populate email/name from the linked user if present."""
        if obj.user:
            obj.email = obj.user.email
            obj.name = obj.user.username
        super().save_model(request, obj, form, change)




@admin.register(InstagramAccount)
class InstagramAccountAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ('username', 'instagram_user_id', 'followers_count', 'is_active', 'is_deleted', 'created_at')
    list_filter = ('is_active', 'is_deleted', 'connection_method', 'created_at')
    search_fields = ('username', 'instagram_user_id', 'full_name')
    actions = ['restore_selected', 'soft_delete_selected']

@admin.register(User)
class UserAdmin(SoftDeleteAdminMixin, BaseUserAdmin):
    """Enhanced admin for User model with 2FA fields"""
    list_display = (
        'email', 'username', 'first_name', 'last_name',
        'get_auth_method', # Show if Google or Email
        'is_email_verified', 'two_factor_enabled',
        'is_staff', 'created_at',
    )
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'is_deleted',
        'is_email_verified', 'two_factor_enabled',
        'created_at'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'get_auth_source', 'bio', 'profile_picture', 'notification_preferences', 'email_preferences')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Email Verification', {
            'fields': ('is_email_verified',)
        }),
        ('Two-Factor Authentication', {  # NEW SECTION
            'fields': (
                'two_factor_enabled',
                'two_factor_secret',
                'backup_codes',
                'two_factor_enabled_at'
            ),
            'classes': ('collapse',),  # Collapsed by default
        }),

        ('cookies', {
            'fields': ('cookie_consent_date','cookie_consent_given', 'cookie_preferences'),
            'classes': ('collapse',),  # Collapsed by default
        }),

        ('OAuth', {
            'fields': ('google_id',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'last_login_at', 'date_joined', 'created_at', 'updated_at')
        }),
    )

    readonly_fields = (
        'created_at', 'updated_at', 'last_login_at',
        'get_auth_source',
        'two_factor_secret', 'backup_codes', 'two_factor_enabled_at'
    )

    # Helper methods for better display
    def get_auth_method(self, obj):
        if obj.google_id:
            return "Google OAuth"
        return "Email/Password"
    get_auth_method.short_description = 'Auth Method'

    def get_auth_source(self, obj):
        if obj.google_id:
            return "User authenticated via Google (No local password required)"
        return "Standard Email/Password"
    get_auth_source.short_description = 'Authentication Source'

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related()
    
    # Custom actions
    actions = ['disable_2fa_for_users', 'restore_selected', 'soft_delete_selected']
    
    @admin.action(description='Disable 2FA for selected users')
    def disable_2fa_for_users(self, request, queryset):
        """Admin action to disable 2FA for multiple users"""
        count = queryset.filter(two_factor_enabled=True).update(
            two_factor_enabled=False,
            two_factor_secret=None,
            backup_codes=[],
            two_factor_enabled_at=None
        )
        self.message_user(request, f'2FA disabled for {count} user(s)')


        

@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin for Email Verification Tokens"""
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'user__username', 'token')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin for Password Reset Tokens"""
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'user__username', 'token')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

















from .models import UserSession, PageVisit, UserEvent

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'device_type', 'os_name', 'browser_name', 'country', 'created_at', 'is_active']
    list_filter = ['device_type', 'os_name', 'browser_name', 'country_code', 'is_active', 'threat_level']
    search_fields = ['user__username', 'ip_address', 'city', 'country']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User & Session', {
            'fields': ('user', 'session_token', 'is_active', 'login_method')
        }),
        ('Network', {
            'fields': ('ip_address', 'ip_version', 'proxy_ip', 'isp', 'asn')
        }),
        ('Location', {
            'fields': ('country', 'city', 'region', 'postal_code', 'latitude', 'longitude', 'timezone')
        }),
        ('Device', {
            'fields': ('device_type', 'device_brand', 'device_model', 'screen_resolution')
        }),
        ('Browser', {
            'fields': ('browser_name', 'browser_version', 'browser_language')
        }),
        ('OS', {
            'fields': ('os_name', 'os_version')
        }),
        ('Security', {
            'fields': ('is_vpn', 'is_proxy', 'is_tor', 'threat_level')
        }),
        ('Activity', {
            'fields': ('page_views', 'actions_count', 'duration_seconds', 'last_activity')
        }),
    )

@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ['user', 'path', 'http_method', 'time_on_page_seconds', 'visited_at']
    list_filter = ['http_method', 'is_internal_referrer']
    search_fields = ['user__username', 'path', 'url']

@admin.register(UserEvent)
class UserEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_type', 'event_name', 'success', 'created_at']
    list_filter = ['event_type', 'event_category', 'success']
    search_fields = ['user__username', 'event_name', 'event_category']


















from .models import EnterpriseContact

@admin.register(EnterpriseContact)
class EnterpriseContactAdmin(admin.ModelAdmin):
    """
    Admin interface for managing enterprise contacts
    """
    list_display = [
        'get_full_name',
        'email',
        'company_name',
        'company_size',
        'status',
        'assigned_to',
        'created_at',
        'contacted_at'
    ]
    
    list_filter = [
        'status',
        'company_size',
        'source',
        'created_at',
        'assigned_to'
    ]
    
    search_fields = [
        'first_name',
        'last_name',
        'email',
        'company_name',
        'phone',
        'project_details'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'ip_address',
        'user_agent'
    ]
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'phone',
                'job_title'
            )
        }),
        ('Company Information', {
            'fields': (
                'company_name',
                'company_size'
            )
        }),
        ('Project Details', {
            'fields': (
                'project_details',
                'budget_range',
                'timeline'
            )
        }),
        ('Lead Management', {
            'fields': (
                'status',
                'assigned_to',
                'internal_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'id',
                'source',
                'ip_address',
                'user_agent',
                'created_at',
                'updated_at',
                'contacted_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    # Actions
    actions = [
        'mark_as_contacted',
        'mark_as_qualified',
        'mark_as_converted'
    ]
    
    def mark_as_contacted(self, request, queryset):
        """Mark selected contacts as contacted"""
        updated = queryset.update(
            status='contacted',
            contacted_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} contact(s) marked as contacted.'
        )
    mark_as_contacted.short_description = "Mark as Contacted"
    
    def mark_as_qualified(self, request, queryset):
        """Mark selected contacts as qualified"""
        updated = queryset.update(status='qualified')
        self.message_user(
            request,
            f'{updated} contact(s) marked as qualified.'
        )
    mark_as_qualified.short_description = "Mark as Qualified"
    
    def mark_as_converted(self, request, queryset):
        """Mark selected contacts as converted"""
        updated = queryset.update(status='converted')
        self.message_user(
            request,
            f'{updated} contact(s) marked as converted.'
        )
    mark_as_converted.short_description = "Mark as Converted"
    
    # Custom columns
    def get_full_name(self, obj):
        """Display full name"""
        return obj.get_full_name()
    get_full_name.short_description = 'Name'
    get_full_name.admin_order_field = 'first_name'