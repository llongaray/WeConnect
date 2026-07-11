from django.contrib import admin

from .models import DeepSeekConfig


@admin.register(DeepSeekConfig)
class DeepSeekConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'last_validated_at', 'updated_at')
    readonly_fields = ('last_validated_at', 'updated_at')
