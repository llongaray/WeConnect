import hashlib
import hmac
import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import Company, SecurityEvent, User
from apps.accounts.totp_service import create_pending_setup
from apps.chat.models import Contact, Conversation
from apps.whatsapp.models import Channel

User = get_user_model()


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(
            legal_name='Empresa A LTDA',
            trade_name='Empresa A',
            cnpj='11.111.111/0001-11',
        )
        self.company_b = Company.objects.create(
            legal_name='Empresa B LTDA',
            trade_name='Empresa B',
            cnpj='22.222.222/0001-22',
        )
        self.gestor_a = User.objects.create_user(
            username='gestor_a',
            password='SenhaSegura1!',
            role=User.Role.GESTOR,
            company=self.company_a,
        )
        self.gestor_b = User.objects.create_user(
            username='gestor_b',
            password='SenhaSegura1!',
            role=User.Role.GESTOR,
            company=self.company_b,
        )
        self.channel_a = Channel.objects.create(
            name='Canal A',
            channel_type=Channel.ChannelType.EVOLUTION_NORMAL,
            company=self.company_a,
        )
        self.channel_b = Channel.objects.create(
            name='Canal B',
            channel_type=Channel.ChannelType.EVOLUTION_NORMAL,
            company=self.company_b,
        )

    def _auth(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_gestor_nao_lista_canais_de_outra_empresa(self):
        client = self._auth(self.gestor_a)
        response = client.get('/api/v1/channels/')
        self.assertEqual(response.status_code, 200)
        ids = {item['id'] for item in response.data.get('results', response.data)}
        self.assertIn(self.channel_a.id, ids)
        self.assertNotIn(self.channel_b.id, ids)

    def test_gestor_nao_acessa_canal_de_outra_empresa(self):
        client = self._auth(self.gestor_a)
        response = client.get(f'/api/v1/channels/{self.channel_b.id}/')
        self.assertEqual(response.status_code, 404)

    def test_gestor_nao_lista_usuarios_de_outra_empresa(self):
        client = self._auth(self.gestor_a)
        response = client.get('/api/v1/users/', {'company_id': self.company_a.id})
        self.assertEqual(response.status_code, 200)
        usernames = {item['username'] for item in response.data.get('results', response.data)}
        self.assertIn('gestor_a', usernames)
        self.assertNotIn('gestor_b', usernames)

    def test_gestor_nao_vincula_canal_de_outra_empresa_na_equipe(self):
        client = self._auth(self.gestor_a)
        response = client.post(
            '/api/v1/teams/',
            {
                'name': 'Equipe Cross',
                'channel_ids': [self.channel_b.id],
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_gestor_nao_cria_botflow_em_canal_de_outra_empresa(self):
        client = self._auth(self.gestor_a)
        response = client.post(
            '/api/v1/bot-flows/',
            {
                'channel': self.channel_b.id,
                'name': 'Fluxo inválido',
                'definition': {'nodes': []},
                'start_node_id': '',
            },
            format='json',
        )
        self.assertIn(response.status_code, (400, 404))

    def test_superuser_exige_company_id_em_canais(self):
        superuser = User.objects.create_superuser(
            username='admin_plat',
            password='SenhaSegura1!',
        )
        client = self._auth(superuser)
        response = client.get('/api/v1/channels/')
        self.assertEqual(response.status_code, 400)


class TotpSetupGateTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            legal_name='Empresa TOTP LTDA',
            trade_name='Empresa TOTP',
            cnpj='33.333.333/0001-33',
        )
        self.gestor = User.objects.create_user(
            username='gestor_totp',
            password='SenhaSegura1!',
            role=User.Role.GESTOR,
            company=self.company,
        )
        self.channel = Channel.objects.create(
            name='Canal TOTP',
            channel_type=Channel.ChannelType.EVOLUTION_NORMAL,
            company=self.company,
        )

    def test_gestor_sem_2fa_nao_lista_canais(self):
        client = APIClient()
        client.force_authenticate(user=self.gestor)
        response = client.get('/api/v1/channels/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.data.get('requires_totp_setup'))

    def test_gestor_sem_2fa_acessa_perfil(self):
        client = APIClient()
        client.force_authenticate(user=self.gestor)
        response = client.get('/api/v1/profile/')
        self.assertEqual(response.status_code, 200)


class MetaWebhookSignatureTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            legal_name='Empresa Meta LTDA',
            trade_name='Empresa Meta',
            cnpj='44.444.444/0001-44',
        )
        self.channel = Channel.objects.create(
            name='Canal Meta',
            channel_type=Channel.ChannelType.META_CLOUD,
            company=self.company,
            credentials={'verify_token': 'verify123', 'app_secret': 'meta-secret-test'},
        )

    def _signed_post(self, payload: dict, secret: str = 'meta-secret-test'):
        body = json.dumps(payload).encode()
        signature = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return body, signature

    @override_settings(DEBUG=False, META_APP_SECRET='meta-secret-test')
    def test_meta_webhook_rejeita_assinatura_invalida(self):
        body, _ = self._signed_post({'entry': []}, secret='wrong')
        response = self.client.post(
            f'/api/webhooks/meta/{self.channel.id}/',
            data=body,
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256='sha256=deadbeef',
        )
        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            SecurityEvent.objects.filter(
                event_type=SecurityEvent.EventType.WEBHOOK_REJECTED,
                company_id=self.company.id,
            ).exists()
        )

    @override_settings(DEBUG=False, META_APP_SECRET='meta-secret-test')
    def test_meta_webhook_aceita_assinatura_valida(self):
        payload = {'object': 'whatsapp_business_account', 'entry': []}
        body, signature = self._signed_post(payload)
        response = self.client.post(
            f'/api/webhooks/meta/{self.channel.id}/',
            data=body,
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256=signature,
        )
        self.assertEqual(response.status_code, 200)


class LoginSetupTokenTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            legal_name='Empresa Login LTDA',
            trade_name='Empresa Login',
            cnpj='55.555.555/0001-55',
        )
        self.gestor = User.objects.create_user(
            username='gestor_login',
            password='SenhaSegura1!',
            role=User.Role.GESTOR,
            company=self.company,
        )

    def test_login_pendente_2fa_nao_emite_cookie_jwt(self):
        client = APIClient()
        response = client.post(
            '/api/auth/login/',
            {'username': 'gestor_login', 'password': 'SenhaSegura1!'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('requires_totp_setup'))
        self.assertIn('setup_token', response.data)
        self.assertNotIn('access', response.data)
        self.assertNotIn('wc_access', response.cookies)

    def test_setup_pendente_com_token_temporario(self):
        token = create_pending_setup(self.gestor.id)
        client = APIClient()
        response = client.post(
            '/api/auth/totp/setup-pending/',
            {'setup_token': token},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('qr_code_base64', response.data)


class TransferIsolationTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(
            legal_name='Empresa TA LTDA',
            trade_name='Empresa TA',
            cnpj='66.666.666/0001-66',
        )
        self.company_b = Company.objects.create(
            legal_name='Empresa TB LTDA',
            trade_name='Empresa TB',
            cnpj='77.777.777/0001-77',
        )
        self.gestor_a = User.objects.create_user(
            username='gestor_ta',
            password='SenhaSegura1!',
            role=User.Role.GESTOR,
            company=self.company_a,
        )
        from django_otp.plugins.otp_totp.models import TOTPDevice
        TOTPDevice.objects.create(user=self.gestor_a, name='default', confirmed=True)
        self.atendente_b = User.objects.create_user(
            username='atendente_tb',
            password='SenhaSegura1!',
            role=User.Role.ATENDENTE,
            company=self.company_b,
        )
        self.channel_a = Channel.objects.create(
            name='Canal TA',
            channel_type=Channel.ChannelType.EVOLUTION_NORMAL,
            company=self.company_a,
        )
        self.contact_a = Contact.objects.create(
            channel=self.channel_a,
            external_id='5511999999999@s.whatsapp.net',
            phone='5511999999999',
            name='Cliente A',
        )
        self.conversation = Conversation.objects.create(
            channel=self.channel_a,
            contact=self.contact_a,
        )

    def test_transfer_rejeita_usuario_de_outra_empresa(self):
        client = APIClient()
        client.force_authenticate(user=self.gestor_a)
        response = client.patch(
            f'/api/v1/conversations/{self.conversation.id}/transfer/',
            {'assigned_to_id': self.atendente_b.id},
            format='json',
        )
        self.assertIn(response.status_code, (400, 403))


class CapabilitiesTests(TestCase):
    def setUp(self):
        self.support = User.objects.create_user(
            username='suporte_wc',
            password='SenhaSegura1!',
            is_staff=True,
            is_superuser=False,
            role=User.Role.GESTOR,
        )
        self.gestor = User.objects.create_user(
            username='gestor_cap',
            password='SenhaSegura1!',
            role=User.Role.GESTOR,
            company=Company.objects.create(
                legal_name='Empresa Cap LTDA',
                trade_name='Empresa Cap',
                code='CAP001',
            ),
        )

    def test_suporte_pode_criar_empresa(self):
        from apps.accounts.services.capabilities import get_user_capabilities

        caps = get_user_capabilities(self.support)
        self.assertTrue(caps['manage_companies'])
        self.assertFalse(caps['view_audit'])
        self.assertFalse(caps['view_security'])

    def test_gestor_nao_acessa_auditoria(self):
        client = APIClient()
        client.force_authenticate(user=self.gestor)
        response = client.get('/api/v1/audit-logs/')
        self.assertEqual(response.status_code, 403)

    def test_atendente_nao_acessa_contatos(self):
        atendente = User.objects.create_user(
            username='atend_cap',
            password='SenhaSegura1!',
            role=User.Role.ATENDENTE,
            company=self.gestor.company,
        )
        client = APIClient()
        client.force_authenticate(user=atendente)
        response = client.get('/api/v1/contacts/')
        self.assertEqual(response.status_code, 403)

    def test_suporte_exige_2fa(self):
        from apps.accounts.totp_service import user_requires_totp_setup

        self.assertTrue(user_requires_totp_setup(self.support))
