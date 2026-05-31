from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..clients.openai_client import OpenAIClient
from ..repositories.document_repository import DocumentRepository
from ..repositories.plan_repository import PlanRepository
from ..schemas.chat import ChatRequest, ChatResponse, ChatSource

SYSTEM_PROMPT = (
    "You are a study assistant. Answer the user's question ONLY using the provided "
    "document chunks below. If the answer cannot be found in the chunks, say: "
    '"No encontré información suficiente en los documentos de este plan para '
    'responder tu pregunta. Prueba subir más documentos o reformular la pregunta." '
    "Do not use any external knowledge or make up information. "
    "Always cite which chunk(s) you used to formulate the answer."
)


class ChatService:
    def __init__(self, db: Session, openai_client: OpenAIClient) -> None:
        self.db = db
        self.openai_client = openai_client
        self.doc_repo = DocumentRepository(db)
        self.plan_repo = PlanRepository(db)

    def chat(self, plan_id: int, request: ChatRequest) -> ChatResponse:
        if not self.plan_repo.get_by_id(plan_id):
            raise HTTPException(status_code=404, detail="Plan not found")

        question_embedding = self.openai_client.generate_embedding(request.question)
        results = self.doc_repo.search_similar(
            plan_id=plan_id,
            embedding=question_embedding,
            top_k=4,
            threshold=0.7,
        )

        if not results:
            return ChatResponse(
                answer="No encontré información suficiente en los documentos de "
                "este plan para responder tu pregunta. Prueba subir más documentos "
                "o reformular la pregunta.",
                sources=[],
            )

        context_parts = []
        for i, (chunk, _) in enumerate(results, 1):
            doc = self.doc_repo.get_document_by_chunk_id(chunk.id)
            filename = doc.filename if doc else "unknown"
            context_parts.append(f"[Chunk {i} — {filename}]\n{chunk.content}")

        context = "\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Document chunks:\n\n{context}\n\n"
                    f"User question: {request.question}"
                ),
            },
        ]

        answer = self.openai_client.chat(messages)

        sources = []
        for chunk, _ in results:
            doc = self.doc_repo.get_document_by_chunk_id(chunk.id)
            sources.append(
                ChatSource(
                    filename=doc.filename if doc else "unknown",
                    content=chunk.content,
                )
            )

        return ChatResponse(answer=answer, sources=sources)
