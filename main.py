"""FastAPI application entry point for To Hatch."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import structlog
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from database import (
    create_task,
    delete_task,
    get_all_tasks,
    get_task_by_id,
    init_db,
    update_task,
)
from logging_config import configure_logging
from middleware import RequestIDMiddleware
from models import ErrorResponse, TaskCreate, TaskUpdate

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_NEXT_STATUS: dict[str, str] = {"nest": "hatching", "hatching": "flown"}
_PREV_STATUS: dict[str, str] = {"hatching": "nest", "flown": "hatching"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Configures structured logging and initialises the SQLite database on
    startup, then yields control to the running application.

    Args:
        app: The :class:`FastAPI` application instance.

    Yields:
        Control to the running application.
    """
    configure_logging()
    init_db()
    log = logging.getLogger(__name__)
    log.info("To Hatch started", extra={"db_path": settings.db_path})
    yield
    log.info("To Hatch shutting down")


app = FastAPI(
    title=settings.app_name,
    description=(
        "An egg-themed Kanban task manager. "
        "Tasks move through three columns: **Nest** → **Hatching** → **Flown**."
    ),
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug,
)

# --- Middleware -----------------------------------------------------------

app.add_middleware(RequestIDMiddleware)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Static files and templates ------------------------------------------

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- Global exception handler --------------------------------------------


@app.exception_handler(Exception)
async def _unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Return a structured JSON error envelope for any unhandled exception.

    Args:
        request: The request that triggered the exception.
        exc: The unhandled exception.

    Returns:
        A 500 JSON response containing a stable error envelope.
    """
    request_id: str | None = getattr(request.state, "request_id", None)
    logger.exception("Unhandled exception", exc_info=exc, request_id=request_id)
    body = ErrorResponse(detail="Internal server error.", request_id=request_id)
    return JSONResponse(status_code=500, content=body.model_dump())


@app.exception_handler(HTTPException)
async def _http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Return a structured JSON error envelope for HTTP exceptions.

    Args:
        request: The request that triggered the exception.
        exc: The :class:`HTTPException` raised by a route handler.

    Returns:
        A JSON response with the appropriate HTTP status code.
    """
    request_id: str | None = getattr(request.state, "request_id", None)
    body = ErrorResponse(detail=str(exc.detail), request_id=request_id)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


# --- Health endpoints ----------------------------------------------------


@app.get(
    "/healthz",
    tags=["ops"],
    summary="Liveness probe",
    description="Returns 200 if the process is alive.",
)
async def healthz() -> dict[str, str]:
    """Return a simple liveness response.

    Returns:
        A JSON object with ``{"status": "ok"}``.
    """
    return {"status": "ok"}


@app.get(
    "/readyz",
    tags=["ops"],
    summary="Readiness probe",
    description="Returns 200 when the database is reachable, 503 otherwise.",
)
async def readyz() -> JSONResponse:
    """Check database connectivity and return a readiness response.

    Returns:
        200 with ``{"status": "ok"}`` if the database is reachable;
        503 with ``{"status": "degraded", "detail": ...}`` otherwise.
    """
    try:
        get_all_tasks()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Readiness check failed", error=str(exc))
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "detail": str(exc)},
        )
    return JSONResponse(status_code=200, content={"status": "ok"})


# --- Board routes --------------------------------------------------------


@app.get(
    "/",
    response_class=HTMLResponse,
    tags=["board"],
    summary="Kanban board",
    description="Render the Kanban board with all tasks grouped by status.",
)
async def index(request: Request) -> Any:
    """Render the Kanban board with all tasks.

    Args:
        request: The incoming HTTP request.

    Returns:
        An HTML response containing the rendered index template.
    """
    tasks = get_all_tasks()
    return templates.TemplateResponse(request, "index.html", {"tasks": tasks})


# --- Task CRUD routes ----------------------------------------------------


