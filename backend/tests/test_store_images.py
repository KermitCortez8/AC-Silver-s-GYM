import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.services.store_images_service import StoreImagesService
from infrastructure.services.local_image_storage import LocalImageStorage
from presentation.dependencies import get_store_images_service
from presentation.routes.store_routes import router


@pytest.fixture
def images_api(tmp_path):
    app = FastAPI()
    service = StoreImagesService(LocalImageStorage(tmp_path))
    app.dependency_overrides[get_store_images_service] = lambda: service
    app.include_router(router)
    return TestClient(app), tmp_path


def test_image_upload_and_listing_preserve_public_urls(images_api):
    client, directory = images_api
    response = client.post("/tienda/imagenes", files={"file": ("../../Producto Demo.PNG", b"image-data", "image/png")})
    assert response.status_code == 201
    record = response.json()
    assert re.fullmatch(r"producto-demo-[a-f0-9]{12}\.png", record["name"])
    assert record["url"] == f"/api/uploads/store-images/{record['name']}"
    assert (directory / record["name"]).read_bytes() == b"image-data"
    assert client.get("/tienda/imagenes").json() == [record]


@pytest.mark.parametrize("filename,data,mime", [
    ("file.txt", b"text", "text/plain"),
    ("file.svg", b"svg", "image/svg+xml"),
    ("file.png", b"", "image/png"),
    ("file.png", b"x" * (5 * 1024 * 1024 + 1), "image/png"),
])
def test_invalid_uploads_are_rejected_before_storage(images_api, filename, data, mime):
    client, directory = images_api
    response = client.post("/tienda/imagenes", files={"file": (filename, data, mime)})
    assert response.status_code == 400
    assert list(directory.iterdir()) == []
