from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    picture: str = ""
    givenName: str = ""
    familyName: str = ""
    role: Literal["admin", "user", "trainer", "staff"] = "user"


class AuthGoogleRequest(BaseModel):
    credential: str
    profile: dict[str, Any] | None = None


class AuthResponse(BaseModel):
    user: UserProfile
    token: str
    expiresIn: int
    source: Literal["backend"] = "backend"
