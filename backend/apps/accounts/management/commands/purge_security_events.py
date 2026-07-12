from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import SecurityEvent


class Command(BaseCommand):
    help = 'Remove eventos de segurança antigos'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=90)

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - timezone.timedelta(days=days)
        deleted, _ = SecurityEvent.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f'Removidos {deleted} evento(s) anteriores a {days} dias.'))
