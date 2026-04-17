# To Hatch — Task Manager

## Scope
- Create, edit, complete, delete tasks
- Due date and priority fields
- Local persistence (SQLite)
- Kanban board: Nest (to do), Hatching (in progress), Flown the Pond (done)
- Egg-themed task cards, colour-coded by priority
- Task emoji evolves by column: 🥚 in Nest, 🐣 in Hatching, 🦆 in Flown the Pond
- Unit tests for core operations
- Filter and sort (stretch)

## Stack
- Python 3.12 / FastAPI
- SQLite for persistence
- Jinja2 templates + vanilla HTML/CSS for frontend
- pytest for testing
- No frontend framework; server-rendered

## Architecture
- main.py: FastAPI app, routes
- database.py: SQLite connection and CRUD operations (hatch.db)
- models.py: Pydantic models for Task
- templates/: Jinja2 HTML templates
- static/: CSS
- tests/: pytest test suite

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
5. Unit tests (mins 24–27)
6. Self-review (mins 27–30)

## Non-Functional Requirements
- Input validation: Pydantic enforces type and field constraints on all inputs
- Error handling: graceful handling of missing tasks (404), invalid data (422), database errors (500)
- Security: all SQL queries use parameterised statements, no string interpolation
- Performance: SQLite is single-file, appropriate for local single-user use; would move to PostgreSQL for multi-user
- Data integrity: CHECK constraints on status and priority columns at the database level
- Accessibility: semantic HTML, form labels, readable contrast ratios

## Deferred
- Drag-and-drop (JS complexity, not worth the time)
- Calendar integration
- Authentication
- Docker containerisation
- Filter/sort (stretch if time permits after tests)

## Definition of Done
- App runs locally on uvicorn
- Full CRUD on tasks via the browser
- Tasks persist in SQLite across server restarts
- Kanban view with three columns
- Task cards visually themed with egg shapes and column-based emoji
- Core CRUD operations covered by passing tests
