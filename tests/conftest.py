import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import TodoStore, get_todo_store


@pytest.fixture
def client() -> TestClient:
    store = TodoStore()
    app.dependency_overrides[get_todo_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
