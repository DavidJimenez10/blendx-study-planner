# BlendX Study Planner - Infrastructure (AWS CDK)

Este proyecto contiene la Infraestructura como Código (IaC) para desplegar el **BlendX Study Planner** en AWS utilizando AWS CDK v2 con TypeScript.

## Arquitectura

La arquitectura está diseñada como una solución "Serverless/Managed" optimizada para un MVP (~$50-70/mes).

- **Frontend:** AWS Amplify (React/Vite).
- **Backend:** ECS Fargate (FastAPI) corriendo en subredes públicas (por ahorro de costos frente a NAT Gateway), protegido por un Security Group estricto.
- **Base de Datos:** RDS PostgreSQL 16.x (Single-AZ) en subredes privadas.
- **Balanceador de Carga:** Application Load Balancer (ALB) público ruteando tráfico al contenedor de Fargate.
- **Secretos:** AWS Secrets Manager gestiona credenciales de BD y llaves (inyectadas al contenedor vía CDK).
- **Workaround HTTPS (CloudFront):** Debido a que no usamos un dominio propio, se debe aprovisionar manualmente una distribución de Amazon CloudFront apuntando al ALB HTTP para habilitar el tráfico HTTPS entre el Frontend (Amplify) y el Backend, resolviendo así problemas de Mixed Content.

## Stacks

1. **`NetworkingStack`**: Define la VPC, subredes públicas y subredes privadas aisladas.
2. **`AppStack`**: Depende de `NetworkingStack`. Despliega RDS, ECR, ECS (Cluster, Task Def, Service), ALB, Secrets y los Roles IAM.

## Comandos Útiles

* `npm run build`   - Compilar TypeScript a JavaScript.
* `npm run watch`   - Observar cambios y compilar automáticamente.
* `npx cdk synth`   - Emitir la plantilla sintetizada de CloudFormation.
* `npx cdk diff`    - Comparar el stack desplegado con el estado actual.
* `npx cdk deploy --all` - Desplegar la infraestructura completa. Primero desplegará NetworkingStack y luego AppStack.
* `npx cdk destroy --all` - Eliminar todos los recursos de AWS creados por este proyecto.

## Despliegue Inicial (Bootstrapping)

1. Asegúrate de tener AWS CLI configurado con tus credenciales.
2. Ejecuta `npx cdk bootstrap` (solo la primera vez en la cuenta/región).
3. Ejecuta `npx cdk deploy --all`.
4. **CloudFront:** Ve a la consola de AWS CloudFront, crea una distribución apuntando al DNS del ALB (HTTP only, AllViewer Request Policy, CachingDisabled).
5. **Secretos:** Ve a AWS Secrets Manager y actualiza el secreto `blendx/app-secrets` con tu `OPENAI_API_KEY` real.
6. **Frontend:** Ve a la consola de AWS Amplify, configura la variable de entorno `VITE_API_URL` apuntando a la URL de tu distribución de CloudFront (ej. `https://d123abc456.cloudfront.net`), y dispara un nuevo build.
