from typing import Annotated

from fastapi import Depends

from ..clients.openai_client import OpenAIClient
from ..core.config import settings
from ..core.database import DBDep
from ..services.agent_service import AgentService
from ..services.auth_service import AuthService
from ..services.chat_service import ChatService
from ..services.document_service import DocumentService
from ..services.generation_service import GenerationService
from ..services.plan_service import PlanService
from ..services.task_service import TaskService
from ..services.user_service import UserService


def get_user_service(db: DBDep) -> UserService:
    return UserService(db)


def get_plan_service(db: DBDep) -> PlanService:
    return PlanService(db)


def get_task_service(db: DBDep) -> TaskService:
    return TaskService(db)


def get_openai_client() -> OpenAIClient:
    return OpenAIClient(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)


OpenAIClientDep = Annotated[OpenAIClient, Depends(get_openai_client)]


def get_generation_service(
    db: DBDep,
    openai_client: OpenAIClientDep,
) -> GenerationService:
    return GenerationService(db, openai_client)


def get_document_service(
    db: DBDep,
    openai_client: OpenAIClientDep,
) -> DocumentService:
    return DocumentService(db, openai_client)


def get_chat_service(
    db: DBDep,
    openai_client: OpenAIClientDep,
) -> ChatService:
    return ChatService(db, openai_client)


def get_agent_service(
    db: DBDep,
    openai_client: OpenAIClientDep,
) -> AgentService:
    return AgentService(db, openai_client)


def get_auth_service(db: DBDep) -> AuthService:
    return AuthService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
PlanServiceDep = Annotated[PlanService, Depends(get_plan_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
GenerationServiceDep = Annotated[GenerationService, Depends(get_generation_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
