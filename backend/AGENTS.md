# AI Study Planner Backend

Backend API for the AI Study Planner application, handling user authentication, study plans, and task management.

**Tech Stack**: Python 3.12, FastAPI, SQLAlchemy (PostgreSQL), Alembic, Pydantic, and Pytest.
**Package Manager**: `uv`

## Project map
- `app/api/`: FastAPI routers and endpoints.
- `app/core/`: Configuration, database sessions, and security utilities.
- `app/models/`: SQLAlchemy ORM models.
- `app/schemas/`: Pydantic models (DTOs) for request/response validation.
- `app/repositories/`: Data access layer (database queries).
- `app/services/`: Core business logic.
- `tests/`: Pytest test suite.

<important if="you need to run commands to start the server, test, or manage dependencies and migrations">

Run with `uv` from the `backend/` directory.

| Command | What it does |
|---|---|
| `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` | Start dev server |
| `uv run pytest` | Run all tests |
| `uv add <package>` | Add dependency (use `--dev` for dev dependencies) |
| `uv run alembic revision --autogenerate -m "message"` | Generate database migration |
| `uv run alembic upgrade head` | Run database migrations |

</important>
