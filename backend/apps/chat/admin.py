from django.contrib import admin

from .models import Contact, Conversation, Message


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'external_id', 'channel', 'updated_at')
    search_fields = ('name', 'phone', 'external_id')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact', 'channel', 'assigned_to', 'status', 'unread_count', 'last_message_at')
    list_filter = ('status', 'assigned_to')
    search_fields = ('contact__name', 'contact__phone')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'direction', 'message_type', 'status', 'created_at')
    list_filter = ('direction', 'message_type', 'status')
