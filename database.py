"""SQLite database initialisation and CRUD functions for To Hatch."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from typing import Generator
from uuid import uuid4

from models import TaskCreate, TaskResponse, TaskUpdate

logger = logging.getLogger(__name__)

DB_PATH = "hatch.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'nest'
                    CHECK(status IN ('nest', 'hatching', 'flown')),
    priority    TEXT NOT NULL DEFAULT 'low'
                    CHECK(priority IN ('low', 'medium', 'high')),
    due_date    TEXT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


@contextmanager
def _get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Yield a function-scoped SQLite connection and close it on exit.

    WAL journal mode is enabled so reads do not block writes and the
    database is safe for concurrent access from multiple threads.

    Yields:
        An open :class:`sqlite3.Connection` with :attr:`sqlite3.Row`
        as the row factory.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def _row_to_response(row: sqlite3.Row) -> TaskResponse:
    """Convert a database row to a :class:`TaskResponse`.

    Args:
        row: A :class:`sqlite3.Row` from the tasks table.

    Returns:
        A fully populated :class:`TaskResponse` instance.
    """
    return TaskResponse(
        id=row["id"],
        title=row["title"],
        status=row["status"],
        priority=row["priority"],
        due_date=row["due_date"],
        created_at=row["created_at"],
    )


def init_db() -> None:
    """Create the tasks table and required indexes if they do not already exist.

    Raises:
        sqlite3.DatabaseError: If the schema cannot be created.
    """
    with _get_connection() as conn:
        conn.execute(_CREATE_TABLE_SQL)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"
        )
        conn.commit()
    logger.debug("Database initialised at %s", DB_PATH)


def create_task(task: TaskCreate) -> TaskResponse:
    """Insert a new task and return the persisted record.

    Args:
        task: Validated task creation payload.

    Returns:
        The newly created task as a :class:`TaskResponse`.

    Raises:
        sqlite3.DatabaseError: If the insert fails.
    """
    task_id = str(uuid4())
    sql = """
        INSERT INTO tasks (id, title, priority, due_date)
        VALUES (?, ?, ?, ?)
    """
    with _get_connection() as conn:
        conn.execute(sql, (task_id, task.title, task.priority, task.due_date))
        conn.commit()
    logger.debug("Created task %s", task_id)
    return get_task_by_id(task_id)


def get_all_tasks() -> list[TaskResponse]:
    """Return all tasks ordered by creation time (oldest first).

    Returns:
        A list of :class:`TaskResponse` objects, possibly empty.

    Raises:
        sqlite3.DatabaseError: If the query fails.
    """
    sql = "SELECT * FROM tasks ORDER BY created_at ASC"
    with _get_connection() as conn:
        rows = conn.execute(sql).fetchall()
    return [_row_to_response(row) for row in rows]


def get_task_by_id(task_id: str) -> TaskResponse:
    """Fetch a single task by its UUID.

    Args:
        task_id: The UUID4 string identifier of the task.

    Returns:
        The matching :class:`TaskResponse`.

    Raises:
        KeyError: If no task with the given ID exists.
        sqlite3.DatabaseError: If the query fails.
    """
    sql = "SELECT * FROM tasks WHERE id = ?"
    with _get_connection() as conn:
        row = conn.execute(sql, (task_id,)).fetchone()
    if row is None:
        raise KeyError(task_id)
    return _row_to_response(row)


def update_task(task_id: str, update: TaskUpdate) -> TaskResponse:
    """Apply a partial update to an existing task.

    Only fields that are not ``None`` in *update* are written.

    Args:
        task_id: The UUID4 string identifier of the task to update.
        update: Partial update payload; ``None`` fields are ignored.

    Returns:
        The updated task as a :class:`TaskResponse`.

    Raises:
        KeyError: If no task with the given ID exists.
        ValueError: If *update* contains no fields to change.
        sqlite3.DatabaseError: If the update fails.
    """
    fields = {k: v for k, v in update.model_dump().items() if v is not None}
    if not fields:
        raise ValueError("No fields provided for update.")

    set_clause = ", ".join(f"{col} = ?" for col in fields)
    sql = f"UPDATE tasks SET {set_clause} WHERE id = ?"  # noqa: S608 — clause built from model keys, not user input
    params = [*fields.values(), task_id]

    with _get_connection() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        if cursor.rowcount == 0:
            raise KeyError(task_id)

    logger.debug("Updated task %s fields=%s", task_id, list(fields))
    return get_task_by_id(task_id)


def delete_task(task_id: str) -> None:
    """Delete a task by its UUID.

    Args:
        task_id: The UUID4 string identifier of the task to delete.

    Raises:
        KeyError: If no task with the given ID exists.
        sqlite3.DatabaseError: If the delete fails.
    """
    sql = "DELETE FROM tasks WHERE id = ?"
    with _get_connection() as conn:
        cursor = conn.execute(sql, (task_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise KeyError(task_id)
    logger.debug("Deleted task %s", task_id)
