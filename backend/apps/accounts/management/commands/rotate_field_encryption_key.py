from django.core.management.base import BaseCommand

from apps.whatsapp.models import Channel


class Command(BaseCommand):
    help = 'Recriptografa credenciais de canais com a chave FIELD_ENCRYPTION_KEY atual'

    def handle(self, *args, **options):
        updated = 0
        for channel in Channel.objects.all().iterator():
            creds = channel.credentials
            if not creds:
                continue
            channel.credentials = creds
            channel.save(update_fields=['credentials'])
            updated += 1
        if updated == 0:
            self.stdout.write(self.style.WARNING('Nenhum canal com credenciais para rotacionar.'))
            return
        self.stdout.write(self.style.SUCCESS(f'Credenciais recriptografadas em {updated} canal(is).'))
        self.stdout.write('Após validar, remova FIELD_ENCRYPTION_KEY_OLD do ambiente.')
