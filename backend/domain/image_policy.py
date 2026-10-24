"""Formatos y tamaño de imágenes; compartidos por servicio y almacenamientos."""
from pathlib import PurePath

IMAGE_MIME_TYPES = {
    ".jpg": {"image/jpeg", "image/jpg"}, ".jpeg": {"image/jpeg", "image/jpg"},
    ".png": {"image/png"}, ".webp": {"image/webp"}, ".gif": {"image/gif"},
}
ALLOWED_IMAGE_EXTENSIONS = frozenset(IMAGE_MIME_TYPES)
# Los SVG existentes siguen disponibles en el catálogo; no se admiten nuevas subidas.
LIST_IMAGE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | {".svg"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def validate_image(filename, data, content_type):
    mime = str(content_type or "").lower().split(";", 1)[0].strip()
    if not mime.startswith("image/"):
        raise ValueError("Selecciona un archivo de imagen")
    if not data:
        raise ValueError("La imagen esta vacia")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("La imagen supera 5 MB")
    extension = PurePath(filename or "producto.jpg").suffix.lower() or ".jpg"
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Formato de imagen no permitido")
    if mime not in IMAGE_MIME_TYPES[extension]:
        raise ValueError("El tipo de imagen no coincide con su extensión")
    return extension
