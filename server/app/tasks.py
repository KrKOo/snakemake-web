import logging
import os
import re
import select
import shutil
import signal
from subprocess import PIPE, STDOUT, CalledProcessError, CompletedProcess, Popen

from celery import shared_task
from celery.contrib.abortable import AbortableTask

from .models import Workflow, WorkflowState
from .utils import pull_workflow_definitions
from .workflow_config import WorkflowConfig


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
                    on_abort(process)
                    aborted = True

            reads, _, _ = select.select([process.stdout], [], [], 1)
            if not reads:
                continue

            line = process.stdout.readline()
            if not line:
                break

            stdout_handler(line[:-1])

    retcode = process.poll()
    if check and retcode:
        raise CalledProcessError(retcode, process.args)
    return CompletedProcess(process.args, retcode)


def log_handler(log_file_path, line, workflow_id):
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

    workflow = Workflow.objects.get(id=workflow_id)
    if finished_jobs:
        workflow.finished_jobs = finished_jobs
    if total_jobs:
        workflow.total_jobs = total_jobs
    if state:
        workflow.state = state
    if job_id:
        workflow.job_ids.append(job_id)

    workflow.save()

@shared_task(base=AbortableTask, bind=True)
def run_workflow(
    self,
    workflow_config: WorkflowConfig,
    workflow_id: str,
    log_file_path: str,
    workflow_folder: str,
    input_dir: str,
    output_dir: str,
    token: str,
):
    pull_workflow_definitions(
        workflow_config.get("workflow_definition_dir"),
        workflow_config.get("workflow_definition_repo"),
        workflow_config.get("workflow_definition_branch"),
    )

    current_workflow_dir = os.path.join(
        workflow_config.get("workflow_dir"), workflow_id
    )

    shutil.copytree(
        os.path.join(workflow_config.get("workflow_definition_dir"), workflow_folder),
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
        workflow = Workflow.objects.get(id=workflow_id)
        workflow.state = WorkflowState.CANCELED
        workflow.save()

    res = stream_command(
        [
            "snakemake",
            "--sdm=conda",
            "--use-conda",
            "--conda-frontend=conda",
            "--executor=auth-tes",
            "--default-storage-provider=s3",
            f"--default-storage-prefix={workflow_config.get('default_storage_prefix')}",
            f"--storage-s3-endpoint-url={workflow_config.get('storage_s3_endpoint_url')}",
            f"--storage-s3-access-key={workflow_config.get('storage_s3_access_key')}",
            f"--storage-s3-secret-key={workflow_config.get('storage_s3_secret_key')}",
            f"--auth-tes-url={workflow_config.get('auth_tes_url')}",
            f"--auth-tes-oidc-client-id={workflow_config.get('auth_tes_oidc_client_id')}",
            f"--auth-tes-oidc-client-secret={workflow_config.get('auth_tes_oidc_client_secret')}",
            f"--auth-tes-oidc-url={workflow_config.get('auth_tes_oidc_url')}",
            f"--auth-tes-oidc-access-token={token}",
            f"--auth-tes-oidc-audience={workflow_config.get('auth_tes_oidc_audience')}",
            f"--container-image={workflow_config.get('container_image')}",
            f"--jobs={workflow_config.get('jobs')}",
        ],
        cwd=current_workflow_dir,
        stdout_handler=lambda line: log_handler(log_file_path, line, workflow_id),
        abort_condition=self.is_aborted,
        on_abort=on_abort,
    )

    shutil.rmtree(current_workflow_dir)

    if res.returncode != 0 and not self.is_aborted():
        workflow = Workflow.objects.get(id=workflow_id)
        workflow.state = WorkflowState.FAILED
        workflow.save()

    return res.returncode
