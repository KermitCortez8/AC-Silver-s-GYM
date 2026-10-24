"""Validación y coordinación de imágenes de productos."""
from pathlib import PurePath
import re
from uuid import uuid4

from application.ports.image_storage import ImageStorage

from domain.image_policy import (
    ALLOWED_IMAGE_EXTENSIONS as ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_BYTES as MAX_IMAGE_BYTES, validate_image,
)


class StoreImagesService:
    def __init__(self, storage: ImageStorage):
        self.storage = storage

    def list_images(self):
        return self.storage.list_images()

    def upload(self, filename, data, content_type):
        extension = validate_image(filename, data, content_type)
        original = PurePath(filename or "producto.jpg")
        stem = re.sub(r"[^a-zA-Z0-9]+", "-", original.stem).strip("-").lower() or "producto"
        safe_name = f"{stem}-{uuid4().hex[:12]}{extension}"
        return self.storage.upload(safe_name, data, str(content_type or "image/jpeg"))
