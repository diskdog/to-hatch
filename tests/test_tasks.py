"""Integration tests for To Hatch task CRUD operations.

Each test runs against a temporary SQLite database that is created fresh
for the test and discarded afterwards, so production data in hatch.db is
never touched.
"""

import pytest
from fastapi.testclient import TestClient

import database
from database import create_task, get_task_by_id
from main import app
from models import TaskCreate


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Yield a TestClient backed by a fresh temporary SQLite database.

    Monkeypatches ``database.DB_PATH`` so every call to ``_get_connection``
    hits a throwaway file under *tmp_path* instead of ``hatch.db``.  The app
    lifespan calls ``init_db()`` on startup, which creates the schema in that
    temporary file before any test code runs.

    Args:
        tmp_path: pytest-provided temporary directory, unique per test.
        monkeypatch: pytest fixture for reversible attribute overrides.

    Yields:
        A :class:`~fastapi.testclient.TestClient` ready to make requests.
    """
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


def test_create_task_with_valid_data(client):
    """POST /tasks with valid data redirects and the new task appears on the board."""
    response = client.post(
        "/tasks",
        data={"title": "Lay the first egg", "priority": "medium"},
        follow_redirects=False,
    )

    assert response.status_code == 303

    board = client.get("/")
    assert "Lay the first egg" in board.text


def test_create_task_missing_title(client):
    """POST /tasks with no title field returns 422 Unprocessable Entity."""
    response = client.post(
        "/tasks",
        data={"priority": "low"},
        follow_redirects=False,
    )

    assert response.status_code == 422


def test_move_task_forward(client):
    """Moving a task forward advances its status: nest → hatching → flown."""
    task = create_task(TaskCreate(title="Egg on the move", priority="low"))

    first_move = client.post(
        f"/tasks/{task.id}/move",
        data={"direction": "forward"},
        follow_redirects=False,
    )
    assert first_move.status_code == 303
    assert get_task_by_id(task.id).status == "hatching"

    second_move = client.post(
        f"/tasks/{task.id}/move",
        data={"direction": "forward"},
        follow_redirects=False,
    )
    assert second_move.status_code == 303
    assert get_task_by_id(task.id).status == "flown"


def test_delete_task(client):
    """POST /tasks/{id}/delete removes the task and it no longer appears on the board."""
    task = create_task(TaskCreate(title="Gone duckling", priority="high"))

    response = client.post(f"/tasks/{task.id}/delete", follow_redirects=False)
    assert response.status_code == 303

    board = client.get("/")
    assert "Gone duckling" not in board.text


def test_get_nonexistent_task(client):
    """GET /tasks/{id}/edit with an unknown ID returns 404."""
    response = client.get("/tasks/nonexistent-uuid/edit")

    assert response.status_code == 404
