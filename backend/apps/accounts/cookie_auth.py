from django.conf import settings
from rest_framework.response import Response


def _cookie_secure() -> bool:
    return not settings.DEBUG


def set_jwt_cookies(response: Response, access: str, refresh: str | None = None) -> Response:
    """Define cookies HttpOnly para tokens JWT."""
    response.set_cookie(
        settings.JWT_ACCESS_COOKIE_NAME,
        access,
        max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        secure=_cookie_secure(),
        samesite='Lax',
        path='/',
    )
    if refresh:
        response.set_cookie(
            settings.JWT_REFRESH_COOKIE_NAME,
            refresh,
            max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
            httponly=True,
            secure=_cookie_secure(),
            samesite='Lax',
            path='/api/auth/',
        )
    return response


def clear_jwt_cookies(response: Response) -> Response:
    response.delete_cookie(settings.JWT_ACCESS_COOKIE_NAME, path='/')
    response.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME, path='/api/auth/')
    return response


def get_refresh_from_request(request) -> str | None:
    return request.data.get('refresh') or request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
