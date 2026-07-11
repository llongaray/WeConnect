from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Team, TeamMembership, User


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    filter_horizontal = ('channels',)


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('team', 'user', 'role', 'created_at')
    list_filter = ('role',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Perfil MoneyConnect', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Perfil MoneyConnect', {'fields': ('role',)}),
    )
