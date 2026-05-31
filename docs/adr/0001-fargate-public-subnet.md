# Fargate en subred publica con IP publica

**Contexto:** Para que el backend de Fargate pueda hacer `docker pull` desde ECR, leer secretos de Secrets Manager, y (pronto) llamar a la API de OpenAI, necesita acceso a internet saliente. La opcion segura estandar es desplegar Fargate en subredes privadas con un NAT Gateway.

**Decision:** Desplegamos Fargate en subredes publicas con IP publica asignada, en lugar de usar NAT Gateway en subredes privadas.

**Por que:** Un NAT Gateway cuesta ~$35-45/mes fijos + trafico, lo que casi duplicaria el costo mensual de esta infraestructura minimalista (~$50-70/mes total). Para un MVP con trafico bajo y sin datos sensibles de usuario final (solo credenciales de infraestructura, que ya estan en Secrets Manager), la concesion de seguridad es aceptable.

**Mitigacion:** El Security Group de Fargate solo acepta trafico entrante en el puerto 8000 desde el Security Group del ALB. Ningun trafico externo puede alcanzar directamente el contenedor de Fargate. La IP publica solo se usa para trafico saliente.

**Reversibilidad:** Alta. Si los costos lo justifican o los requisitos de seguridad cambian, migrar a subredes privadas con NAT Gateway es un cambio de configuracion en el CDK (subnet public -> private, asignPublicIp: true -> false, crear NAT Gateway).
