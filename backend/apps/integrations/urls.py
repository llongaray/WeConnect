from django.urls import path

from .views import DeepSeekConfigView, GenerateFlowView

urlpatterns = [
    path('deepseek/', DeepSeekConfigView.as_view(), name='deepseek-config'),
    path('deepseek/generate-flow/', GenerateFlowView.as_view(), name='deepseek-generate-flow'),
]
