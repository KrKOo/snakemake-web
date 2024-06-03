import os
import re
import logging
import shutil
from app import celery, app
from subprocess import Popen, PIPE, STDOUT, CalledProcessError, CompletedProcess
from .models import Workflow, WorkflowState
from .wrappers import with_updated_workflow_definitions


def stream_command(
    args,
    *,
    stdout_handler=logging.info,
    check=True,
    text=True,
    **kwargs,
):
    """Mimic subprocess.run, while processing the command output in real time."""
    with Popen(args, text=text, stdout=PIPE, stderr=STDOUT, **kwargs) as process:
        for line in process.stdout:
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
    elif "WorkflowError" in line or "OSError" in line:
        state = WorkflowState.FAILED
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


@celery.task
@with_updated_workflow_definitions
def run_workflow(
    workflow_id, log_file_path, workflow_folder, input_dir, output_dir, token
):
    current_workflow_dir = os.path.join(app.config["WORKFLOW_DIR"], workflow_id)

    shutil.copytree(
        os.path.join(app.config["WORKFLOW_DEFINITION_DIR"], workflow_folder),
        current_workflow_dir,
    )

    snakefile = os.path.join(app.config["WORKFLOW_DIR"], workflow_id, "Snakefile")

    with open(snakefile) as f:
        snakefile_template = f.read()

    with open(snakefile, "w") as f:
        f.write(
            snakefile_template.replace("<input_dir>", f"'{input_dir}'").replace(
                "<output_dir>", f"'{output_dir}'"
            )
        )

    res = stream_command(
        [
            "snakemake",
            "--sdm=conda",
            "--use-conda",
            "--conda-frontend=conda",
            "--executor=auth-tes",
            "--default-storage-provider=s3",
            f"--default-storage-prefix={app.config['DEFAULT_STORAGE_PREFIX']}",
            f"--storage-s3-endpoint-url={app.config['STORAGE_S3_ENDPOINT_URL']}",
            f"--storage-s3-access-key={app.config['STORAGE_S3_ACCESS_KEY']}",
            f"--storage-s3-secret-key={app.config['STORAGE_S3_SECRET_KEY']}",
            f"--auth-tes-url={app.config['TES_URL']}",
            f"--auth-tes-oidc-client-id={app.config['TES_OIDC_CLIENT_ID']}",
            f"--auth-tes-oidc-client-secret={app.config['TES_OIDC_CLIENT_SECRET']}",
            f"--auth-tes-oidc-url={app.config['TES_OIDC_URL']}",
            f"--auth-tes-oidc-access-token={token}",
            f"--auth-tes-oidc-audience={app.config['TES_OIDC_AUDIENCE']}",
            f"--container-image={app.config['SNAKEMAKE_CONTAINER_IMAGE']}",
            f"--jobs={app.config['SNAKEMAKE_JOBS']}",
        ],
        cwd=current_workflow_dir,
        stdout_handler=lambda line: log_handler(log_file_path, line, workflow_id),
    )

    shutil.rmtree(current_workflow_dir)

    if res.returncode != 0:
        workflow = Workflow.objects.get(id=workflow_id)
        workflow.state = WorkflowState.FAILED
        workflow.save()

    return res.returncode
