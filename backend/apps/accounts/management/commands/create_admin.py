from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Cria usuário administrador inicial do MoneyConnect'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--password', default='admin123')
        parser.add_argument('--email', default='admin@moneyconnect.local')

    def handle(self, *args, **options):
        username = options['username']
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Usuário "{username}" já existe.'))
            return

        user = User.objects.create_user(
            username=username,
            email=options['email'],
            password=options['password'],
            role=User.Role.ADMIN,
            first_name='Administrador',
        )
        self.stdout.write(self.style.SUCCESS(f'Admin criado: {user.username}'))
