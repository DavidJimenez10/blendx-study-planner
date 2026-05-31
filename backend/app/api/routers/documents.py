
from fastapi import APIRouter, UploadFile

from ...schemas.plan_document import PlanDocumentRead
from ..deps import DocumentServiceDep

router = APIRouter(prefix="/plans/{plan_id}/documents", tags=["documents"])


@router.post("", response_model=PlanDocumentRead, status_code=201)
def upload_document(plan_id: int, file: UploadFile, svc: DocumentServiceDep):
    return svc.upload_document(plan_id, file)


@router.get("", response_model=list[PlanDocumentRead])
def list_documents(plan_id: int, svc: DocumentServiceDep):
    return svc.get_documents(plan_id)


@router.delete("/{document_id}", status_code=204)
def delete_document(plan_id: int, document_id: int, svc: DocumentServiceDep):
    svc.delete_document(plan_id, document_id)
