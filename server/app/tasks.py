import os
import logging
import shutil
from app import celery, app
from subprocess import Popen, PIPE, STDOUT, CalledProcessError, CompletedProcess


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


@celery.task
def run_workflow(
    workflow_id, log_file_path, workflow_folder, input_dir, output_dir, token
):
    def log_handler(line):
        with open(log_file_path, "a") as f:
            f.write(line + "\n")

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
        stdout_handler=log_handler,
    )

    shutil.rmtree(current_workflow_dir)

    return res.returncode
