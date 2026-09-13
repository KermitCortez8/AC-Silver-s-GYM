"""Verifica las credenciales de Google antes de usar sus datos en el gimnasio."""
from __future__ import annotations

from functools import partial
import threading

from cachecontrol import CacheControl
from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import requests

from config import get_settings

_transport = threading.local()


def verify_google_credential(credential: str) -> dict:
    client_id = get_settings().google_client_id
    if not client_id:
        raise RuntimeError("Google no está configurado: falta GOOGLE_CLIENT_ID en backend/.env")
    if not credential or len(credential) > 16384:
        raise ValueError("No se recibió una credencial válida de Google")
    if not hasattr(_transport, "request"):
        # Respeta la caché HTTP de los certificados sin compartir una sesión entre hilos.
        _transport.request = Request(session=CacheControl(requests.Session()))
    try:
        claims = id_token.verify_oauth2_token(
            credential, partial(_transport.request, timeout=10), client_id,
        )
    except (TransportError, requests.RequestException) as error:
        raise RuntimeError("No se pudo consultar Google. Inténtalo nuevamente.") from error
    except (ValueError, GoogleAuthError) as error:
        raise ValueError("La credencial de Google es inválida o venció. Vuelve a seleccionar tu cuenta.") from error
    if (
        claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}
        or claims.get("aud") != client_id
        or not claims.get("sub")
        or claims.get("email_verified") is not True
        or not claims.get("email")
    ):
        raise ValueError("Google no pudo verificar la identidad o el correo de esta cuenta")
    return claims
