"""FastAPI application entry point for To Hatch."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import (
    create_task,
    delete_task,
    get_all_tasks,
    get_task_by_id,
    init_db,
    update_task,
)
from models import TaskCreate, TaskUpdate

_NEXT_STATUS = {"nest": "hatching", "hatching": "flown"}
_PREV_STATUS = {"hatching": "nest", "flown": "hatching"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Initialises the SQLite database on startup.

    Args:
        app: The :class:`FastAPI` application instance.

    Yields:
        Control to the running application.
    """
    init_db()
    yield


app = FastAPI(title="To Hatch", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the Kanban board with all tasks.

    Args:
        request: The incoming HTTP request.

    Returns:
        An HTML response containing the rendered index template.
    """
    tasks = get_all_tasks()
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks})


@app.post("/tasks")
async def task_create(
    title: str = Form(...),
    priority: str = Form("low"),
    due_date: Optional[str] = Form(None),
) -> RedirectResponse:
    create_task(TaskCreate(title=title, priority=priority, due_date=due_date or None))
    return RedirectResponse("/", status_code=303)


@app.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
async def task_edit_form(task_id: str, request: Request) -> HTMLResponse:
    try:
        task = get_task_by_id(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    return templates.TemplateResponse("edit.html", {"request": request, "task": task})


@app.post("/tasks/{task_id}/edit")
async def task_edit_submit(
    task_id: str,
    title: str = Form(...),
    priority: str = Form(...),
    due_date: Optional[str] = Form(None),
) -> RedirectResponse:
    try:
        update_task(task_id, TaskUpdate(title=title, priority=priority, due_date=due_date or None))
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    return RedirectResponse("/", status_code=303)


@app.post("/tasks/{task_id}/delete")
async def task_delete(task_id: str) -> RedirectResponse:
    try:
        delete_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    return RedirectResponse("/", status_code=303)


@app.post("/tasks/{task_id}/move")
async def task_move(task_id: str, direction: str = Form(...)) -> RedirectResponse:
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
