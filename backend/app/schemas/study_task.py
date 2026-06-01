from pydantic import BaseModel


class StudyTaskCreate(BaseModel):
    title: str
    estimated_hours: float
    subtopic: str | None = "general"


class StudyTaskUpdate(BaseModel):
    completed: bool


class StudyTaskRead(BaseModel):
    id: int
    plan_id: int
    title: str
    estimated_hours: float
    completed: bool
    subtopic: str = "general"

    model_config = {"from_attributes": True}
