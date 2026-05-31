import io

from fastapi import HTTPException, UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from sqlalchemy.orm import Session

from ..clients.openai_client import OpenAIClient
from ..models.plan_document import DocumentChunk
from ..repositories.document_repository import DocumentRepository
from ..repositories.plan_repository import PlanRepository
from ..schemas.plan_document import PlanDocumentRead

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "text/plain": "txt",
    "text/markdown": "md",
    "text/x-markdown": "md",
}


class DocumentService:
    def __init__(self, db: Session, openai_client: OpenAIClient) -> None:
        self.db = db
        self.openai_client = openai_client
        self.doc_repo = DocumentRepository(db)
        self.plan_repo = PlanRepository(db)

    def upload_document(self, plan_id: int, file: UploadFile) -> PlanDocumentRead:
        if not self.plan_repo.get_by_id(plan_id):
            raise HTTPException(status_code=404, detail="Plan not found")

        content_bytes = file.file.read()
        file_size = len(content_bytes)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail="File too large. Maximum size is 10MB."
            )

        file_type = ALLOWED_TYPES.get(file.content_type or "", "")
        if not file_type:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Allowed: PDF, TXT, MD.",
            )

        text = self._extract_text(content_bytes, file_type)
        if not text.strip():
            raise HTTPException(
                status_code=422, detail="No text could be extracted from the file."
            )

        chunks = self._split_text(text)
        if not chunks:
            raise HTTPException(
                status_code=422, detail="File content could not be split into chunks."
            )

        embeddings = []
        for chunk in chunks:
            embedding = self.openai_client.generate_embedding(chunk)
            embeddings.append(embedding)

        doc = self.doc_repo.create_document(
            plan_id=plan_id,
            filename=file.filename or "unknown",
            file_type=file_type,
            file_size=file_size,
            chunk_count=len(chunks),
        )

        chunk_models = []
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_models.append(
                DocumentChunk(
                    document_id=doc.id,
                    plan_id=plan_id,
                    content=chunk_text,
                    embedding=embedding,
                    chunk_index=i,
                )
            )
        self.doc_repo.create_chunks(chunk_models)

        return PlanDocumentRead.model_validate(doc)

    def get_documents(self, plan_id: int) -> list[PlanDocumentRead]:
        if not self.plan_repo.get_by_id(plan_id):
            raise HTTPException(status_code=404, detail="Plan not found")
        docs = self.doc_repo.get_by_plan_id(plan_id)
        return [PlanDocumentRead.model_validate(d) for d in docs]

    def delete_document(self, plan_id: int, document_id: int) -> None:
        if not self.plan_repo.get_by_id(plan_id):
            raise HTTPException(status_code=404, detail="Plan not found")
        if not self.doc_repo.delete(document_id):
            raise HTTPException(status_code=404, detail="Document not found")

    def _extract_text(self, content: bytes, file_type: str) -> str:
        if file_type == "pdf":
            try:
                reader = PdfReader(io.BytesIO(content))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                return text.replace("\x00", "")
            except PdfReadError:
                raise HTTPException(
                    status_code=422,
                    detail="Could not read PDF file. The file may be corrupted or invalid.",
                )
        return content.decode("utf-8", errors="replace").replace("\x00", "")

    def _split_text(self, text: str) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return splitter.split_text(text)
