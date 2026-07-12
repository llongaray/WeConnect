from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.mixins import CompanyScopedMixin
from apps.accounts.models import AuditLog
from apps.accounts.permissions import IsGestorOrSuperUser
from apps.accounts.services.capabilities import is_platform_admin
from apps.accounts.services.audit import log_audit
from apps.accounts.services.limits import assert_company_can_add

from .models import Channel
from .providers.evolution import extract_qrcode_base64, extract_remote_state
from .providers.factory import get_provider
from .serializers import ChannelCreateSerializer, ChannelSerializer


class ChannelViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
  """CRUD e conexão de canais WhatsApp."""

  permission_classes = [IsAuthenticated, IsGestorOrSuperUser]
  company_field = 'company'
  http_method_names = ['get', 'post', 'delete', 'head', 'options']

  def get_queryset(self):
    qs = Channel.objects.all()
    qs = self.filter_queryset_by_company(qs)

    if self.action != 'list':
      return qs

    include_inactive = self.request.query_params.get('include_inactive') == 'true'
    include_archived = self.request.query_params.get('include_archived') == 'true'

    if not include_archived:
      qs = qs.filter(is_archived=False)
    if not include_inactive:
      qs = qs.filter(is_active=True)

    return qs

  def get_serializer_class(self):
    if self.action == 'create':
      return ChannelCreateSerializer
    return ChannelSerializer

  def destroy(self, request, *args, **kwargs):
    if not is_platform_admin(request.user):
      raise PermissionDenied('Apenas superuser da plataforma pode excluir canais permanentemente.')
    return super().destroy(request, *args, **kwargs)

  def create(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    self.perform_create(serializer)
    channel = serializer.instance
    channel.refresh_from_db()
    return Response(ChannelSerializer(channel).data, status=status.HTTP_201_CREATED)

  def _fetch_and_save_qrcode(self, channel: Channel, provider, initial_result: dict | None = None):
    """Obtém QR Code da Evolution e salva no canal."""
    qrcode_base64 = extract_qrcode_base64(initial_result or {})
    if not qrcode_base64:
      follow_up = provider._connect_and_wait_qrcode(attempts=12)  # noqa: SLF001
      qrcode_base64 = extract_qrcode_base64(follow_up)
    if qrcode_base64:
      channel.qrcode_base64 = qrcode_base64
      channel.status = Channel.Status.CONNECTING
      channel.save(update_fields=['qrcode_base64', 'status', 'updated_at'])
    return qrcode_base64

  def _safe_disconnect(self, channel: Channel):
    """Desconecta o canal remotamente sem interromper a operação local."""
    try:
      get_provider(channel).disconnect()
    except RuntimeError:
      pass
    channel.status = Channel.Status.CLOSE
    channel.qrcode_base64 = ''
    channel.save(update_fields=['status', 'qrcode_base64', 'updated_at'])

  def perform_create(self, serializer):
    user = self.request.user
    company = user.company if user.is_gestor else serializer.validated_data.get('company')
    if user.is_superuser:
      company = serializer.validated_data.get('company') or self.get_company_scope()
    if not company:
      raise ValidationError({'detail': 'Informe a empresa do canal.'})

    assert_company_can_add(company, 'channel')
    channel = serializer.save(company=company)

    log_audit(
      action=AuditLog.Action.CREATE,
      entity_type='channel',
      entity_id=channel.id,
      entity_label=channel.name,
      actor=user,
      company=company,
      request=self.request,
    )

    if channel.is_evolution:
      try:
        provider = get_provider(channel)
        result = provider.create_remote_instance()
        self._fetch_and_save_qrcode(channel, provider, result)
        if not channel.qrcode_base64:
          channel.status = Channel.Status.CONNECTING
          channel.save(update_fields=['status', 'updated_at'])
      except RuntimeError as exc:
        channel.delete()
        raise ValidationError({'detail': str(exc)}) from exc

  def perform_destroy(self, instance):
    log_audit(
      action=AuditLog.Action.DELETE,
      entity_type='channel',
      entity_id=instance.id,
      entity_label=instance.name,
      actor=self.request.user,
      company=instance.company,
      request=self.request,
    )
    if instance.is_evolution:
      try:
        get_provider(instance).delete_remote_instance()
      except RuntimeError:
        pass
    instance.delete()

  @action(detail=True, methods=['post'])
  def deactivate(self, request, pk=None):
    """Inativa o canal (gestor/superuser). Libera licença e desconecta."""
    channel = self.get_object()
    if channel.is_archived:
      raise ValidationError({'detail': 'Canal arquivado não pode ser inativado. Restaure-o primeiro.'})

    self._safe_disconnect(channel)
    channel.is_active = False
    channel.save(update_fields=['is_active', 'updated_at'])

    log_audit(
      action=AuditLog.Action.STATUS_CHANGE,
      entity_type='channel',
      entity_id=channel.id,
      entity_label=channel.name,
      actor=request.user,
      company=channel.company,
      metadata={'is_active': False},
      request=request,
    )
    return Response(ChannelSerializer(channel).data)

  @action(detail=True, methods=['post'])
  def archive(self, request, pk=None):
    """Arquiva o canal (gestor/superuser). Oculta da operação e libera licença."""
    channel = self.get_object()
    if channel.is_archived:
      return Response(ChannelSerializer(channel).data)

    self._safe_disconnect(channel)
    channel.is_active = False
    channel.is_archived = True
    channel.save(update_fields=['is_active', 'is_archived', 'updated_at'])

    log_audit(
      action=AuditLog.Action.STATUS_CHANGE,
      entity_type='channel',
      entity_id=channel.id,
      entity_label=channel.name,
      actor=request.user,
      company=channel.company,
      metadata={'is_active': False, 'is_archived': True},
      request=request,
    )
    return Response(ChannelSerializer(channel).data)

  @action(detail=True, methods=['post'])
  def restore(self, request, pk=None):
    """Restaura canal arquivado ou reativa canal inativo."""
    channel = self.get_object()
    reactivate = bool(request.data.get('reactivate', True))

    if reactivate and not channel.is_active:
      assert_company_can_add(channel.company, 'channel')

    channel.is_archived = False
    if reactivate:
      channel.is_active = True

    channel.save(update_fields=['is_active', 'is_archived', 'updated_at'])

    log_audit(
      action=AuditLog.Action.STATUS_CHANGE,
      entity_type='channel',
      entity_id=channel.id,
      entity_label=channel.name,
      actor=request.user,
      company=channel.company,
      metadata={'is_active': channel.is_active, 'is_archived': channel.is_archived},
      request=request,
    )
    return Response(ChannelSerializer(channel).data)

  @action(detail=True, methods=['get'])
  def status_detail(self, request, pk=None):
    channel = self.get_object()
    self._sync_remote_status(channel)
    channel.refresh_from_db()
    return Response(ChannelSerializer(channel).data)

  @action(detail=True, methods=['post'])
  def connect(self, request, pk=None):
    channel = self.get_object()
    if not channel.is_active or channel.is_archived:
      raise ValidationError({'detail': 'Canal inativo ou arquivado não pode ser conectado.'})

    force_reset = bool(request.data.get('reset', False))
    provider = get_provider(channel)

    try:
      if channel.is_meta_manual:
        result = provider.connect()
        remote_state = result.get('state', 'open')
        channel.phone = result.get('phone', '')
        channel.status = Channel.Status.OPEN if remote_state == 'open' else Channel.Status.CLOSE
        channel.qrcode_base64 = ''
        channel.save()
      else:
        if not channel.qrcode_base64 and not force_reset:
          force_reset = True

        if force_reset:
          result = provider.connect(force_reset=True)
        elif channel.qrcode_base64:
          result = {}
        else:
          result = provider.connect(force_reset=False)

        qrcode_base64 = extract_qrcode_base64(result)
        if not qrcode_base64 and not channel.qrcode_base64:
          self._fetch_and_save_qrcode(channel, provider, result)
        elif qrcode_base64:
          channel.qrcode_base64 = qrcode_base64
          channel.status = Channel.Status.CONNECTING
          channel.save(update_fields=['qrcode_base64', 'status', 'updated_at'])

        channel.refresh_from_db()
        if not channel.qrcode_base64:
          self._sync_remote_status(channel)

    except RuntimeError as exc:
      return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    channel.refresh_from_db()
    data = ChannelSerializer(channel).data
    if channel.is_evolution and channel.status == Channel.Status.CONNECTING and not channel.qrcode_base64:
      data['detail'] = (
        'Sessão iniciada na Evolution. O QR Code pode levar alguns segundos — '
        'aguarde a atualização automática ou clique em Gerar QR Code novamente. '
        'Se não aparecer, reinicie o container Evolution (versão do WhatsApp Web desatualizada).'
      )
    return Response(data)

  @action(detail=True, methods=['post'])
  def disconnect(self, request, pk=None):
    channel = self.get_object()
    try:
      get_provider(channel).disconnect()
    except RuntimeError as exc:
      return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    channel.status = Channel.Status.CLOSE
    channel.qrcode_base64 = ''
    channel.save(update_fields=['status', 'qrcode_base64', 'updated_at'])
    return Response(ChannelSerializer(channel).data)

  @action(detail=True, methods=['post'], url_path='reveal-credentials')
  def reveal_credentials(self, request, pk=None):
    channel = self.get_object()
    if not channel.is_meta_manual:
      return Response({'detail': 'Canal não possui credenciais Meta.'}, status=status.HTTP_400_BAD_REQUEST)
    from apps.accounts.services.step_up import verify_step_up
    if not verify_step_up(
      request.user,
      password=request.data.get('password', ''),
      totp_code=request.data.get('totp_code', ''),
    ):
      return Response({'detail': 'Confirme sua senha ou código 2FA.'}, status=status.HTTP_403_FORBIDDEN)
    log_audit(
      action=AuditLog.Action.STATUS_CHANGE,
      entity_type='channel',
      entity_id=channel.id,
      entity_label=channel.name,
      actor=request.user,
      company=channel.company,
      metadata={'action': 'reveal_meta_credentials'},
      request=request,
    )
    return Response(channel.credentials)

  @action(detail=True, methods=['post'], url_path='reveal-webhook-secret')
  def reveal_webhook_secret(self, request, pk=None):
    channel = self.get_object()
    if not channel.is_evolution:
      return Response({'detail': 'Disponível apenas para canais Evolution.'}, status=status.HTTP_400_BAD_REQUEST)
    from apps.accounts.services.step_up import verify_step_up
    from apps.whatsapp.providers.factory import get_provider
    if not verify_step_up(
      request.user,
      password=request.data.get('password', ''),
      totp_code=request.data.get('totp_code', ''),
    ):
      return Response({'detail': 'Confirme sua senha ou código 2FA.'}, status=status.HTTP_403_FORBIDDEN)
    secret = channel.ensure_webhook_secret()
    log_audit(
      action=AuditLog.Action.STATUS_CHANGE,
      entity_type='channel',
      entity_id=channel.id,
      entity_label=channel.name,
      actor=request.user,
      company=channel.company,
      metadata={'action': 'reveal_webhook_secret'},
      request=request,
    )
    provider = get_provider(channel)
    return Response({
      'webhook_secret': secret,
      'webhook_url': provider.webhook_url(),
      'webhook_header': 'X-Webhook-Secret',
    })

  def _sync_remote_status(self, channel: Channel):
    if channel.is_meta_manual:
      try:
        result = get_provider(channel).get_status()
        remote_state = result.get('state', '')
        if remote_state == 'open':
          channel.status = Channel.Status.OPEN
          channel.phone = result.get('phone', '')
          channel.qrcode_base64 = ''
        elif remote_state in ('close', 'closed'):
          channel.status = Channel.Status.CLOSE
        channel.save()
      except RuntimeError:
        pass
      return

    try:
      state = get_provider(channel).get_status()
      remote_state = extract_remote_state(state)
      if remote_state == 'open':
        channel.status = Channel.Status.OPEN
        channel.qrcode_base64 = ''
      elif remote_state in ('close', 'closed'):
        channel.status = Channel.Status.CLOSE
      elif remote_state == 'connecting':
        channel.status = Channel.Status.CONNECTING
      channel.save()
    except RuntimeError:
      pass
