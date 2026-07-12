from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """Autentica JWT via cookie HttpOnly ou header Authorization."""

    def authenticate(self, request):
        header = self.get_header(request)
        raw_token = None
        if header is not None:
            raw_token = self.get_raw_token(header)
        if raw_token is None:
            raw_token = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
        if raw_token is None:
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError as exc:
            raise InvalidToken(exc.args[0]) from exc
        return self.get_user(validated_token), validated_token
