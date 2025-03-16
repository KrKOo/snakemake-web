from uuid import UUID
from app.schemas import WorkflowListItem, WorkflowDetail
from app.db.models import WorkflowModel
from app.db import BaseDatabase
from app.repository.job_repository import JobRepository
from app.auth import AccessToken


class WorkflowRepository:
    def __init__(self, db: BaseDatabase, job_repository: JobRepository):
        self.db = db
        self.job_repository = job_repository

    def get_list_item(self, workflow_id: UUID) -> WorkflowListItem | None:
        workflow_model = self.db.get_one(WorkflowModel, {"id": workflow_id})

        if not workflow_model:
            return None
        
        return WorkflowListItem(
            id=workflow_model.id,
            created_at=workflow_model.created_at,
            state=workflow_model.state,
            total_jobs=workflow_model.total_jobs,
            finished_jobs=workflow_model.finished_jobs,
        )
    
    def get_detail(self, workflow_id: UUID, token: AccessToken) -> WorkflowDetail | None:
        workflow_model = self.db.get_one(WorkflowModel, {"id": workflow_id})

        if not workflow_model:
            return None

        return WorkflowDetail(
            id=workflow_model.id,
            created_at=workflow_model.created_at,
            state=workflow_model.state,
            jobs=self.job_repository.get_detail_list(workflow_model.job_ids, token),
        )
    
    def get_owner(self, workflow_id: UUID) -> str | None:
        workflow_model = self.db.get_one(WorkflowModel, {"id": workflow_id})

        if not workflow_model:
            return None

        return workflow_model.created_by
    
    def get_task_id(self, workflow_id: UUID) -> str | None:
        workflow_model = self.db.get_one(WorkflowModel, {"id": workflow_id})

        if not workflow_model:
            return None

        return workflow_model.task_id
    
    def get_list_by_user(self, username: str) -> list[WorkflowListItem]:
        workflows = self.db.get_many(WorkflowModel, {"created_by": username})

        res = []
        for workflow in workflows:
            workflow_res = WorkflowListItem(
                id=workflow.id,
                created_at=workflow.created_at,
                state=workflow.state,
                total_jobs=workflow.total_jobs,
                finished_jobs=workflow.finished_jobs,
            )

            res.append(workflow_res)
        
        return res
    
    def get(self, workflow_id: UUID) -> WorkflowModel | None:
        return self.db.get_one(WorkflowModel, {"id": workflow_id})
    
    def update(self, workflow: WorkflowModel):
        self.db.update_one(WorkflowModel, {"id": workflow.id}, workflow)

    def save(self, workflow: WorkflowModel):
        self.db.insert_one(WorkflowModel, workflow)