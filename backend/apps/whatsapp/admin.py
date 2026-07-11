from django.contrib import admin

from .models import Channel


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
  list_display = ('name', 'channel_type', 'status', 'phone', 'is_active', 'updated_at')
  list_filter = ('channel_type', 'status', 'is_active')
  readonly_fields = ('qrcode_base64', 'webhook_secret', 'created_at', 'updated_at')
