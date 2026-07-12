import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='weconnect.ping')
def ping() -> str:
    """Tarefa de verificação do worker Celery."""
    return 'pong'


@shared_task(
    bind=True,
    name='weconnect.process_chatbot',
    max_retries=3,
    default_retry_delay=30,
)
def process_chatbot(self, conversation_id: int, message_id: int, force_restart: bool = False):
    """Processa fluxo do chatbot fora do ciclo HTTP do webhook."""
    from apps.automation.engine import maybe_process_chatbot
    from apps.chat.models import Conversation, Message

    try:
        conversation = Conversation.objects.select_related('channel', 'channel__company').get(pk=conversation_id)
        message = Message.objects.get(pk=message_id, conversation=conversation)
        maybe_process_chatbot(conversation, message, force_restart=force_restart)
    except (Conversation.DoesNotExist, Message.DoesNotExist) as exc:
        logger.warning('Chatbot ignorado — conversa/mensagem inválida (conv=%s, msg=%s)', conversation_id, message_id)
        return
    except Exception as exc:
        logger.exception('Erro ao processar chatbot (conv=%s, msg=%s)', conversation_id, message_id)
        raise self.retry(exc=exc) from exc


def dispatch_chatbot_processing(conversation_id: int, message_id: int, force_restart: bool = False):
    """Enfileira ou executa o chatbot conforme USE_CELERY."""
    from django.conf import settings

    if settings.USE_CELERY:
        process_chatbot.delay(conversation_id, message_id, force_restart)
        return

    process_chatbot(conversation_id, message_id, force_restart)
