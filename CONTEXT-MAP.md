# Context Map

## Contexts

- [Backend](./backend/CONTEXT.md) -- Python/FastAPI API layer: authentication, study plans, and tasks
- [Frontend](./frontend/CONTEXT.md) -- React/TypeScript UI: dashboard, plan detail, and authentication pages

## Relationships

- **Frontend -> Backend**: Frontend consumes REST API from Backend. Authenticated via JWT Bearer token. In development, Vite proxies `/api` to the backend. In production, `VITE_API_URL` points to the ALB DNS.
- **Backend -> PostgreSQL**: Backend stores all persistent data in PostgreSQL via SQLAlchemy ORM. Migrations managed by Alembic.
