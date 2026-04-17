# To Hatch — Task Manager
## Scope
- Create, edit, complete, delete tasks
- Due date and priority fields
- Local persistence (SQLite)
- Kanban board: Nest (to do), Hatching (in progress), Flown the Pond (done)
- Egg-themed task cards, colour-coded by priority
- Task emoji evolves by column: 🥚 in Nest, 🐣 in Hatching, 🦆 in Flown the Pond
- Tests for core CRUD operations

## Stack
- Python 3.10+ / FastAPI
- SQLite for persistence
- Jinja2 templates + vanilla HTML/CSS for frontend
- pytest + httpx TestClient for testing
- No frontend framework; server-rendered

## Architecture
- main.py: FastAPI app, routes
- database.py: SQLite CRUD operations (hatch.db), function-scoped connections via context managers
- models.py: Pydantic models for Task
- templates/: Jinja2 HTML templates
- static/: CSS
- tests/: pytest test suite
- requirements.txt: pinned dependencies

## Data Model
- Task status values: 'nest', 'hatching', 'flown' (CHECK constraint at DB level)
- Priority values: 'low', 'medium', 'high' (CHECK constraint at DB level)
- IDs: UUID4 strings
- All SQL uses parameterised queries

## Priority Order
1. Database + API scaffold (mins 2–7)
2. CRUD routes + basic HTML template (mins 7–13)
3. Kanban board layout (mins 13–20)
4. Egg visuals + theming (mins 20–24)
5. Integration tests (mins 24–27)
6. Self-review (mins 27–30)

## Development Practices
- Code style: Google Python Style Guide (type annotations, Google-style docstrings, proper imports)
- Commit style: Beams' seven rules (imperative mood, 50-char subject, 72-char body wrap)

## Non-Functional Requirements
- Input validation: Pydantic enforces type and field constraints on all inputs
- Error handling: graceful handling of missing tasks (404), invalid data (422), database errors (500)
- Security: all SQL queries use parameterised statements, no string interpolation
- Performance: SQLite is single-file, appropriate for local single-user use; would move to PostgreSQL for multi-user
- Data integrity: CHECK constraints on status and priority columns at the database level
- Accessibility: semantic HTML, form labels, readable contrast ratios

## Deferred
- Drag-and-drop (JS complexity, not worth the time)
- Filter/sort (stretch if time permits after tests)
- Calendar integration
- Authentication
- Docker containerisation

## Definition of Done
- App runs locally on uvicorn
- Full CRUD on tasks via the browser
- Tasks persist in SQLite across server restarts
- Kanban view with three columns
- Task cards visually themed with egg shapes and column-based emoji
- Core CRUD operations covered by passing tests