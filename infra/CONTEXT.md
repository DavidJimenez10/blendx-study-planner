# Infrastructure

Defines, versions, and deploys all AWS resources for the BlendX Study Planner. Includes CDK stacks (Networking + App), the CI/CD pipeline (GitHub Actions), and the Amplify frontend hosting config.

## Language

### CDK

**Stack**:
A group of AWS resources deployed as a single unit. Two stacks: `NetworkingStack` (VPC, subnets, Internet Gateway) and `AppStack` (ECS, RDS, ALB, ECR, Secrets Manager, Security Groups, IAM Roles).
_Avoid_: Template, construct tree

**Security Group**:
A virtual firewall attached to a specific resource. Three groups: `ALB-SG` (ingress :80/:443 from 0.0.0.0/0), `Fargate-SG` (ingress :8000 from ALB-SG only), `RDS-SG` (ingress :5432 from Fargate-SG only).
_Avoid_: Firewall rule, network ACL

**CfnOutput**:
A value exported by CDK after `cdk deploy`, intended for manual copy to GitHub Secrets or Amplify env vars. Includes `EcsClusterName`, `EcsServiceName`, `TaskDefFamily`, `EcrRepoUri`, and `AlbDnsName`.
_Avoid_: Stack output, export

**Secret**:
A single JSON secret in AWS Secrets Manager with three fields: `DATABASE_URL` (auto-generated from RDS credentials), `JWT_SECRET` (auto-generated), and `OPENAI_API_KEY` (placeholder, filled manually via AWS console).
_Avoid_: Env vars, config secret

### CI/CD

**Deploy workflow**:
A GitHub Actions workflow at `.github/workflows/deploy.yml`. Triggers on `pull_request.closed + merged == true` targeting `main` when files under `backend/` change. Two jobs: `build-and-push` (builds Docker image, tags it, pushes to ECR) and `deploy` (registers a new ECS task definition revision and forces a new deployment).
_Avoid_: Release pipeline, CI job

**OIDC**:
OpenID Connect authentication between GitHub Actions and AWS. GitHub issues a short-lived JWT token; AWS IAM trusts it via `AssumeRoleWithWebIdentity`. No long-lived access keys are stored in repository secrets.
_Avoid_: Access key auth, static credentials

**Double-tag strategy**:
Every Docker image pushed to ECR receives two tags: `${{ github.sha }}` (traceable to the exact commit) and `latest` (so the initial CDK task definition always resolves). After deployment, ECS registers a new task definition revision pinned to the SHA-tagged image.
_Avoid_: Single tag, release tag

### Amplify

**Amplify App**:
An AWS Amplify application connected to this GitHub repository. Builds the Vite frontend via `amplify.yml` (`cd frontend && npm ci` then `npm run build`) and serves the output (`frontend/dist/`) through a CDN. Deploys automatically when `main` changes.
_Avoid_: Static hosting, S3 website

**VITE_API_URL**:
Environment variable set in the Amplify console to the ALB DNS. The frontend reads it via `import.meta.env.VITE_API_URL` and falls back to `/api` (Vite dev proxy). This is the bridge between the Amplify-hosted frontend and the ECS-hosted backend.
_Avoid_: API endpoint, backend URL
