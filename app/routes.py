from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.schemas import TodoCreate, TodoResponse, TodoUpdate
from app.store import TodoStore, get_todo_store


router = APIRouter(prefix="/todos", tags=["todos"])
Store = Annotated[TodoStore, Depends(get_todo_store)]


def not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, store: Store) -> TodoResponse:
    return store.create(todo)


@router.get("", response_model=list[TodoResponse])
def list_todos(store: Store) -> list[TodoResponse]:
    return store.list()


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, store: Store) -> TodoResponse:
    todo = store.get(todo_id)
    if todo is None:
        raise not_found()
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoUpdate, store: Store) -> TodoResponse:
    updated = store.update(todo_id, todo)
    if updated is None:
        raise not_found()
    return updated


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, store: Store) -> Response:
    if not store.delete(todo_id):
        raise not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
