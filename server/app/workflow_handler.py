import os
import uuid
import subprocess
import requests
from pathlib import Path

from app import app
from .utils import tes_auth

def run(username, token) -> uuid.UUID:
    workflow_id = uuid.uuid4()

    log_file_path = Path(os.path.join(app.config["LOG_DIR"], username, f"{workflow_id}.txt"))
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_file_path, "w")

    subprocess.Popen(
        [
            "snakemake",
            "--sdm=conda",
            "--executor=tes",
            "--snakefile=workflows/Snakefile",
            "--directory=workflows",
            "--default-storage-provider=s3",
            f"--default-storage-prefix={app.config['DEFAULT_STORAGE_PREFIX']}",
            f"--storage-s3-endpoint-url={app.config['STORAGE_S3_ENDPOINT_URL']}",
            f"--storage-s3-access-key={app.config['STORAGE_S3_ACCESS_KEY']}",
            f"--storage-s3-secret-key={app.config['STORAGE_S3_SECRET_KEY']}",
            f"--tes-url={app.config['TES_URL']}",
            f"--tes-oidc-client-id={app.config['TES_OIDC_CLIENT_ID']}",
            f"--tes-oidc-client-secret={app.config['TES_OIDC_CLIENT_SECRET']}",
            f"--tes-oidc-url={app.config['TES_OIDC_URL']}",
            f"--tes-oidc-access-token={token}",
            f"--tes-oidc-audience={app.config['TES_OIDC_AUDIENCE']}",
            f"--container-image={app.config['SNAKEMAKE_CONTAINER_IMAGE']}",
            f"--jobs={app.config['SNAKEMAKE_JOBS']}",
        ],
        stdout=log_file,
        stderr=log_file,
    )

    return workflow_id

def get_workflow_jobs_info(username, workflow_id, list_view=False):
    job_ids = get_workflow_jobs(username, workflow_id)
    jobs_info = []
    for job_id in job_ids:
        jobs_info.append(get_job_info(job_id, list_view))
    return jobs_info

def get_workflow_jobs(username, workflow_id) -> list[str]:
    log_dir = os.path.join(app.config["LOG_DIR"], username)
    log_file = os.path.join(log_dir, f"{workflow_id}.txt")
    
    if not os.path.exists(log_file):
        raise FileNotFoundError("Workflow not found") 

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
