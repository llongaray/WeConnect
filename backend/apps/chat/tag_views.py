from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.services.capabilities import is_platform_operator, user_has_capability

from .models import Tag
from .tag_serializers import TagCreateUpdateSerializer, TagSerializer
from .tag_services import funnel_stages_for_company


class TagViewSet(viewsets.ModelViewSet):
  """CRUD de tags de funil por empresa."""

  permission_classes = [IsAuthenticated]
  http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

  def _company_id(self):
    user = self.request.user
    if user.company_id:
      return user.company_id
    if is_platform_operator(user):
      company_id = self.request.query_params.get('company_id')
      if company_id:
        return int(company_id)
    return None

  def get_queryset(self):
    company_id = self._company_id()
    if not company_id:
      return Tag.objects.none()
    qs = Tag.objects.filter(company_id=company_id)
    if self.action == 'list':
      active_only = self.request.query_params.get('active_only', 'true')
      if active_only != 'false':
        qs = qs.filter(is_active=True)
    return qs

  def get_serializer_class(self):
    if self.action in ('create', 'update', 'partial_update'):
      return TagCreateUpdateSerializer
    return TagSerializer

  def _require_manage(self):
    user = self.request.user
    if not (user.is_admin or user.is_gestor):
      raise PermissionDenied('Apenas gestores podem gerenciar tags.')

  def list(self, request, *args, **kwargs):
    if not user_has_capability(request.user, 'access_inbox'):
      raise PermissionDenied()
    return super().list(request, *args, **kwargs)

  def retrieve(self, request, *args, **kwargs):
    if not user_has_capability(request.user, 'access_inbox'):
      raise PermissionDenied()
    return super().retrieve(request, *args, **kwargs)

  def create(self, request, *args, **kwargs):
    self._require_manage()
    company_id = self._company_id()
    if not company_id:
      raise ValidationError({'detail': 'Informe a empresa ativa.'})
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    tag = serializer.save(company_id=company_id)
    return Response(TagSerializer(tag).data, status=status.HTTP_201_CREATED)

  def update(self, request, *args, **kwargs):
    self._require_manage()
    return super().update(request, *args, **kwargs)

  def partial_update(self, request, *args, **kwargs):
    self._require_manage()
    return super().partial_update(request, *args, **kwargs)

  def destroy(self, request, *args, **kwargs):
    self._require_manage()
    return super().destroy(request, *args, **kwargs)

  @action(detail=False, methods=['get'])
  def funnel(self, request):
    if not user_has_capability(request.user, 'access_inbox'):
      raise PermissionDenied()
    company_id = self._company_id()
    if not company_id:
      return Response([])
    return Response(funnel_stages_for_company(company_id))
