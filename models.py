"""Pydantic data models for the To Hatch task manager."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Request model for creating a new task.

    Attributes:
        title: The task title, required and non-empty.
        priority: Urgency level; defaults to ``"low"``.
        due_date: Optional ISO-8601 date string (YYYY-MM-DD).
    """

    title: str = Field(..., min_length=1)
    priority: Literal["low", "medium", "high"] = "low"
    due_date: str | None = None


class TaskUpdate(BaseModel):
    """Request model for partially updating an existing task.

    Only fields set to a non-``None`` value are written to the database.

    Attributes:
        title: New task title, if changing.
        status: New workflow status, if changing.
        priority: New urgency level, if changing.
        due_date: New due date string, or ``None`` to clear.
    """

    title: str | None = Field(default=None, min_length=1)
    status: Literal["nest", "hatching", "flown"] | None = None
    priority: Literal["low", "medium", "high"] | None = None
    due_date: str | None = None


class TaskResponse(BaseModel):
    """Full task representation returned from the API.

    Attributes:
        id: UUID4 string primary key.
        title: Task title.
        status: Workflow column (``"nest"``, ``"hatching"``, or ``"flown"``).
        priority: Urgency level (``"low"``, ``"medium"``, or ``"high"``).
        due_date: Optional ISO-8601 date string.
        created_at: ISO-8601 timestamp when the task was created.
    """

    id: str
    title: str
    status: Literal["nest", "hatching", "flown"]
    priority: Literal["low", "medium", "high"]
    due_date: str | None
    created_at: str


class ErrorResponse(BaseModel):
    """Standard JSON error envelope returned by the global exception handler.

    Attributes:
        detail: Human-readable error message.
        request_id: Propagated ``X-Request-ID`` for log correlation.
    """

    detail: str
    request_id: str | None = None
