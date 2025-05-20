from functools import wraps
import os
import time
import uuid
from pathlib import Path
from celery.contrib.abortable import AbortableAsyncResult

from .auth import AccessToken
from .db.models import WorkflowModel
from .tasks import run_workflow
from .workflow_definition.manager import get_workflow_definition_by_id
from .repository import WorkflowRepository
from .config import config
from .workflow_config import WorkflowConfig

class WorkflowWasNotRun(Exception):
    """Raised when trying to access a workflow that was not run yet"""


class WorkflowMultipleRuns(Exception):
    """Raised when trying to run a workflow that was already run"""


class Workflow:
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        log_dir: str,
        tes_url: str,
        token: AccessToken,
        id: uuid.UUID | None = None,
    ):
        self.workflow_repository = workflow_repository
        self.id = id
        self.log_dir = log_dir
        self.tes_url = tes_url
        self.token = token

        self.was_run = self.exists()

    @staticmethod
    def ensure_was_run(f):
        @wraps(f)
        def decorated(self, *args, **kwargs):
            if not self.was_run:
                raise WorkflowWasNotRun

            return f(self, *args, **kwargs)

        return decorated

    def run(
        self,
        workflow_config: WorkflowConfig,
        workflow_definition_id: uuid.UUID,
        input_dir: str,
        output_dir: str,
        username: str,
    ):
        if self.was_run:
            raise WorkflowMultipleRuns

        self.id = uuid.uuid4()
        self.was_run = True

        log_file_path = Path(
            os.path.join(
                self.log_dir, username, f"{int(time.time() * 1000)}_{self.id}.txt"
            )
        )
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        workflow_definition_metadata = get_workflow_definition_by_id(workflow_definition_id)
        
        for tes_datasets in config.tes_data:
            if input_dir in tes_datasets.datasets:
                workflow_config.auth_tes_url = tes_datasets.tes_url
                break
        
        task_state = run_workflow.delay(
            workflow_config=workflow_config,
            workflow_id=str(self.id),
            log_file_path=log_file_path.as_posix(),
            workflow_folder=workflow_definition_metadata.dir,
            input_dir=input_dir,
            output_dir=output_dir,
            result_bucket=self.token.userinfo.sub.replace("@", "_"),
            username=username,
            token=self.token.value,
            input_mapping=workflow_definition_metadata.get_input_mapping({"dataset": input_dir}),
        )

        workflow = WorkflowModel(
            _id=self.id,
            task_id=task_state.id,
            created_by=username,
        )

        self.workflow_repository.save(workflow)

        return self.id

    def exists(self):
        if not self.id:
            return False

        return self.workflow_repository.get_list_item(self.id) is not None

    @ensure_was_run
    def cancel(self):
        self.workflow_repository.cancel(self.id)
        task_id = self.workflow_repository.get_task_id(self.id)
        result = AbortableAsyncResult(task_id)
        result.abort()

    @ensure_was_run
    def is_owned_by_user(self, username):
        workflow_owner = self.workflow_repository.get_owner(self.id)
        return workflow_owner == username

    @ensure_was_run
    def get_detail(self):
        return self.workflow_repository.get_detail(self.id, self.token)
