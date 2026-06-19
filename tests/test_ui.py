from fastapi.testclient import TestClient


def test_index_serves_ui(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Focus List" in response.text
    assert 'id="todo-form"' in response.text
    assert 'id="todo-list"' in response.text
    assert '/static/styles.css' in response.text
    assert '/static/app.js' in response.text


def test_static_assets_are_available(client: TestClient) -> None:
    css = client.get("/static/styles.css")
    javascript = client.get("/static/app.js")

    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")
    assert javascript.status_code == 200
    assert "javascript" in javascript.headers["content-type"]
    assert client.get("/static/missing.css").status_code == 404


def test_api_documentation_coexists_with_ui(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert "/todos" in schema.json()["paths"]
