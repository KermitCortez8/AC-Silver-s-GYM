"""TC-172: permisos antes de storage y política de subida como staff."""
from types import SimpleNamespace

from presentation.dependencies import get_current_user
from tests.tienda_pedidos.integracion.test_store_images import images_api  # noqa: F401


def test_tc172_roles_y_archivo_invalido_no_escriben_storage(images_api):
    client, directory = images_api
    for role in ("user", "trainer"):
        client.app.dependency_overrides[get_current_user] = lambda role=role: SimpleNamespace(role=role)
        assert client.post("/tienda/imagenes", files={"file": ("qa.png", b"image", "image/png")}).status_code == 403
        assert list(directory.iterdir()) == []
    client.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role="staff")
    for name, data, mime in [("qa.txt", b"text", "text/plain"), ("qa.svg", b"svg", "image/svg+xml"),
                             ("qa.png", b"", "image/png"), ("qa.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")]:
        assert client.post("/tienda/imagenes", files={"file": (name, data, mime)}).status_code == 400
        assert list(directory.iterdir()) == []
    response = client.post("/tienda/imagenes", files={"file": ("qa.png", b"image", "image/png")})
    assert response.status_code == 201
    assert response.json()["url"].startswith("/api/uploads/store-images/qa-")
    assert (directory / response.json()["name"]).read_bytes() == b"image"
