from datetime import datetime

from pydantic import BaseModel


class PlanDocumentRead(BaseModel):
    id: int
    plan_id: int
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
