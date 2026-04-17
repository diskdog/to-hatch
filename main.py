"""FastAPI application entry point for To Hatch."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import init_db


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
    """Render the application home page.

    Args:
        request: The incoming HTTP request.

    Returns:
        An HTML response containing the rendered index template.
    """
    return templates.TemplateResponse("index.html", {"request": request})
