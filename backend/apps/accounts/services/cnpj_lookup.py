import re

import httpx
from rest_framework.exceptions import ValidationError

BRASIL_API_CNPJ_URL = 'https://brasilapi.com.br/api/cnpj/v1/{cnpj}'


def normalize_cnpj(value: str) -> str:
    """Remove caracteres não numéricos do CNPJ."""
    return re.sub(r'\D', '', value or '')


def format_cnpj(digits: str) -> str:
    """Formata CNPJ como 00.000.000/0000-00."""
    clean = normalize_cnpj(digits)
    if len(clean) != 14:
        return digits
    return f'{clean[:2]}.{clean[2:5]}.{clean[5:8]}/{clean[8:12]}-{clean[12:]}'


def _format_phone(raw: str) -> str:
    """Formata telefone retornado pela API (DDD + número)."""
    digits = re.sub(r'\D', '', raw or '')
    if len(digits) == 10:
        return f'({digits[:2]}) {digits[2:6]}-{digits[6:]}'
    if len(digits) == 11:
        return f'({digits[:2]}) {digits[2:7]}-{digits[7:]}'
    return raw


def _build_address(data: dict) -> str:
    """Monta endereço legível a partir dos campos da Receita."""
    parts: list[str] = []

    if data.get('logradouro'):
        line = data['logradouro']
        if data.get('numero'):
            line += f', {data["numero"]}'
        if data.get('complemento'):
            line += f' — {data["complemento"]}'
        parts.append(line)

    location = ', '.join(p for p in [data.get('bairro'), data.get('municipio')] if p)
    if data.get('uf'):
        location = f'{location} — {data["uf"]}' if location else data['uf']
    if location:
        parts.append(location)

    cep = normalize_cnpj(str(data.get('cep') or ''))[:8]
    if len(cep) == 8:
        parts.append(f'CEP {cep[:5]}-{cep[5:]}')

    return ' — '.join(parts)


def lookup_cnpj(cnpj: str) -> dict:
    """Consulta dados cadastrais do CNPJ na Brasil API."""
    digits = normalize_cnpj(cnpj)
    if len(digits) != 14:
        raise ValidationError({'detail': 'CNPJ deve conter 14 dígitos.'})

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(BRASIL_API_CNPJ_URL.format(cnpj=digits))
    except httpx.RequestError as exc:
        raise ValidationError({'detail': 'Não foi possível consultar o CNPJ no momento.'}) from exc

    if response.status_code == 404:
        raise ValidationError({'detail': 'CNPJ não encontrado na Receita Federal.'})
    if response.status_code != 200:
        raise ValidationError({'detail': 'Serviço de consulta de CNPJ indisponível.'})

    data = response.json()
    phone = _format_phone(data.get('ddd_telefone_1') or data.get('ddd_telefone_2') or '')

    return {
        'cnpj': format_cnpj(digits),
        'legal_name': data.get('razao_social') or '',
        'trade_name': data.get('nome_fantasia') or data.get('razao_social') or '',
        'address': _build_address(data),
        'contact_email': data.get('email') or '',
        'contact_phone': phone,
    }
