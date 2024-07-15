from functools import wraps
import os
import time
import uuid
import requests
from pathlib import Path
from app import celery as celeryapp
from celery.contrib.abortable import AbortableAsyncResult

from .models import Workflow as WorkflowModel
from .tasks import run_workflow
from .workflow_definition.manager import get_workflow_definition_by_id


class WorkflowWasNotRun(Exception):
    """Raised when trying to access a workflow that was not run yet"""


class WorkflowMultipleRuns(Exception):
    """Raised when trying to run a workflow that was already run"""


class Workflow:
    def __init__(
        self,
        id: str = None,
        log_dir: str = None,
        tes_url: str = None,
        tes_auth: requests.auth.HTTPBasicAuth = None,
    ):
        self.id = id
        self.lod_dir = log_dir
        self.tes_url = tes_url
        self.tes_auth = tes_auth

        self.was_run = self.exists()

    def ensure_was_run(f):
        @wraps(f)
        def decorated(self, *args, **kwargs):
            if not self.was_run:
                raise WorkflowWasNotRun

            return f(self, *args, **kwargs)

        return decorated

    def run(self, workflow_definition_id, input_dir, output_dir, username, token):
        if self.was_run:
            raise WorkflowMultipleRuns

        self.id = str(uuid.uuid4())
        self.was_run = True

        log_file_path = Path(
            os.path.join(
                self.log_dir, username, f"{int(time.time() * 1000)}_{self.id}.txt"
            )
        )
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        workflow_definition = get_workflow_definition_by_id(workflow_definition_id)

        task_state = run_workflow.delay(
            self.id,
            log_file_path.as_posix(),
            workflow_definition.dir,
            input_dir,
            output_dir,
            token,
            config,
        )

        workflow = WorkflowModel(
            id=self.id,
            task_id=task_state.id,
            created_by=username,
        )

        workflow.save()

        return self.id

    def exists(self):
        if not self.id:
            return False

        return WorkflowModel.objects.get(id=self.id) is not None

    @ensure_was_run
    def cancel(self):
        workflow_object = WorkflowModel.objects.get(id=self.id)
        result = AbortableAsyncResult(
            workflow_object.task_id, backend=celeryapp.backend
        )
        result.abort()

    @ensure_was_run
    def is_owned_by_user(self, username):
        workflow_object = WorkflowModel.objects.get(id=self.id)
        return workflow_object.created_by == username

    @ensure_was_run
    def get_detail(self):
        workflow_object = WorkflowModel.objects.get(id=self.id)

        workflow_detail = {
            "id": workflow_object.id,
            "created_at": workflow_object.created_at.timestamp() * 1000,
            "state": workflow_object.state.value,
            "jobs": self.get_jobs_info(),
        }
        return workflow_detail

    @ensure_was_run
    def get_jobs_info(self, list_view=False):
        job_ids = self.get_jobs()
        jobs_info = []
        for job_id in job_ids:
            jobs_info.append(self._get_job_info(job_id, list_view))
        return jobs_info

    @ensure_was_run
    def get_jobs(self) -> list[str]:
        workflow = WorkflowModel.objects(id=self.id).only("job_ids").first()
        if not workflow:
            return []
        return workflow.job_ids

    def _get_job_info(self, job_id, list_view=False):
        request_url = f"{self.tes_url}/v1/tasks/{job_id}"
        if not list_view:
            request_url += "?view=FULL"

        response = requests.get(request_url, auth=self.tes_auth)

        if response.status_code == 200:
            data = response.json()

            if list_view:
                return data

            job_info = {}
            job_info["id"] = data["id"]
            job_info["created_at"] = data["creation_time"]
            job_info["state"] = data["state"]
            try:
                job_info["logs"] = data["logs"][0]["logs"][0]["stdout"]
            except KeyError:
                job_info["logs"] = ""

            return job_info
        else:
            return None
