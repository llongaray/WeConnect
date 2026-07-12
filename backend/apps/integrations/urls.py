from django.urls import path

from .views import (
    AIProviderDetailView,
    AIProviderListView,
    DeepSeekConfigView,
    GenerateFlowView,
)

urlpatterns = [
    path('ai/providers/', AIProviderListView.as_view(), name='ai-providers'),
    path('ai/providers/<str:provider_type>/', AIProviderDetailView.as_view(), name='ai-provider-detail'),
    path('ai/generate-flow/', GenerateFlowView.as_view(), name='ai-generate-flow'),
    path('deepseek/', DeepSeekConfigView.as_view(), name='deepseek-config'),
    path('deepseek/generate-flow/', GenerateFlowView.as_view(), name='deepseek-generate-flow'),
]
