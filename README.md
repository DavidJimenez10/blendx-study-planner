# AI Study Planner

A study planning app to organize goals, plans, and tasks. JWT-based auth, progress tracking, and target dates.

## Stack

| Layer      | Technology                                    |
|------------|-----------------------------------------------|
| Backend    | Python 3.12, FastAPI, SQLAlchemy 2, uv        |
| Database   | PostgreSQL 16                                 |
| Migrations | Alembic                                       |
| Frontend   | React 18, TypeScript, Vite, Mantine 7         |
| Container  | Docker Compose                                |

## Quick Start

```bash
docker compose up --build
```

On first boot the backend automatically runs migrations and seeds the database with sample data.

| Service   | URL                         |
|-----------|-----------------------------|
| Frontend  | http://localhost:5173       |
| API       | http://localhost:8000       |
| API Docs  | http://localhost:8000/docs  |

> If port 8000 is already in use, change `"8000:8000"` to `"8001:8000"` in `docker-compose.yml`.

## Seed Data

The seeder runs automatically on every `compose up` (idempotent — skips if the admin user already exists).

| Credential | Value      |
|------------|------------|
| Username   | `admin`    |
| Password   | `admin123` |

Four sample plans are created (AWS cert, TypeScript, Clean Code, System Design) with multiple tasks at various completion states so you can see the progress bars and date badges in action.

To re-seed from scratch, remove the database volume and restart:

```bash
docker compose down -v && docker compose up --build
```

## API Endpoints

| Method | Path                            | Description              |
|--------|---------------------------------|--------------------------|
| POST   | /auth/register                  | Create account           |
| POST   | /auth/login                     | Sign in, get JWT         |
| GET    | /users/{id}/plans               | List user's plans        |
| POST   | /plans                          | Create study plan        |
| GET    | /plans/{id}                     | Get study plan           |
| PATCH  | /plans/{id}                     | Update plan              |
| POST   | /plans/{id}/tasks               | Add task to plan         |
| GET    | /plans/{id}/tasks               | List tasks               |
| PATCH  | /plans/{id}/tasks/{taskId}      | Toggle task completion   |

## Development

### Backend tests

```bash
cd backend
uv sync --all-groups
uv run pytest tests/ -v
```

### Backend only (no Docker)

```bash
cd backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/study_planner \
  uv run uvicorn app.main:app --reload
```

### Frontend only (no Docker)

```bash
cd frontend
npm install
npm run dev
```

## AWS Deployment

The application can be deployed to AWS using CDK (Infrastructure as Code), ECS Fargate (backend), Amplify (frontend), and RDS PostgreSQL.

### Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) configured with administrator credentials
- [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) (`npm install -g aws-cdk && cdk bootstrap`)
- [Node.js 22+](https://nodejs.org/)
- [Docker](https://www.docker.com/) (for building the backend image locally to verify)
- A [GitHub](https://github.com) repository connected to this codebase

### Step 1: Deploy infrastructure

```bash
cd infra
npm install
cdk deploy --all
```

This provisions all AWS resources: VPC with public/private subnets, ECR repository, ECS Fargate cluster and service, RDS PostgreSQL 16.4, Application Load Balancer, and Secrets Manager. After deployment, CDK prints the following outputs:

| CfnOutput          | Use for                          |
|--------------------|----------------------------------|
| `EcrRepoUri`       | GitHub Secret `ECR_REPOSITORY`   |
| `EcsClusterName`   | GitHub Secret `ECS_CLUSTER`      |
| `EcsServiceName`   | GitHub Secret `ECS_SERVICE`      |
| `TaskDefFamily`    | GitHub Secret `ECS_TASK_DEF_FAMILY` |
| `AlbDnsName`       | Amplify env var `VITE_API_URL`   |

### Step 2: Fill the OpenAI API key

Go to AWS Console > Secrets Manager, locate the secret created by the CDK, and edit the `OPENAI_API_KEY` field with your actual key.

### Step 3: Set up GitHub OIDC and secrets

1. Create an OIDC provider in IAM (AWS > IAM > Identity Providers > Add provider > OpenID Connect, URL: `https://token.actions.githubusercontent.com`, audience: `sts.amazonaws.com`).
2. Create an IAM role with a trust policy for the GitHub OIDC provider, scoped to your repository. Attach the permissions listed in `docs/prd/001-aws-deployment.md` (module 2, line 96).
3. Add the role ARN as `AWS_ROLE_ARN` in GitHub repository Secrets.
4. Copy each CfnOutput value from Step 1 into the corresponding GitHub Secret.

### Step 4: Connect Amplify

1. Go to AWS Amplify Console > New app > Host web app > GitHub, and select this repository.
2. Amplify auto-detects `amplify.yml` at the repository root.
3. In the Amplify app settings, add `VITE_API_URL` as an environment variable set to `http://<AlbDnsName>` (from Step 1).

The frontend will rebuild and deploy automatically when `main` changes. The CI/CD pipeline (`.github/workflows/deploy.yml`) will build and deploy the backend when a PR to `main` is merged with changes under `backend/`.

### Estimated monthly cost

| Resource            | Approx. cost |
|---------------------|--------------|
| RDS (db.t4g.micro)  | ~$15/mo      |
| ECS Fargate (0.25 vCPU / 0.5 GB) | ~$15/mo |
| Application Load Balancer | ~$20/mo |
| Secrets Manager     | ~$0.50/mo    |
| CloudWatch Logs     | ~$2-5/mo     |
| Amplify (free tier) | $0           |
| **Total**           | **~$50-70/mo** |

### Architecture diagram

```
Internet
  │
  ├─ :443 ──► ALB (public) ──► Fargate (public subnet, :8000)
  │               │                    │
  │               │                    ├─► ECR (Docker image)
  │               │                    ├─► Secrets Manager (DB URL, JWT, OpenAI key)
  │               │                    └─► RDS (private subnet, :5432)
  │
  └─ CDN ──► Amplify ──► frontend/dist/
                 │
                 └─► VITE_API_URL ──► ALB DNS
```

### Tear down

```bash
cd infra
cdk destroy --all
```

## Architecture

```
backend/app/
├── api/routers/   → HTTP layer (parse request, return response)
├── services/      → Business logic, raises 404s
├── repositories/  → Database access only
├── models/        → SQLAlchemy ORM models
├── schemas/       → Pydantic request/response models
├── core/          → Config, database session, JWT/bcrypt helpers
└── seed.py        → Idempotent sample data seeder

frontend/src/
├── api/           → API client and token helpers
├── components/
│   ├── layout/    → AppHeader
│   ├── routing/   → PrivateRoute
│   ├── plan/      → PlanCard, CreatePlanModal
│   └── task/      → TaskItem, AddTaskModal
└── pages/
    ├── auth/      → LoginPage
    ├── dashboard/ → Dashboard
    └── plans/     → PlanDetail
```
