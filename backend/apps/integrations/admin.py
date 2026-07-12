from django.contrib import admin

from .models import AIProviderConfig, DeepSeekConfig


@admin.register(AIProviderConfig)
class AIProviderConfigAdmin(admin.ModelAdmin):
    list_display = ('company', 'provider_type', 'status', 'is_default', 'last_validated_at', 'updated_at')
    list_filter = ('provider_type', 'status', 'is_default')
    readonly_fields = ('last_validated_at', 'updated_at')


@admin.register(DeepSeekConfig)
class DeepSeekConfigAdmin(admin.ModelAdmin):
    list_display = ('company', 'status', 'last_validated_at', 'updated_at')
    readonly_fields = ('last_validated_at', 'updated_at')
