from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin

from .models import Channel
from .providers.evolution import extract_qrcode_base64, extract_remote_state
from .providers.factory import get_provider
from .serializers import ChannelCreateSerializer, ChannelSerializer


class ChannelViewSet(viewsets.ModelViewSet):
  """CRUD e conexão de canais WhatsApp."""

  permission_classes = [IsAuthenticated, IsAdmin]
  queryset = Channel.objects.all()

  def get_serializer_class(self):
    if self.action == 'create':
      return ChannelCreateSerializer
    return ChannelSerializer

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

  def perform_create(self, serializer):
    channel = serializer.save()
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
    if instance.is_evolution:
      try:
        get_provider(instance).delete_remote_instance()
      except RuntimeError:
        pass
    instance.delete()

  @action(detail=True, methods=['get'])
  def status_detail(self, request, pk=None):
    channel = self.get_object()
    self._sync_remote_status(channel)
    channel.refresh_from_db()
    return Response(ChannelSerializer(channel).data)

  @action(detail=True, methods=['post'])
  def connect(self, request, pk=None):
    channel = self.get_object()
    force_reset = bool(request.data.get('reset', False))
    provider = get_provider(channel)

    try:
      if channel.is_meta_cloud:
        result = provider.connect()
        remote_state = result.get('state', 'open')
        channel.phone = result.get('phone', '')
        channel.status = Channel.Status.OPEN if remote_state == 'open' else Channel.Status.CLOSE
        channel.qrcode_base64 = ''
        channel.save()
      else:
        # Sem QR salvo: recria sessão limpa para forçar novo pareamento
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

  def _sync_remote_status(self, channel: Channel):
    if channel.is_meta_cloud:
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
