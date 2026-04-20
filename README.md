# to-hatch

> Egg-themed Kanban task manager built with FastAPI and SQLite.

![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![Ruff](https://img.shields.io/badge/lint-ruff-261230)
![mypy](https://img.shields.io/badge/types-mypy%20strict-1F5082)
![Coverage](https://img.shields.io/badge/coverage-%E2%89%A585%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## About

`to-hatch` is a themed Kanban board: tasks are **eggs**, columns are **baskets**, and work moves from `to-hatch` through `hatching` to `hatched`. It was built as a self-contained demo for a technical interview, with the constraint that every layer (API, data, UI, tests, tooling) should be legible end-to-end inside a single afternoon of reading.

The stack is deliberately small: FastAPI for the web layer, Jinja templates for the UI, SQLite for persistence, pytest for verification. The scaffolding around it (Ruff, mypy strict, pytest-cov, bandit) is production-grade even though the app is not, because the point of the exercise is to show the *shape* of how I work, not the scale of the problem.

## Quickstart

```bash
# Clone
git clone https://github.com/diskdog/to-hatch.git
cd to-hatch

# Install (pick one)
uv sync                                    # recommended, if you have uv
pip install -r requirements.txt            # fallback

# Run
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

<!-- If the entrypoint isn't `main:app`, swap for the correct module:attribute -->

## Development

```bash
# Run the test suite with coverage
pytest

# Lint
ruff check .

# Format
ruff format .

# Type-check
mypy .

# Security scan
bandit -r . -c pyproject.toml
```

## Quality gates

The repo is configured to enforce:

- **Ruff** with Google-style docstrings (`pydocstyle` convention = google), plus the `E`, `W`, `F`, `I`, `N`, `D`, `UP`, `B`, `C4`, `SIM`, `PL`, and `S` rule sets.
- **mypy strict mode** with the Pydantic plugin.
- **pytest** with a coverage floor of 85%; builds fail below that.
- **bandit** for basic SAST, configured in `pyproject.toml`.

Configuration lives in `pyproject.toml` rather than scattered dotfiles, so a reviewer has exactly one place to look.

## Project layout

```
to-hatch/
├── main.py              # FastAPI app + route definitions
├── models.py            # Pydantic models
├── database.py          # SQLite connection + queries
├── middleware.py        # Request ID, logging, error handlers
├── config.py            # Pydantic settings
├── logging_config.py    # structlog setup
├── templates/           # Jinja templates
├── static/              # CSS, JS, assets
├── tests/               # pytest suite
├── pyproject.toml       # single source of truth for tooling
├── PLAN.md              # design notes and build plan
└── README.md
```

## Design notes

See [`PLAN.md`](./PLAN.md) for the full build plan, architectural choices, and trade-offs considered during the sprint.

## License

MIT. See [`LICENSE`](./LICENSE).
