from typing import Annotated

from pydantic import BaseModel, StringConstraints


TodoTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]


class TodoCreate(BaseModel):
    title: TodoTitle
    completed: bool = False


class TodoUpdate(BaseModel):
    title: TodoTitle
    completed: bool


class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool
