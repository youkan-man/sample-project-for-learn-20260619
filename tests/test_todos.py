import pytest
from fastapi.testclient import TestClient


def create_todo(client: TestClient, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"title": "Write tests"}
    payload.update(overrides)
    response = client.post("/todos", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_todo_uses_defaults_and_increments_ids(client: TestClient) -> None:
    first = create_todo(client, title="  First task  ")
    second = create_todo(client, title="Second task", completed=True)

    assert first == {"id": 1, "title": "First task", "completed": False}
    assert second == {"id": 2, "title": "Second task", "completed": True}


def test_list_and_get_todos(client: TestClient) -> None:
    assert client.get("/todos").json() == []
    first = create_todo(client, title="First")
    second = create_todo(client, title="Second")

    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == [first, second]
    assert client.get("/todos/2").json() == second


def test_update_todo(client: TestClient) -> None:
    todo = create_todo(client)

    response = client.put(
        f"/todos/{todo['id']}",
        json={"title": "Updated task", "completed": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": todo["id"],
        "title": "Updated task",
        "completed": True,
    }
    assert client.get(f"/todos/{todo['id']}").json() == response.json()


def test_delete_todo(client: TestClient) -> None:
    todo = create_todo(client)

    response = client.delete(f"/todos/{todo['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/todos/{todo['id']}").status_code == 404


def test_missing_todo_returns_404(client: TestClient) -> None:
    assert client.get("/todos/999").json() == {"detail": "Todo not found"}
    assert client.get("/todos/999").status_code == 404
    assert (
        client.put(
            "/todos/999", json={"title": "Missing", "completed": False}
        ).status_code
        == 404
    )
    assert client.delete("/todos/999").status_code == 404


@pytest.mark.parametrize("title", ["", "   ", "x" * 201])
def test_create_rejects_invalid_title(client: TestClient, title: str) -> None:
    response = client.post("/todos", json={"title": title})
    assert response.status_code == 422


def test_put_requires_all_fields(client: TestClient) -> None:
    todo = create_todo(client)
    response = client.put(f"/todos/{todo['id']}", json={"title": "Incomplete"})
    assert response.status_code == 422


def test_openapi_is_available(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/todos" in response.json()["paths"]
