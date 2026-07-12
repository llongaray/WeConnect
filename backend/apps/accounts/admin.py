from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django_otp.admin import OTPAdminSite

from .models import AuditLog, Company, SecurityEvent, Team, TeamMembership, User

admin_site = OTPAdminSite(name='admin')


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('code', 'trade_name', 'is_active', 'created_at')
    search_fields = ('code', 'trade_name', 'legal_name', 'cnpj')
    readonly_fields = ('code', 'created_at', 'updated_at')


class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'entity_type', 'entity_label', 'company', 'actor', 'created_at')
    list_filter = ('action', 'entity_type')
    readonly_fields = ('created_at',)


class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'company', 'ip_address', 'username', 'channel_id', 'created_at')
    list_filter = ('event_type', 'company')
    readonly_fields = ('created_at',)


class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_active', 'created_at')
    list_filter = ('company', 'is_active')
    filter_horizontal = ('channels',)


class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('team', 'user', 'role', 'created_at')
    list_filter = ('role',)


class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'company', 'is_staff', 'is_active')
    list_filter = ('role', 'company', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Perfil WeConnect', {'fields': ('role', 'company', 'cpf', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Perfil WeConnect', {'fields': ('role', 'company', 'cpf', 'phone')}),
    )


admin_site.register(Company, CompanyAdmin)
admin_site.register(AuditLog, AuditLogAdmin)
admin_site.register(SecurityEvent, SecurityEventAdmin)
admin_site.register(Team, TeamAdmin)
admin_site.register(TeamMembership, TeamMembershipAdmin)
admin_site.register(User, UserAdmin)
