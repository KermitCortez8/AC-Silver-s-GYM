from __future__ import annotations

import base64
import json
import time

from utils.security import (
    create_local_token,
    decode_token_payload,
    get_expiry_seconds,
    get_user_role,
    hash_password,
    normalize_profile,
    verify_password,
)


def _jwt_with_payload(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    return f"header.{encoded}.signature"


def test_get_user_role_returns_user_without_email() -> None:
    assert get_user_role(None) == "user"


def test_get_user_role_marks_urp_email_as_admin() -> None:
    assert get_user_role("persona@urp.edu.pe") == "admin"


def test_decode_token_payload_reads_jwt_payload() -> None:
    assert decode_token_payload(_jwt_with_payload({"email": "a@b.com"})) == {"email": "a@b.com"}


def test_decode_token_payload_returns_none_for_invalid_token() -> None:
    assert decode_token_payload("token-invalido") is None


def test_normalize_profile_uses_email_prefix_as_name_fallback() -> None:
    profile = normalize_profile({"email": "cliente@example.com"}, "")
    assert profile["name"] == "cliente"


def test_get_expiry_seconds_uses_default_for_token_without_exp() -> None:
    assert get_expiry_seconds(_jwt_with_payload({"sub": "abc"}), default_seconds=120) == 120


def test_hash_password_can_be_verified() -> None:
    stored = hash_password("secreto")
    assert verify_password("secreto", stored) is True


def test_verify_password_rejects_wrong_password() -> None:
    stored = hash_password("secreto")
    assert verify_password("otro", stored) is False


def test_create_local_token_contains_expected_profile_data() -> None:
    token = create_local_token({"id": "u1", "email": "u1@example.com", "name": "User"}, expires_seconds=90)
    payload = decode_token_payload(token)
    assert payload["email"] == "u1@example.com"
    assert payload["exp"] >= int(time.time()) + 80


def test_normalize_profile_can_use_token_payload_when_profile_is_missing() -> None:
    token = _jwt_with_payload({"sub": "abc", "email": "token@example.com", "given_name": "Token"})
    profile = normalize_profile(None, token)
    assert profile["id"] == "abc"
    assert profile["email"] == "token@example.com"