@app.post(
    "/tasks",
    tags=["tasks"],
    summary="Create task",
    description="Create a new task and redirect to the board.",
    status_code=303,
)
async def task_create(
    title: str = Form(..., min_length=1),
    priority: str = Form("low"),
    due_date: str | None = Form(None),
) -> RedirectResponse:
    """Create a new task from form data.

    Args:
        title: Task title (required, non-empty).
        priority: Urgency level; defaults to ``"low"``.
        due_date: Optional ISO-8601 date string.

    Returns:
        A 303 redirect to the board root.
    """
    create_task(TaskCreate(title=title, priority=priority, due_date=due_date or None))
    return RedirectResponse("/", status_code=303)


@app.get(
    "/tasks/{task_id}/edit",
    response_class=HTMLResponse,
    tags=["tasks"],
    summary="Edit task form",
    description="Render the edit form for a specific task.",
)
async def task_edit_form(task_id: str, request: Request) -> Any:
    """Render the edit form for an existing task.

    Args:
        task_id: UUID4 identifier of the task to edit.
        request: The incoming HTTP request.

    Returns:
        An HTML response containing the rendered edit template.

    Raises:
        HTTPException: 404 if *task_id* does not exist.
    """
    try:
        task = get_task_by_id(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    return templates.TemplateResponse(request, "edit.html", {"task": task})


@app.post(
    "/tasks/{task_id}/edit",
    tags=["tasks"],
    summary="Update task",
    description="Apply edits to a task and redirect to the board.",
    status_code=303,
)
async def task_edit_submit(
    task_id: str,
    title: str = Form(...),
    priority: str = Form(...),
    due_date: str | None = Form(None),
) -> RedirectResponse:
    """Apply edits to an existing task.

    Args:
        task_id: UUID4 identifier of the task to update.
        title: New task title.
        priority: New urgency level.
        due_date: New due date, or omitted to clear.

    Returns:
        A 303 redirect to the board root.

    Raises:
        HTTPException: 404 if *task_id* does not exist.
    """
    try:
        update_task(
            task_id,
            TaskUpdate(title=title, priority=priority, due_date=due_date or None),
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    return RedirectResponse("/", status_code=303)


@app.post(
    "/tasks/{task_id}/delete",
    tags=["tasks"],
    summary="Delete task",
    description="Delete a task and redirect to the board.",
    status_code=303,
)
async def task_delete(task_id: str) -> RedirectResponse:
    """Delete a task by ID.

    Args:
        task_id: UUID4 identifier of the task to delete.

    Returns:
        A 303 redirect to the board root.

    Raises:
        HTTPException: 404 if *task_id* does not exist.
    """
    try:
        delete_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    return RedirectResponse("/", status_code=303)


@app.post(
    "/tasks/{task_id}/move",
    tags=["tasks"],
    summary="Move task",
    description=(
        "Advance or retreat a task's status. "
        "``direction=forward`` moves nest→hatching→flown; "
        "``direction=back`` reverses."
    ),
    status_code=303,
)
async def task_move(
    task_id: str, direction: str = Form(...)
) -> RedirectResponse:
    """Change a task's Kanban column.

    Args:
        task_id: UUID4 identifier of the task to move.
        direction: ``"forward"`` to advance or ``"back"`` to retreat.

    Returns:
        A 303 redirect to the board root.

    Raises:
        HTTPException: 400 if *direction* is not ``"forward"`` or ``"back"``.
        HTTPException: 404 if *task_id* does not exist.
    """
    try:
        task = get_task_by_id(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")

    if direction == "forward":
        new_status = _NEXT_STATUS.get(task.status)
    elif direction == "back":
        new_status = _PREV_STATUS.get(task.status)
    else:
        raise HTTPException(status_code=400, detail="Invalid direction")

    if new_status:
        update_task(task_id, TaskUpdate(status=new_status))

    return RedirectResponse("/", status_code=303)
