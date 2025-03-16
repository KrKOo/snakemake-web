from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.common import WorkflowState

class WorkflowId(BaseModel):
    id: UUID

class WorkflowListItem(BaseModel):
    id: UUID
    created_at: datetime
    state: WorkflowState
    finished_jobs: int
    total_jobs: int

class JobDetail(BaseModel):
    id: str
    created_at: datetime
    state: str
    logs: str

class JobListItem(BaseModel):
    id: str
    created_at: datetime
    state: str

class WorkflowDetail(BaseModel):
    id: UUID
    created_at: datetime
    state: WorkflowState
    #workflow_definition_id: UUID
    #input_dir: str
    #output_dir: str
    jobs: list[JobDetail]

class WorkflowDefinitionListItem(BaseModel):
    id: UUID
    name: str
    definition: str

class WorkflowRun(BaseModel):
    workflow_definition_id: UUID 
    input_dir: str
    output_dir: str