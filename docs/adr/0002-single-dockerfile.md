# Dockerfile unico sin multi-stage build

**Contexto:** El `docker-compose.yml` de desarrollo sobreescribe el CMD del Dockerfile para anyadir `--reload` y monta el codigo fuente como volumen para hot-reload. Esto permite que el mismo Dockerfile sirva tanto para desarrollo local como para produccion en ECS.

**Decision:** Mantenemos un solo `Dockerfile` en `backend/` sin multi-stage build. El unico cambio necesario para produccion es eliminar `--reload` del CMD base.

**Por que:** La imagen de desarrollo y la de produccion son identicas en contenido (mismas dependencias, mismo codigo, mismo runtime). La unica diferencia es el flag `--reload`. Multi-stage build no reduciria significativamente el tamanyo de la imagen porque las dependencias de Python y `uv` ya estan optimizadas. Mantener un solo Dockerfile evita duplicacion y divergencia entre entornos.

**Alternativa considerada:** Crear un `Dockerfile.prod` separado con multi-stage build. Se rechazo porque:
- El tamanyo de la imagen no es un problema en este MVP (~300 MB con `python:3.12-slim` y dependencias).
- Dos Dockerfiles requieren mantener dos CMDs sincronizados.
- El `docker-compose.yml` ya maneja el override para desarrollo.

**Reversibilidad:** Alta. Si en el futuro se necesitan optimizaciones de tamanyo (capas mas delgadas, builder stage separado), se puede introducir un Dockerfile de produccion sin afectar el flujo de desarrollo.
