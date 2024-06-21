from datetime import datetime, UTC
from enum import Enum
from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    IntField,
    EnumField,
    ListField,
)


class WorkflowState(Enum):
    UNKNOWN = "UNKNOWN"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class Workflow(Document):
    id = StringField(required=True, primary_key=True)
    task_id = StringField(required=True)
    created_at = DateTimeField(default=lambda: datetime.now(UTC), required=True)
    created_by = StringField(required=True)
    total_jobs = IntField(default=0)
    finished_jobs = IntField(default=0)
    state = EnumField(WorkflowState, default=WorkflowState.UNKNOWN)
    job_ids = ListField(StringField(), default=[])
