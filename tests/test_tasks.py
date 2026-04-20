"""Integration tests for To Hatch task CRUD operations.

Each test runs against a temporary SQLite database that is created fresh
for the test and discarded afterwards, so production data in hatch.db is
never touched.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import database
from database import create_task, get_task_by_id
from main import app
from models import TaskCreate


@pytest.fixture()
def client(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> TestClient:
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


# ---------------------------------------------------------------------------
# Basic CRUD — happy paths
# ---------------------------------------------------------------------------


def test_create_task_with_valid_data(client: TestClient) -> None:
    """POST /tasks with valid data redirects and the new task appears on the board."""
    response = client.post(
        "/tasks",
        data={"title": "Lay the first egg", "priority": "medium"},
        follow_redirects=False,
    )

    assert response.status_code == 303

    board = client.get("/")
    assert "Lay the first egg" in board.text


def test_create_task_with_due_date(client: TestClient) -> None:
    """POST /tasks with a due_date persists the date and shows it on the board."""
    response = client.post(
        "/tasks",
        data={"title": "Timed egg", "priority": "high", "due_date": "2026-12-31"},
        follow_redirects=False,
    )

    assert response.status_code == 303

    board = client.get("/")
    assert "Timed egg" in board.text


def test_create_task_defaults_to_low_priority(client: TestClient) -> None:
    """POST /tasks without a priority field defaults to low."""
    client.post("/tasks", data={"title": "Default priority"}, follow_redirects=False)

    board = client.get("/")
    assert "Default priority" in board.text


def test_create_task_missing_title(client: TestClient) -> None:
    """POST /tasks with no title field returns 422 Unprocessable Entity."""
    response = client.post(
        "/tasks",
        data={"priority": "low"},
        follow_redirects=False,
    )

    assert response.status_code == 422


def test_delete_task(client: TestClient) -> None:
    """POST /tasks/{id}/delete removes the task and it no longer appears on the board."""
    task = create_task(TaskCreate(title="Gone duckling", priority="high"))

    response = client.post(f"/tasks/{task.id}/delete", follow_redirects=False)
    assert response.status_code == 303

    board = client.get("/")
    assert "Gone duckling" not in board.text


def test_delete_nonexistent_task(client: TestClient) -> None:
    """POST /tasks/{id}/delete with an unknown ID returns 404."""
    response = client.post("/tasks/nonexistent-id/delete", follow_redirects=False)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Edit / update
# ---------------------------------------------------------------------------


def test_edit_task_form_renders(client: TestClient) -> None:
    """GET /tasks/{id}/edit returns 200 with the task's current values."""
    task = create_task(TaskCreate(title="Egg to edit", priority="low"))

    response = client.get(f"/tasks/{task.id}/edit")
    assert response.status_code == 200
    assert "Egg to edit" in response.text


def test_edit_task_updates_title_and_priority(client: TestClient) -> None:
    """POST /tasks/{id}/edit persists title and priority changes."""
    task = create_task(TaskCreate(title="Old title", priority="low"))

    response = client.post(
        f"/tasks/{task.id}/edit",
        data={"title": "New title", "priority": "high"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    updated = get_task_by_id(task.id)
    assert updated.title == "New title"
    assert updated.priority == "high"


def test_edit_task_clears_due_date(client: TestClient) -> None:
    """POST /tasks/{id}/edit with no due_date clears an existing date."""
    task = create_task(TaskCreate(title="Dated egg", priority="low", due_date="2026-01-01"))

    client.post(
        f"/tasks/{task.id}/edit",
        data={"title": "Dated egg", "priority": "low"},
        follow_redirects=False,
    )

    updated = get_task_by_id(task.id)
    assert updated.due_date is None


def test_edit_nonexistent_task(client: TestClient) -> None:
    """POST /tasks/{id}/edit with an unknown ID returns 404."""
    response = client.post(
        "/tasks/nonexistent-id/edit",
        data={"title": "Ghost", "priority": "low"},
        follow_redirects=False,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Move / status transitions
# ---------------------------------------------------------------------------


def test_move_task_forward(client: TestClient) -> None:
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


def test_move_task_backward(client: TestClient) -> None:
    """Moving a task backward retreats its status: hatching → nest."""
    task = create_task(TaskCreate(title="Regressing egg", priority="low"))
    # advance first so there is somewhere to retreat from
    client.post(f"/tasks/{task.id}/move", data={"direction": "forward"}, follow_redirects=False)
    assert get_task_by_id(task.id).status == "hatching"

    response = client.post(
        f"/tasks/{task.id}/move",
        data={"direction": "back"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert get_task_by_id(task.id).status == "nest"


def test_move_task_at_final_status_stays_put(client: TestClient) -> None:
    """Moving a flown task forward is a no-op — status remains flown."""
    task = create_task(TaskCreate(title="Already flown", priority="low"))
    client.post(f"/tasks/{task.id}/move", data={"direction": "forward"}, follow_redirects=False)
    client.post(f"/tasks/{task.id}/move", data={"direction": "forward"}, follow_redirects=False)
    assert get_task_by_id(task.id).status == "flown"

    response = client.post(
        f"/tasks/{task.id}/move",
        data={"direction": "forward"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert get_task_by_id(task.id).status == "flown"


def test_move_task_at_first_status_backward_stays_put(client: TestClient) -> None:
    """Moving a nest task backward is a no-op — status remains nest."""
    task = create_task(TaskCreate(title="Nest-bound egg", priority="low"))

    response = client.post(
        f"/tasks/{task.id}/move",
        data={"direction": "back"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert get_task_by_id(task.id).status == "nest"


def test_move_invalid_direction(client: TestClient) -> None:
    """POST /tasks/{id}/move with an unknown direction returns 400."""
    task = create_task(TaskCreate(title="Confused egg", priority="low"))

    response = client.post(
        f"/tasks/{task.id}/move",
        data={"direction": "sideways"},
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_move_nonexistent_task(client: TestClient) -> None:
    """POST /tasks/{id}/move with an unknown ID returns 404."""
    response = client.post(
        "/tasks/nonexistent-id/move",
        data={"direction": "forward"},
        follow_redirects=False,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Health / ops endpoints
# ---------------------------------------------------------------------------


def test_healthz_returns_ok(client: TestClient) -> None:
    """GET /healthz returns 200 with status ok."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_returns_ok_when_db_available(client: TestClient) -> None:
    """GET /readyz returns 200 when the database is reachable."""
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_get_nonexistent_task(client: TestClient) -> None:
    """GET /tasks/{id}/edit with an unknown ID returns 404."""
    response = client.get("/tasks/nonexistent-uuid/edit")

    assert response.status_code == 404


def test_error_response_has_detail_field(client: TestClient) -> None:
    """404 error responses include a 'detail' field in the JSON body."""
    response = client.get("/tasks/nonexistent/edit")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body


def test_request_id_header_propagated(client: TestClient) -> None:
    """X-Request-ID sent in request is echoed back in the response."""
    response = client.get("/healthz", headers={"X-Request-ID": "test-abc-123"})
    assert response.headers.get("x-request-id") == "test-abc-123"


def test_request_id_generated_when_absent(client: TestClient) -> None:
    """A UUID X-Request-ID is generated and returned when the header is missing."""
    response = client.get("/healthz")
    assert "x-request-id" in response.headers
    rid = response.headers["x-request-id"]
    assert len(rid) == 36  # UUID4 format
