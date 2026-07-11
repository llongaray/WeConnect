from django.urls import path

from .webhooks import evolution_webhook, meta_webhook

urlpatterns = [
  path('evolution/<int:channel_id>/', evolution_webhook, name='evolution-webhook'),
  path('meta/<int:channel_id>/', meta_webhook, name='meta-webhook'),
]
