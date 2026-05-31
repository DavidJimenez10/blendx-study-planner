from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatSource(BaseModel):
    filename: str
    content: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
