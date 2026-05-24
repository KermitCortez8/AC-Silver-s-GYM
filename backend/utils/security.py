from __future__ import annotations

import base64
import binascii
import json
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
        "email": email,
        "name": name,
        "picture": str(source.get("picture") or ""),
        "givenName": str(source.get("given_name") or source.get("givenName") or name.split(" ")[0] or ""),
        "familyName": str(source.get("family_name") or source.get("familyName") or ""),
        "role": get_user_role(email),
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
