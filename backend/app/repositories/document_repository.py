from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models.plan_document import DocumentChunk, PlanDocument


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_document(
        self, plan_id: int, filename: str, file_type: str, file_size: int, chunk_count: int
    ) -> PlanDocument:
        doc = PlanDocument(
            plan_id=plan_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            chunk_count=chunk_count,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_id(self, document_id: int) -> PlanDocument | None:
        return self.db.query(PlanDocument).filter(PlanDocument.id == document_id).first()

    def get_by_plan_id(self, plan_id: int) -> list[PlanDocument]:
        return (
            self.db.query(PlanDocument)
            .filter(PlanDocument.plan_id == plan_id)
            .order_by(PlanDocument.created_at.desc())
            .all()
        )

    def delete(self, document_id: int) -> bool:
        doc = self.get_by_id(document_id)
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        return True

    def create_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        self.db.add_all(chunks)
        self.db.commit()
        return chunks

    def search_similar(
        self, plan_id: int, embedding: list[float], top_k: int, threshold: float
    ) -> list[tuple[DocumentChunk, float]]:
        embedding_str = f"[{','.join(map(str, embedding))}]"
        query = text(
            """
            SELECT dc.id, dc.document_id, dc.plan_id, dc.content, dc.embedding,
                   dc.chunk_index, dc.created_at,
                   1 - (dc.embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM document_chunks dc
            WHERE dc.plan_id = :plan_id
              AND 1 - (dc.embedding <=> CAST(:embedding AS vector)) > :threshold
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
            """
        )
        rows = (
            self.db.execute(
                query,
                {
                    "plan_id": plan_id,
                    "embedding": embedding_str,
                    "threshold": threshold,
                    "top_k": top_k,
                },
            )
            .mappings()
            .all()
        )

        results = []
        for row in rows:
            chunk = DocumentChunk(
                id=row["id"],
                document_id=row["document_id"],
                plan_id=row["plan_id"],
                content=row["content"],
                chunk_index=row["chunk_index"],
            )
            results.append((chunk, row["similarity"]))
        return results

    def get_document_by_chunk_id(self, chunk_id: int) -> PlanDocument | None:
        chunk = self.db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            return None
        return self.db.query(PlanDocument).filter(PlanDocument.id == chunk.document_id).first()
