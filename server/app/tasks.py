import logging
import os
import re
import select
import shutil
import signal
from typing import Dict, Optional
import uuid
from subprocess import PIPE, STDOUT, CalledProcessError, CompletedProcess, Popen

from celery import shared_task
from celery.contrib.abortable import AbortableTask

from .common import WorkflowState
from .utils import pull_workflow_definitions
from .workflow_config import WorkflowConfig
from .api_dependencies import get_workflow_repository


def stream_command(
    args,
    *,
    stdout_handler=logging.info,
    abort_condition=None,
    abort_signal=signal.SIGINT,
    on_abort=None,
    check=False,
    text=True,
    **kwargs,
):
    """Mimic subprocess.run, while processing the command output in real time."""
    with Popen(args, text=text, stdout=PIPE, stderr=STDOUT, **kwargs) as process:
        aborted = False

        while True:
            if abort_condition and not aborted:
                if abort_condition():
                    os.kill(process.pid, abort_signal)
                    on_abort(process) if on_abort else None
                    aborted = True

            reads, _, _ = select.select([process.stdout], [], [], 1)
            if not reads:
                continue

            line = process.stdout.readline() if process.stdout is not None else None

            if not line:
                break

            stdout_handler(line[:-1])

    retcode = process.wait()

    if check and retcode != 0:
        raise CalledProcessError(retcode, process.args)
    return CompletedProcess(process.args, retcode)


def log_handler(workflow_repository, log_file_path, line, workflow_id):
    with open(log_file_path, "a") as f:
        f.write(line + "\n")

    progress_regex = re.compile(r"^(\d*) of (\d*) steps .* done$")
    line_match = progress_regex.match(line)

    job_id = state = finished_jobs = total_jobs = None

    if line.startswith("[TES] Task submitted: "):
        job_id = line.split(" ")[-1]
        state = WorkflowState.RUNNING
    elif line.startswith("total"):
        total_jobs = int(line.split(" ")[-1])
    elif "Nothing to be done" in line:
        state = WorkflowState.FINISHED
    elif line_match:
        finished_jobs = int(line_match.group(1))
        total_jobs = int(line_match.group(2))

        if total_jobs == finished_jobs:
            state = WorkflowState.FINISHED
        else:
            state = WorkflowState.RUNNING
    else:
        return

    
    workflow = workflow_repository.get(uuid.UUID(workflow_id))
    if not workflow:
        return

    if finished_jobs:
        workflow.finished_jobs = finished_jobs
    if total_jobs:
        workflow.total_jobs = total_jobs
    if state:
        workflow.state = state
    if job_id:
        workflow.job_ids.append(job_id)

    workflow_repository.update(workflow)

@shared_task(base=AbortableTask, bind=True)
def run_workflow(
    self,
    workflow_config: WorkflowConfig,
    workflow_id: str,
    log_file_path: str,
    workflow_folder: str,
    input_dir: str,
    output_dir: str,
    result_bucket: str,
    username: str,
    token: str,
    input_mapping: Optional[Dict[str, str]] = None,
):
    workflow_repository = get_workflow_repository()

    pull_workflow_definitions(
        workflow_config.workflow_definition_dir,
        workflow_config.workflow_definition_repo,
        workflow_config.workflow_definition_branch
    )

    current_workflow_dir = os.path.join(
        workflow_config.workflow_dir, workflow_id
    )

    shutil.copytree(
        os.path.join(workflow_config.workflow_definition_dir, workflow_folder),
        current_workflow_dir,
    )

    snakefile = os.path.join(current_workflow_dir, "Snakefile")

    with open(snakefile) as f:
        snakefile_template = f.read()

    with open(snakefile, "w") as f:
        f.write(
            snakefile_template.replace("<input_dir>", f"'{input_dir}'").replace(
                "<output_dir>", f"'{output_dir}'"
            )
        )

    def on_abort(process):
        workflow = workflow_repository.get(uuid.UUID(workflow_id))
        if not workflow:
            return
        workflow.state = WorkflowState.CANCELED
        workflow_repository.update(workflow)

    command_args = [
        "snakemake",
        "--sdm=conda",
        "--use-conda",
        "--conda-frontend=conda",
        "--executor=auth-tes",
        "--default-storage-provider=s3",
        f"--default-storage-prefix={workflow_config.default_storage_prefix}",
        f"--storage-s3-endpoint-url={workflow_config.storage_s3_endpoint_url}",
        f"--storage-s3-access-key={workflow_config.storage_s3_access_key}",
        f"--storage-s3-secret-key={workflow_config.storage_s3_secret_key}",
        f"--auth-tes-url={workflow_config.auth_tes_url}",
        "--auth-tes-oidc-auth=true",
        f"--container-image={workflow_config.container_image}",
        f"--jobs={workflow_config.jobs}",
        "--envvars",
        "ACCESS_TOKEN",
        "RESULT_BUCKET",
        "INPUT_DIR",
        "OUTPUT_DIR",
        "USER_ID",
        "INBOX_HOST",
        "DOWNLOAD_HOST",
        "WORKFLOW_ID",
        "TMP_DIR",
        "CLIENT_ID",
        "CLIENT_SECRET",
        "OIDC_URL",
        "AUDIENCE",
    ]

    if input_mapping:
        input_mapping_str = " ".join(
            f"{k}={v}" for k, v in input_mapping.items()
        )
        command_args.extend(["--input-passthrough-mapping", input_mapping_str])

    res = stream_command(
        command_args,
        cwd=current_workflow_dir,
        env={
            **os.environ,
            "ACCESS_TOKEN": token,
            "WORKFLOW_ID": workflow_id,
            "RESULT_BUCKET": result_bucket,
            "INPUT_DIR": input_dir,
            "OUTPUT_DIR": output_dir,
            "USER_ID": username.replace("@", "_"),
            "INBOX_HOST": workflow_config.inbox_host,
            "DOWNLOAD_HOST": workflow_config.download_host,
            "TMP_DIR": workflow_config.tmp_dir,
            "CLIENT_ID": workflow_config.oidc_client_id,
            "CLIENT_SECRET": workflow_config.oidc_client_secret,
            "OIDC_URL": workflow_config.oidc_url,
            "AUDIENCE": workflow_config.oidc_audience,
        },
        stdout_handler=lambda line: log_handler(workflow_repository, log_file_path, line, workflow_id),
        abort_condition=self.is_aborted,
        on_abort=on_abort,
    )

    shutil.rmtree(current_workflow_dir)

    if res.returncode != 0 and not self.is_aborted():
        workflow = workflow_repository.get(uuid.UUID(workflow_id))
        if not workflow:
            return
        workflow.state = WorkflowState.FAILED
        workflow_repository.update(workflow)

    return res.returncode
