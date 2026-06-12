from __future__ import annotations

import base64
import binascii
import hashlib
import json
import secrets
import time
from typing import Any


def get_user_role(email: str | None) -> str:
    if not email:
        return "user"
    return "admin" if email.endswith("@urp.edu.pe") else "user"


def decode_token_payload(token: str) -> dict[str, Any] | None:
    if not token:
        return None
    parts = token.split(".")
    if len(parts) == 3:
        try:
            payload = parts[1].replace("-", "+").replace("_", "/")
            padding = len(payload) % 4
            if padding:
                payload += "=" * (4 - padding)
            data = base64.b64decode(payload)
            raw = json.loads(data.decode("utf-8"))
            return raw if isinstance(raw, dict) else None
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error):
            return None

    try:
        normalized = token.strip()
        padding = len(normalized) % 4
        if padding:
            normalized += "=" * (4 - padding)
        data = base64.b64decode(normalized)
        raw = json.loads(data.decode("utf-8"))
        return raw if isinstance(raw, dict) else None
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error):
        return None


def normalize_profile(profile: dict[str, Any] | None, token: str) -> dict[str, Any]:
    source = profile or decode_token_payload(token) or {}
    email = str(source.get("email") or "").strip()
    name = str(source.get("name") or source.get("given_name") or source.get("givenName") or email.split("@")[0] or "Usuario").strip()
    return {
        "id": str(source.get("sub") or source.get("id") or email or "user-001"),
        "id_usuario": str(source.get("id_usuario") or source.get("id") or ""),
        "id_cliente": source.get("id_cliente"),
        "email": email,
        "telefono": str(source.get("telefono") or ""),
        "dni": str(source.get("dni") or ""),
        "name": name,
        "picture": str(source.get("picture") or ""),
        "givenName": str(source.get("given_name") or source.get("givenName") or name.split(" ")[0] or ""),
        "familyName": str(source.get("family_name") or source.get("familyName") or ""),
        "role": str(source.get("role") or get_user_role(email)),
    }


def get_expiry_seconds(token: str, default_seconds: int = 3600) -> int:
    payload = decode_token_payload(token)
    if not payload or "exp" not in payload:
        return default_seconds
    try:
        expires_at = int(float(payload["exp"]))
    except (TypeError, ValueError):
        return default_seconds
    return max(expires_at - int(time.time()), 60)


def hash_password(password: str) -> str:
    value = str(password or "")
    if not value:
        return ""

    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    value = str(password or "")
    stored = str(stored_hash or "")
    if not value or not stored:
        return False

    try:
        algorithm, salt, digest = stored.split("$", 2)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256" or not salt or not digest:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return secrets.compare_digest(candidate, digest)


def create_local_token(profile: dict[str, Any], expires_seconds: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": str(profile.get("id") or profile.get("id_usuario") or profile.get("id_cliente") or profile.get("email") or ""),
        "id": str(profile.get("id") or profile.get("id_usuario") or profile.get("id_cliente") or ""),
        "id_usuario": str(profile.get("id_usuario") or profile.get("id") or ""),
        "id_cliente": profile.get("id_cliente"),
        "email": str(profile.get("email") or profile.get("correo") or ""),
        "name": str(profile.get("name") or profile.get("nombre") or ""),
        "telefono": str(profile.get("telefono") or ""),
        "dni": str(profile.get("dni") or ""),
        "role": str(profile.get("role") or "user"),
        "iat": now,
        "exp": now + int(expires_seconds),
    }
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.b64encode(raw).decode("utf-8").rstrip("=")
