"""Authentication state abstraction for Google OAuth integration."""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode


@dataclass
class AuthState:
    state: str
    message: str
    user: dict[str, Any] | None = None


class AuthManager:
    """Google OAuth/OpenID Connect state manager.

    It never stores Google passwords and never fabricates a logged-in user.
    When configuration exists, it generates a real Google authorization URL.
    """

    def __init__(self, settings: Any | None = None):
        self.settings = settings
        self._state = "logged_out"
        self._user = None
        self._oauth_state = None
        self._message = "No has iniciado sesion."

    def get_status(self) -> dict[str, Any]:
        return {
            "state": self._state,
            "message": self._message,
            "user": self._user,
            "oauth_state": self._oauth_state,
        }

    def start_oauth(self) -> dict[str, Any]:
        client_id = self._config("google_client_id", "GOOGLE_CLIENT_ID")
        redirect_uri = self._config("google_redirect_uri", "GOOGLE_REDIRECT_URI")
        scopes = self._config("google_scopes", "GOOGLE_SCOPES") or "openid email profile"
        if not client_id or not redirect_uri:
            self._state = "authentication_error"
            self._message = "Google Login no esta configurado. Define Client ID y Redirect URI en Configuracion > Cuenta."
            return self.get_status()

        self._oauth_state = secrets.token_urlsafe(24)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scopes,
            "state": self._oauth_state,
            "access_type": "offline",
            "prompt": "consent",
        }
        self._state = "authenticating"
        self._message = "Abre la URL de Google para continuar con la autenticacion."
        status = self.get_status()
        status["auth_url"] = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        return status

    def complete_oauth_callback(self, state: str, user: dict[str, Any]) -> dict[str, Any]:
        if not self._oauth_state or state != self._oauth_state:
            self._state = "authentication_error"
            self._message = "La respuesta de autenticacion no coincide con el estado esperado."
            return self.get_status()
        return self.complete_login(user)

    def complete_login(self, user: dict[str, Any]) -> dict[str, Any]:
        self._state = "authenticated"
        self._user = user
        self._message = "Cuenta conectada correctamente."
        return self.get_status()

    def logout(self) -> dict[str, Any]:
        self._state = "logged_out"
        self._user = None
        self._oauth_state = None
        self._message = "No has iniciado sesion."
        return self.get_status()

    def expire_session(self) -> dict[str, Any]:
        self._state = "session_expired"
        self._user = None
        self._message = "La sesion expiro. Vuelve a iniciar sesion."
        return self.get_status()

    def _config(self, setting_key: str, env_key: str) -> str:
        if self.settings is not None:
            value = self.settings.get(setting_key, "")
            if value:
                return str(value)
        return os.environ.get(env_key, "")
