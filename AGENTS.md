# AGENTS.md

AI Study Planner: Monorepo with a Python 3.12/FastAPI backend and React 18/TypeScript frontend to organize study goals.

## Project map
- `backend/` - Python API layer (FastAPI, SQLAlchemy, PostgreSQL, uv)
- `frontend/` - React UI (Vite, Mantine, npm)

<important if="you need to run commands to start the application or use docker compose">
| Command | Description |
|---|---|
| `docker compose up --build` | Spin up the entire application locally (auto-migrates and seeds DB) |

- **Frontend URL**: http://localhost:5173
- **API URL**: http://localhost:8000 (Swagger docs available at `/docs`)
- **Default Credentials**: `admin` / `admin123`
</important>

<important if="you are working on backend tasks">
- See `backend/AGENTS.md` for `uv` commands, testing steps, and specific backend architecture.
</important>

<important if="you are working on frontend tasks">
- See `frontend/AGENTS.md` for `npm` commands, build steps, and UI component structure.
</important>

<important if="you are working on infrastructure or CI/CD tasks">
- See `infra/AGENTS.md` for CDK commands (synth, deploy, diff, destroy), CI/CD pipeline details, and Amplify configuration.
- See `docs/prd/001-aws-deployment.md` for the full specification of all deployment modules.
- See `docs/adr/` for architecture decisions (Fargate in public subnets, single Dockerfile, OIDC CI/CD pipeline).
</important>

<important if="you need to understand or integrate with the REST API">
- See `README.md` for an overview of the API endpoints.
</important>

## Agent skills

### Issue tracker

GitHub Issues en `DavidJimenez10/blendx-study-planner` via `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Solo se usan `needs-info` y `ready-for-agent`. See `docs/agents/triage-labels.md`.

### Domain docs

Multi-context: `CONTEXT-MAP.md` en la raíz apunta a `CONTEXT.md` por cada contexto (`backend/`, `frontend/`). See `docs/agents/domain.md`.