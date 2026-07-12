from django.urls import path

from .webhooks import evolution_webhook, meta_messaging_webhook, meta_webhook

urlpatterns = [
  path('evolution/<int:channel_id>/', evolution_webhook, name='evolution-webhook'),
  path('meta/<int:channel_id>/', meta_webhook, name='meta-webhook'),
  path('meta-messaging/<int:channel_id>/', meta_messaging_webhook, name='meta-messaging-webhook'),
]
