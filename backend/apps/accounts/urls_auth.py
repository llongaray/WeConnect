from django.urls import path

from .views_auth import (
    AcceptPrivacyPendingView,
    AcceptPrivacyView,
    CsrfTokenView,
    CustomTokenObtainPairView,
    LoginPrecheckView,
    LoginTotpView,
    LogoutView,
    SessionView,
    ThrottledTokenRefreshView,
)
from .views_totp import (
    TotpConfirmPendingView,
    TotpConfirmView,
    TotpDisableView,
    TotpSetupPendingView,
    TotpSetupView,
    TotpStatusView,
)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/precheck/', LoginPrecheckView.as_view(), name='login_precheck'),
    path('login/totp/', LoginTotpView.as_view(), name='login_totp'),
    path('refresh/', ThrottledTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='token_logout'),
    path('session/', SessionView.as_view(), name='session'),
    path('accept-privacy/', AcceptPrivacyView.as_view(), name='accept_privacy'),
    path('accept-privacy-pending/', AcceptPrivacyPendingView.as_view(), name='accept_privacy_pending'),
    path('csrf/', CsrfTokenView.as_view(), name='csrf'),
    path('totp/setup/', TotpSetupView.as_view(), name='totp_setup'),
    path('totp/setup-pending/', TotpSetupPendingView.as_view(), name='totp_setup_pending'),
    path('totp/confirm/', TotpConfirmView.as_view(), name='totp_confirm'),
    path('totp/confirm-pending/', TotpConfirmPendingView.as_view(), name='totp_confirm_pending'),
    path('totp/disable/', TotpDisableView.as_view(), name='totp_disable'),
    path('totp/status/', TotpStatusView.as_view(), name='totp_status'),
]
