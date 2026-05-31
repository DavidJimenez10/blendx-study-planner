# Context Map

## Contexts

- [Backend](./backend/CONTEXT.md) -- Python/FastAPI API layer: authentication, study plans, and tasks
- [Frontend](./frontend/CONTEXT.md) -- React/TypeScript UI: dashboard, plan detail, and authentication pages
- [Infrastructure](./infra/CONTEXT.md) -- AWS CDK stacks, CI/CD pipeline, and Amplify hosting config

## Relationships

- **Frontend -> Backend**: Frontend consumes REST API from Backend. Authenticated via JWT Bearer token. In development, Vite proxies `/api` to the backend. In production, `VITE_API_URL` points to the ALB DNS.
- **Backend -> PostgreSQL**: Backend stores all persistent data in PostgreSQL via SQLAlchemy ORM. Migrations managed by Alembic.
- **Infrastructure -> Backend**: Infrastructure deploys the backend via ECS Fargate. The CI/CD pipeline (`.github/workflows/deploy.yml`) builds the Docker image from `backend/`, pushes it to ECR, registers a new task definition revision referencing the Secrets Manager secret for `DATABASE_URL`/`JWT_SECRET`/`OPENAI_API_KEY`, and forces an ECS service update. The FastAPI application runs inside the Fargate container and connects to RDS PostgreSQL provisioned by the CDK.
- **Infrastructure -> Frontend**: Infrastructure defines the frontend deployment via `amplify.yml`. Amplify builds `frontend/` with `npm ci && npm run build` and serves the output through a CDN. The `VITE_API_URL` environment variable (configured in the Amplify console) tells the frontend where the backend ALB lives.
- **Frontend -> Infrastructure**: The frontend reads `VITE_API_URL` — the ALB DNS exported by Infrastructure as a CfnOutput — to reach the backend API in production.
