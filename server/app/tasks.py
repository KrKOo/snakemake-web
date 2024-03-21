import logging
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
def run_workflow(log_file_path, workflow_folder, token):
    def handler(line):
        with open(log_file_path, "a") as f:
            f.write(line + "\n")

    return stream_command(
        [
            "snakemake",
            "--sdm=conda",
            "--executor=auth-tes",
            f"--snakefile={app.config['WORKFLOW_DEFINITION_DIR']}/{workflow_folder}/Snakefile",
            f"--directory={app.config['WORKFLOW_DEFINITION_DIR']}/{workflow_folder}",
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
        stdout_handler=handler,
    )
