import os
import time
import uuid
import requests
import json
from pathlib import Path
from app import app

from .models import Workflow
from .utils import tes_auth
from .tasks import run_workflow
from .wrappers import with_updated_workflow_definitions

@with_updated_workflow_definitions
def run(workflow_definition_id, input_dir, output_dir, username, token) -> uuid.UUID:
    workflow_id = uuid.uuid4()

    log_file_path = Path(os.path.join(app.config["LOG_DIR"], username, f"{int(time.time() * 1000)}_{workflow_id}.txt"))
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    workflow_folder = get_workflow_dir_by_id(workflow_definition_id)

    workflow = Workflow(
        id=str(workflow_id),
        created_by=username,
    )
    workflow.save()

    run_workflow.delay(str(workflow_id), log_file_path.as_posix(), workflow_folder, input_dir, output_dir, token)

    return workflow_id 

@with_updated_workflow_definitions
def get_workflow_definitions():
    res = []
    for workflow_definition_dir in get_workflow_definition_dirs():
        workflow_res = {}

        metadata = get_workflow_metadata(workflow_definition_dir)
        workflow_res["id"] = metadata["id"]
        workflow_res["name"] = metadata["name"]

        with open(os.path.join(app.config['WORKFLOW_DEFINITION_DIR'], str(workflow_definition_dir), "Snakefile")) as f:
            workflow_res["definition"] = f.read()

        res.append(workflow_res)

    return res

def get_workflow_metadata(workflow_dir):
    with open(os.path.join(workflow_dir, "metadata.json")) as json_data:
        metadata = json.load(json_data)
        return metadata

def get_workflow_dir_by_id(workflow_id):
    for workflow_definition_dir in get_workflow_definition_dirs():
        if get_workflow_metadata(workflow_definition_dir)["id"] == workflow_id:
            return workflow_definition_dir

def get_workflow_definition_dirs():
    workflow_definition_dirs = [os.path.join(app.config['WORKFLOW_DEFINITION_DIR'], d) for d in os.listdir(app.config['WORKFLOW_DEFINITION_DIR']) if not d.startswith(".")]

    # Filter out non-directories
    workflow_definition_dirs = [d for d in workflow_definition_dirs if os.path.isdir(d)]

    return workflow_definition_dirs

def get_workflows(username):
    workflows = Workflow.objects(created_by=username).only("id", "state", "created_at", "total_jobs", "finished_jobs")

    res = []
    for workflow in workflows:
        workflow_res = {}
        workflow_res["id"] = workflow.id
        workflow_res["created_at"] = workflow.created_at.timestamp() * 1000
        workflow_res["status"] = workflow.state.value
        workflow_res["total_jobs"] = workflow.total_jobs
        workflow_res["finished_jobs"] = workflow.finished_jobs

        res.append(workflow_res)

    return res

def get_workflow_jobs_info(username, workflow_id, list_view=False):
    job_ids = get_workflow_jobs(username, workflow_id)
    jobs_info = []
    for job_id in job_ids:
        jobs_info.append(get_job_info(job_id, list_view))
    return jobs_info

def get_workflow_jobs(username, workflow_id) -> list[str]:
    workflow = Workflow.objects(id=workflow_id, created_by=username).only("job_ids").first()
    if not workflow:
        return []

    return workflow.job_ids

def get_job_info(job_id, list_view=False):
    request_url = f"{app.config["TES_URL"]}/v1/tasks/{job_id}"
    if not list_view:
        request_url += "?view=FULL"
    
    response = requests.get(request_url, auth=tes_auth)

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
