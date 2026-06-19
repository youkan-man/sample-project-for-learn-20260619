from threading import Lock

from app.schemas import TodoCreate, TodoResponse, TodoUpdate


class TodoStore:
    def __init__(self) -> None:
        self._todos: dict[int, TodoResponse] = {}
        self._next_id = 1
        self._lock = Lock()

    def create(self, data: TodoCreate) -> TodoResponse:
        with self._lock:
            todo = TodoResponse(id=self._next_id, **data.model_dump())
            self._todos[todo.id] = todo
            self._next_id += 1
            return todo

    def list(self) -> list[TodoResponse]:
        with self._lock:
            return [self._todos[todo_id] for todo_id in sorted(self._todos)]

    def get(self, todo_id: int) -> TodoResponse | None:
        with self._lock:
            return self._todos.get(todo_id)

    def update(self, todo_id: int, data: TodoUpdate) -> TodoResponse | None:
        with self._lock:
            if todo_id not in self._todos:
                return None
            todo = TodoResponse(id=todo_id, **data.model_dump())
            self._todos[todo_id] = todo
            return todo

    def delete(self, todo_id: int) -> bool:
        with self._lock:
            return self._todos.pop(todo_id, None) is not None


_todo_store = TodoStore()


def get_todo_store() -> TodoStore:
    return _todo_store
