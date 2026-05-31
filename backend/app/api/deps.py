from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from ..clients.openai_client import OpenAIClient
from ..core.config import settings
from ..core.database import get_db
from ..services.generation_service import GenerationService
from ..services.plan_service import PlanService
from ..services.task_service import TaskService
from ..services.user_service import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_plan_service(db: Session = Depends(get_db)) -> PlanService:
    return PlanService(db)


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(db)


def get_openai_client() -> OpenAIClient:
    return OpenAIClient(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)


def get_generation_service(
    db: Session = Depends(get_db),
    openai_client: OpenAIClient = Depends(get_openai_client),
) -> GenerationService:
    return GenerationService(db, openai_client)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
PlanServiceDep = Annotated[PlanService, Depends(get_plan_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
OpenAIClientDep = Annotated[OpenAIClient, Depends(get_openai_client)]
GenerationServiceDep = Annotated[GenerationService, Depends(get_generation_service)]
