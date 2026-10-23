"""Transporte HTTP compartido; los errores conservan los códigos del proveedor."""
import json
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from application.errors import PersistenceUnavailable


class RemoteServiceError(PersistenceUnavailable):
    def __init__(self, context, status, payload):
        self.status = status
        self.payload = payload if isinstance(payload, dict) else {}
        self.code = self.payload.get("code")
        self.remote_message = self.payload.get("message", "")
        super().__init__(f"{context} fallo ({status}): {json.dumps(payload, ensure_ascii=False)}")


def error_payload(error):
    """Acepta errores estructurados y mensajes de adaptadores anteriores."""
    if isinstance(error, RemoteServiceError):
        return error.payload
    message = str(error)
    try:
        payload = json.loads(message[message.index("{"):])
        return payload if isinstance(payload, dict) else {}
    except (ValueError, TypeError):
        return {}


def database_code(error):
    code = error_payload(error).get("code")
    if code:
        return code
    # Adaptadores anteriores a los errores estructurados y dobles de pruebas.
    match = re.match(r"^(PGRST\d{3}|[0-9A-Z]{5})(?=[:\s])", str(error))
    return match.group(1) if match else None


def send(request, *, context, timeout=20, opener=urlopen):
    try:
        with opener(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {"message": raw}
        raise RemoteServiceError(context, error.code, payload) from error
    except OSError as error:
        raise RemoteServiceError(context, 503, {"message": "El proveedor no está disponible"}) from error


def json_request(url, *, method, headers, body=None, context, timeout=20, opener=urlopen):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    raw = send(Request(url, data=data, headers=headers, method=method),
               context=context, timeout=timeout, opener=opener)
    return json.loads(raw) if raw else None


def supabase_headers(key):
    return {"apikey": key, "Authorization": f"Bearer {key}",
            "Accept": "application/json", "Content-Type": "application/json"}
