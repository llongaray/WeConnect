from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls_auth')),
    path('api/v1/', include('apps.chat.urls')),
    path('api/v1/', include('apps.whatsapp.urls')),
    path('api/v1/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.automation.urls')),
    path('api/v1/', include('apps.integrations.urls')),
    path('api/webhooks/', include('apps.whatsapp.urls_webhooks')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
