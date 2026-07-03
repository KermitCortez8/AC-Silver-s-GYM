from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


class SupabaseStorageService:
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}

    def __init__(self, supabase_url: str, supabase_key: str, bucket: str) -> None:
        self.base_url = supabase_url.rstrip("/")
        self.key = supabase_key
        self.bucket = bucket.strip()

    def public_url(self, path: str) -> str:
        encoded_path = "/".join(quote(segment, safe="") for segment in path.split("/") if segment)
        return f"{self.base_url}/storage/v1/object/public/{quote(self.bucket, safe='')}/{encoded_path}"

    def upload(self, path: str, data: bytes, content_type: str) -> dict[str, str]:
        encoded_path = "/".join(quote(segment, safe="") for segment in path.split("/") if segment)
        url = f"{self.base_url}/storage/v1/object/{quote(self.bucket, safe='')}/{encoded_path}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": content_type or "application/octet-stream",
            "x-upsert": "true",
        }
        request = Request(url, data=data, headers=headers, method="POST")

        try:
            with urlopen(request, timeout=30) as response:
                response.read()
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"No se pudo subir la imagen a Supabase ({error.code}): {details}") from error

        return {
            "name": path.split("/")[-1],
            "path": path,
            "url": self.public_url(path),
        }

    def list_images(self, prefix: str = "", limit: int = 200) -> list[dict[str, str]]:
        url = f"{self.base_url}/storage/v1/object/list/{quote(self.bucket, safe='')}"
        body = {
            "prefix": prefix or "",
            "limit": limit,
            "offset": 0,
            "sortBy": {"column": "name", "order": "asc"},
        }
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        request = Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"No se pudo listar imagenes del bucket ({error.code}): {details}") from error

        rows = json.loads(raw) if raw else []
        images: list[dict[str, str]] = []

        for row in rows if isinstance(rows, list) else []:
            name = str(row.get("name") or "").strip()
            if not name or row.get("id") is None:
                continue

            extension = f".{name.rsplit('.', 1)[-1].lower()}" if "." in name else ""
            if extension and extension not in self.IMAGE_EXTENSIONS:
                continue

            images.append(
                {
                    "name": name,
                    "path": name,
                    "url": self.public_url(name),
                }
            )

        return images
