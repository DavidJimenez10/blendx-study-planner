# AI Study Planner Infrastructure

Infrastructure as Code (CDK TypeScript) for the BlendX Study Planner. Defines networking (VPC, subnets), compute (ECS Fargate), database (RDS PostgreSQL), load balancing (ALB), secrets (Secrets Manager), and CI/CD (GitHub Actions + Amplify).

**Tech Stack**: AWS CDK 2, TypeScript, Node.js 22+
**Package Manager**: `npm`

## Project map
- `bin/` - CDK app entry point
- `lib/` - Stack definitions (`networking-stack.ts`, `app-stack.ts`)
- `test/` - CDK snapshot tests
- `cdk.json` - CDK configuration (app command, context)
- `cdk.context.json` - CDK context values (VPC lookups, AZ mappings)

<important if="you need to run CDK commands (synth, deploy, diff, destroy)">
Run from the `infra/` directory.

| Command | Description |
|---|---|
| `npm run build` | Compile TypeScript to JS (`tsc`) |
| `cdk synth` | Synthesize CloudFormation templates without deploying |
| `cdk diff` | Show differences between deployed stack and local code |
| `cdk deploy --all` | Deploy all stacks to AWS |
| `cdk deploy NetworkingStack` | Deploy only the networking stack |
| `cdk deploy AppStack` | Deploy only the app stack |
| `cdk destroy --all` | Destroy all stacks (tear down entire environment) |
| `npm test` | Run CDK snapshot tests |

First deployment must be `cdk deploy NetworkingStack` followed by `cdk deploy AppStack` (AppStack depends on VPC resources from NetworkingStack). Together, `cdk deploy --all` handles this ordering automatically.

After `cdk deploy AppStack`, copy the CfnOutput values to GitHub repository secrets for CI/CD and to the Amplify console for `VITE_API_URL`.
</important>

<important if="you need to understand or modify the CI/CD pipeline">
- See `.github/workflows/deploy.yml` for the workflow definition.
- See `docs/adr/0003-cicd-oidc-pipeline.md` for the rationale behind OIDC auth and double-tag strategy.
- GitHub Actions uses OIDC to authenticate to AWS. The IAM role ARN must be stored as `AWS_ROLE_ARN` in GitHub Secrets.
- Required GitHub Secrets (set manually after first `cdk deploy`): `AWS_ROLE_ARN`, `ECR_REPOSITORY`, `ECS_CLUSTER`, `ECS_SERVICE`, `ECS_TASK_DEF_FAMILY`, `AWS_REGION`.
</important>

<important if="you need to understand or modify the Amplify configuration">
- See `amplify.yml` at the repository root for the Amplify build specification.
- The frontend expects `VITE_API_URL` as an Amplify environment variable pointing to the ALB DNS (obtained from the `AlbDnsName` CfnOutput after `cdk deploy`).
</important>
