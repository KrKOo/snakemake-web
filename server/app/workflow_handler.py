import os
import re
import time
import uuid
import requests
from pathlib import Path

from app import app
from .utils import tes_auth

from .tasks import run_workflow

def run(workflow_definition_id, username, token) -> uuid.UUID:
    workflow_id = uuid.uuid4()

    log_file_path = Path(os.path.join(app.config["LOG_DIR"], username, f"{int(time.time() * 1000)}_{workflow_id}.txt"))
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    workflow_folder = [d for d in os.listdir(app.config['WORKFLOW_DEFINITION_DIR']) if d.startswith(workflow_definition_id + "_")][0]

    run_workflow.delay(log_file_path.as_posix(), workflow_folder, token)

    return workflow_id 

def get_workflow_definitions():
    workflows = [d for d in os.listdir(app.config['WORKFLOW_DEFINITION_DIR'])]
    res = []
    for workflow_dir in workflows:
        workflow_res = {}
        with open(f"{app.config['WORKFLOW_DEFINITION_DIR']}/{workflow_dir}/Snakefile") as f:
            workflow_res["id"] = workflow_dir.split("_")[0]
            workflow_name = workflow_dir[workflow_dir.find("_") + 1 :]
            workflow_res["name"] = workflow_name.replace("_", " ").capitalize()
            workflow_res["definition"] = f.read()
            res.append(workflow_res)
    return res

def get_workflows(username):
    log_dir = os.path.join(app.config["LOG_DIR"], username)
    workflow_logs = [f for f in os.listdir(log_dir) if os.path.isfile(os.path.join(log_dir, f))]
    workflows = []
    for workflow_log in workflow_logs:
        with open(os.path.join(log_dir, workflow_log), "r") as f:
            log = f.read()
        
        workflow = {}
        workflow["id"] = workflow_log.split("_")[1].split(".")[0]
        workflow["created_at"] = int(workflow_log.split("_")[0])

        if "WorkflowError" in log:
            workflow["status"] = "Failed"
        elif "Nothing to be done" in log:
            workflow["status"] = "Completed (did nothing)"
        else:
            progress_regex = r"^(\d*) of (\d*) steps .* done$"
            matches = list(re.finditer(progress_regex, log, re.MULTILINE))
            if len(matches) == 0:
                workflow["status"] = "Unknown"
            else:
                job_count = int(matches[-1].group(2))
                finished_jobs = int(matches[-1].group(1))

                if job_count == finished_jobs:
                    workflow["status"] = f"Completed ({finished_jobs}/{job_count})"
                else:
                    workflow["status"] = f"Running {finished_jobs}/{job_count}"
        
        workflows.append(workflow)
    return workflows

def get_workflow_jobs_info(username, workflow_id, list_view=False):
    job_ids = get_workflow_jobs(username, workflow_id)
    jobs_info = []
    for job_id in job_ids:
        jobs_info.append(get_job_info(job_id, list_view))
    return jobs_info

def get_workflow_jobs(username, workflow_id) -> list[str]:
    log_dir = os.path.join(app.config["LOG_DIR"], username)

    files = [f for f in os.listdir(log_dir) if workflow_id in f]

    if len(files) == 0:
        raise FileNotFoundError("Workflow not found") 
    
    log_file = os.path.join(log_dir, files[0])

    with open(log_file, 'r') as f:
        log = f.read()

    job_ids = []
    for line in log.split('\n'):
        if line.startswith("[TES] Task submitted: "):
            job_id = line.split(" ")[-1]
            job_ids.append(job_id)

    return job_ids

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
        job_info["creationTime"] = data["creationTime"]
        job_info["state"] = data["state"]
        try:
            job_info["logs"] = data["logs"][0]["logs"][0]["stdout"]
        except KeyError:
            job_info["logs"] = ""

        return job_info
    else:
        return None
