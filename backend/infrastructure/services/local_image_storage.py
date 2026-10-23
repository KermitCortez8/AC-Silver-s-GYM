"""Almacenamiento local compatible con las rutas públicas existentes."""
from pathlib import Path

from application.services.store_images_service import ALLOWED_IMAGE_EXTENSIONS


class LocalImageStorage:
    def __init__(self, directory):
        self.directory = Path(directory)

    @staticmethod
    def _record(name):
        return {"name": name, "path": name, "url": f"/api/uploads/store-images/{name}"}

    def list_images(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        return [self._record(path.name) for path in sorted(self.directory.iterdir())
                if path.is_file() and path.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS]

    def upload(self, path, data, content_type):
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / path).write_bytes(data)
        return self._record(path)
