from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Cria superuser inicial da plataforma WeConnect'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--password', default='admin123')
        parser.add_argument('--email', default='admin@weconnect.local')

    def handle(self, *args, **options):
        import os

        username = options['username'] or os.getenv('DJANGO_ADMIN_USERNAME', 'admin')
        password = options['password'] or os.getenv('DJANGO_ADMIN_PASSWORD', 'admin123')
        email = options['email'] or os.getenv('DJANGO_ADMIN_EMAIL', 'admin@weconnect.local')

        def ensure_password_ok(raw_password: str) -> None:
            try:
                validate_password(raw_password)
            except ValidationError as exc:
                raise CommandError(f'Senha insegura: {"; ".join(exc.messages)}') from exc

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if user.is_superuser and user.company_id is None:
                self.stdout.write(self.style.WARNING(f'Usuário "{username}" já é superuser da plataforma.'))
                return

            user.is_superuser = True
            user.is_staff = True
            user.company = None
            user.role = User.Role.GESTOR
            if password:
                ensure_password_ok(password)
                user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Usuário "{username}" promovido a superuser da plataforma.'))
            return

        ensure_password_ok(password)
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='Superuser',
            role=User.Role.GESTOR,
        )
        user.company = None
        user.save(update_fields=['company'])
        self.stdout.write(self.style.SUCCESS(f'Superuser criado: {user.username}'))
