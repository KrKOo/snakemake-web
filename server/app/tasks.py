import os
import re
import logging
import shutil
import signal
import select
from celery.contrib.abortable import AbortableTask
from app import celery, app
from subprocess import Popen, PIPE, STDOUT, CalledProcessError, CompletedProcess

from .models import Workflow, WorkflowState
from .wrappers import with_updated_workflow_definitions


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


@celery.task(base=AbortableTask, bind=True)
@with_updated_workflow_definitions
def run_workflow(
    self,
    workflow_id,
    log_file_path,
    workflow_folder,
    input_dir,
    output_dir,
    token,
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
            f"--default-storage-prefix={app.config['DEFAULT_STORAGE_PREFIX']}",
            f"--storage-s3-endpoint-url={app.config['STORAGE_S3_ENDPOINT_URL']}",
            f"--storage-s3-access-key={app.config['STORAGE_S3_ACCESS_KEY']}",
            f"--storage-s3-secret-key={app.config['STORAGE_S3_SECRET_KEY']}",
            f"--auth-tes-url={app.config['TES_URL']}",
            f"--auth-tes-oidc-client-id={app.config['OIDC_CLIENT_ID']}",
            f"--auth-tes-oidc-client-secret={app.config['OIDC_CLIENT_SECRET']}",
            f"--auth-tes-oidc-url={app.config['OIDC_URL']}",
            f"--auth-tes-oidc-access-token={token}",
            f"--auth-tes-oidc-audience={app.config['OIDC_AUDIENCE']}",
            f"--container-image={app.config['SNAKEMAKE_CONTAINER_IMAGE']}",
            f"--jobs={app.config['SNAKEMAKE_JOBS']}",
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
