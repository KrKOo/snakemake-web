import os
import re
import time
import uuid
import requests
from pathlib import Path
from bson import json_util

from app import app

from .models import Workflow, WorkflowState
from .utils import tes_auth
from .tasks import run_workflow

def run(workflow_definition_id, input_dir, output_dir, username, token) -> uuid.UUID:
    workflow_id = uuid.uuid4()

    log_file_path = Path(os.path.join(app.config["LOG_DIR"], username, f"{int(time.time() * 1000)}_{workflow_id}.txt"))
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    workflow_folder = [d for d in os.listdir(app.config['WORKFLOW_DEFINITION_DIR']) if d.startswith(workflow_definition_id + "_")][0]

    workflow = Workflow(
        id=str(workflow_id),
        created_by=username,
    )
    workflow.save()

    run_workflow.delay(str(workflow_id), log_file_path.as_posix(), workflow_folder, input_dir, output_dir, token)

    return workflow_id 

def get_workflow_definitions():
    workflows = [d for d in os.listdir(app.config['WORKFLOW_DEFINITION_DIR'])]
    res = []
    for workflow_dir in workflows:
        workflow_res = {}
        with open(os.path.join(app.config['WORKFLOW_DEFINITION_DIR'], str(workflow_dir), "Snakefile")) as f:
            workflow_res["id"] = workflow_dir.split("_")[0]
            workflow_name = workflow_dir[workflow_dir.find("_") + 1 :]
            workflow_res["name"] = workflow_name.replace("_", " ").capitalize()
            workflow_res["definition"] = f.read()
            res.append(workflow_res)
    return res

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
