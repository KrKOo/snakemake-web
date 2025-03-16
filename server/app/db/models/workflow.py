from datetime import datetime, UTC
from pydantic import ConfigDict, Field
from uuid import UUID

from app.common import WorkflowState
from .model import Model


class WorkflowModel(Model):
    _collection_name = "workflow"

    id: UUID = Field(..., alias="_id")
    task_id: str = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str = Field(...)
    total_jobs: int = 0
    finished_jobs: int = 0
    state: WorkflowState = WorkflowState.UNKNOWN
    job_ids: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)
