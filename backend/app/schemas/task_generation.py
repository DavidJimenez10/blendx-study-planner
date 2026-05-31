from pydantic import BaseModel, Field

from .study_task import StudyTaskRead


class GenerateTasksRequest(BaseModel):
    max_tasks: int | None = Field(None, ge=1)


class GeneratedTask(BaseModel):
    title: str
    estimated_hours: float


class FailedGeneration(BaseModel):
    title: str = ""
    estimated_hours: float = 0.0
    reason: str


class GenerateTasksResponse(BaseModel):
    tasks: list[StudyTaskRead]
    total_estimated_hours: float
    hours_match: bool
    warning: str | None = None
    failed_generations: list[FailedGeneration] = []
