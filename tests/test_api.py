def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_endpoint(client):
    response = client.get("/products", params={"q": "camisa azul"})
    assert response.status_code == 200
    body = response.json()
    assert body[0]["product"]["sku"] == "CAM-001"


def test_get_product_endpoint(client):
    response = client.get("/products/cam-001")
    assert response.status_code == 200
    assert response.json()["precio"] == "89.90"


def test_missing_product_returns_404(client):
    response = client.get("/products/NO-EXISTE")
    assert response.status_code == 404


def test_refresh_endpoint(client):
    response = client.post("/catalog/refresh")
    assert response.status_code == 200
    assert response.json()["valid_products"] == 2
