from django.contrib import admin

from .models import BotFlow, ConversationBotState


@admin.register(BotFlow)
class BotFlowAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'is_active', 'start_node_id', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'channel__name')


@admin.register(ConversationBotState)
class ConversationBotStateAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'flow', 'current_node_id', 'waiting_for', 'invalid_attempts')
    list_filter = ('waiting_for',)
