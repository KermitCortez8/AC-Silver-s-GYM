"""Validación y coordinación de imágenes de productos."""
from pathlib import PurePath
import re
from uuid import uuid4

from application.ports.image_storage import ImageStorage

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class StoreImagesService:
    def __init__(self, storage: ImageStorage):
        self.storage = storage

    def list_images(self):
        return self.storage.list_images()

    def upload(self, filename, data, content_type):
        if not str(content_type or "").lower().startswith("image/"):
            raise ValueError("Selecciona un archivo de imagen")
        if not data:
            raise ValueError("La imagen esta vacia")
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError("La imagen supera 5 MB")
        original = PurePath(filename or "producto.jpg")
        extension = original.suffix.lower() or ".jpg"
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError("Formato de imagen no permitido")
        stem = re.sub(r"[^a-zA-Z0-9]+", "-", original.stem).strip("-").lower() or "producto"
        safe_name = f"{stem}-{uuid4().hex[:12]}{extension}"
        return self.storage.upload(safe_name, data, str(content_type or "image/jpeg"))
