from fastapi import APIRouter

from ...schemas.chat import ChatRequest, ChatResponse
from ..deps import ChatServiceDep

router = APIRouter(prefix="/plans/{plan_id}/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(plan_id: int, data: ChatRequest, svc: ChatServiceDep):
    return svc.chat(plan_id, data)
