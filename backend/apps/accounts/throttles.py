from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """Rate limit para endpoints de autenticação (login/refresh)."""
    scope = 'auth'


class CnpjLookupRateThrottle(SimpleRateThrottle):
    """Rate limit para consulta de CNPJ (superuser autenticado)."""
    scope = 'cnpj_lookup'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class DeepSeekRateThrottle(SimpleRateThrottle):
    """Rate limit para geração de fluxos via DeepSeek."""
    scope = 'deepseek'

    def get_cache_key(self, request, view):
        user = request.user
        company_id = request.query_params.get('company_id') or request.data.get('company_id') or ''
        if user and user.is_authenticated:
            ident = f'{user.pk}:{company_id}'
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}
