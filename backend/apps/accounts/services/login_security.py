import os

from django.core.cache import cache

LOGIN_GENERIC_MESSAGE = (
    'Credenciais inválidas ou acesso temporariamente bloqueado. Tente novamente mais tarde.'
)

MAX_ATTEMPTS = int(os.getenv('LOGIN_MAX_ATTEMPTS', '5'))
ATTEMPT_WINDOW_SECONDS = int(os.getenv('LOGIN_ATTEMPT_WINDOW_MINUTES', '15')) * 60
LOCKOUT_SECONDS = int(os.getenv('LOGIN_LOCKOUT_MINUTES', '30')) * 60


def _ip_key(ip: str) -> str:
    return f'login:ip:{ip}'


def _user_key(username: str) -> str:
    return f'login:user:{username.lower()}'


def _lock_ip_key(ip: str) -> str:
    return f'login:lock:ip:{ip}'


def _lock_user_key(username: str) -> str:
    return f'login:lock:user:{username.lower()}'


def remaining_lockout_seconds(ip: str | None, username: str | None) -> int:
    """Retorna segundos restantes do bloqueio, ou 0 se liberado."""
    remaining = 0
    keys: list[str] = []
    if ip:
        keys.append(_lock_ip_key(ip))
    if username:
        keys.append(_lock_user_key(username))

    for key in keys:
        if cache.get(key) is None:
            continue
        ttl = cache.ttl(key)
        if ttl is None or ttl < 0:
            remaining = max(remaining, LOCKOUT_SECONDS)
        else:
            remaining = max(remaining, ttl)
    return remaining


def is_blocked(ip: str | None, username: str | None) -> bool:
    """Verifica se IP ou usuário estão bloqueados por bruteforce."""
    return remaining_lockout_seconds(ip, username) > 0


def _increment_failures(key: str) -> int:
    """Incrementa contador de falhas com TTL na janela configurada."""
    if cache.get(key) is None:
        cache.set(key, 1, ATTEMPT_WINDOW_SECONDS)
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, ATTEMPT_WINDOW_SECONDS)
        return 1


def _apply_lockout(ip: str | None, username: str | None) -> None:
    """Aplica bloqueio temporário ao IP e/ou username."""
    if ip:
        cache.set(_lock_ip_key(ip), 1, LOCKOUT_SECONDS)
        cache.delete(_ip_key(ip))
    if username:
        cache.set(_lock_user_key(username), 1, LOCKOUT_SECONDS)
        cache.delete(_user_key(username))


def register_failure(ip: str | None, username: str | None) -> dict:
    """
    Registra tentativa falha de login.
    Retorna dict com attempt_count e locked (bool).
    """
    ip_count = _increment_failures(_ip_key(ip)) if ip else 0
    user_count = _increment_failures(_user_key(username)) if username else 0
    attempt_count = max(ip_count, user_count)
    locked = attempt_count >= MAX_ATTEMPTS

    if locked:
        _apply_lockout(ip, username)

    return {
        'attempt_count': attempt_count,
        'locked': locked,
        'max_attempts': MAX_ATTEMPTS,
    }


def clear_success(ip: str | None, username: str | None) -> None:
    """Limpa contadores após login bem-sucedido."""
    if ip:
        cache.delete(_ip_key(ip))
        cache.delete(_lock_ip_key(ip))
    if username:
        cache.delete(_user_key(username))
        cache.delete(_lock_user_key(username))


def get_failure_count(ip: str | None, username: str | None) -> int:
    """Retorna contagem atual de falhas na janela."""
    counts = []
    if ip:
        counts.append(cache.get(_ip_key(ip)) or 0)
    if username:
        counts.append(cache.get(_user_key(username)) or 0)
    return max(counts) if counts else 0


def unlock_ip(ip: str) -> None:
    """Remove bloqueio e contadores de um IP."""
    cache.delete(_lock_ip_key(ip))
    cache.delete(_ip_key(ip))


def unlock_username(username: str) -> None:
    """Remove bloqueio e contadores de um usuário."""
    normalized = username.lower()
    cache.delete(_lock_user_key(normalized))
    cache.delete(_user_key(normalized))
