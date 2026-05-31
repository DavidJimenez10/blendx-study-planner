# pgvector como vector store para Document Chat (RAG)

**Contexto:** La feature de Document Chat requiere una base de datos vectorial para almacenar embeddings de documentos y hacer busqueda semantica. La aplicacion ya usa PostgreSQL 16 como base de datos principal.

**Decision:** Usamos la extension pgvector en PostgreSQL (imagen `pgvector/pgvector:pg16`), en lugar de un vector store externo como Pinecone o Chroma.

**Por que:**
- **Simplicidad operacional:** Una sola base de datos que manejar, sin servicio externo adicional que configurar, monitorear y asegurar.
- **Co-localizacion de datos:** Los chunks de documentos viven en la misma base de datos que los Study Plans, permitiendo filtrado por `plan_id` en la misma consulta SQL (tenant isolation nativa).
- **Costo:** pgvector es open-source y no anade costo adicional. Pinecone empieza en ~$70/mes.
- **Suficiente para la escala del MVP:** Con documentos de hasta 30 paginas y busquedas top-k=4, pgvector con indice IVFFlat maneja la carga sin problemas.
- **pgvector/pgvector:pg16** es un drop-in replacement de la imagen `postgres:16-alpine` existente.

**Alternativas consideradas:**
- **Pinecone/Chroma/Qdrant:** Anaden un servicio externo que duplica la complejidad de despliegue (nuevo contenedor, nuevo health check, nuevas variables de entorno, nuevo costo) sin beneficio real a la escala actual.
- **SQLite con extension vectorial:** No viable porque la app ya usa PostgreSQL y las pruebas usan SQLite en memoria; mezclar dos engines de DB complica el testing.

**Reversibilidad:** Media. Migrar a un vector store externo requeriria exportar embeddings, reindexar, y cambiar la capa de repository, pero el modelo de datos (chunks con plan_id) se mantendria igual.
