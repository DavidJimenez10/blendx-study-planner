from pydantic import BaseModel, Field


class Subtopic(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    suggested_hours: float = Field(gt=0)


class BreakdownResponse(BaseModel):
    subtopics: list[Subtopic]


class AgentGenerateRequest(BaseModel):
    approved_subtopics: list[Subtopic] = Field(min_length=1)


class TaskDraft(BaseModel):
    title: str = Field(min_length=1)
    estimated_hours: float = Field(gt=0)
