import os
import uuid

from git import Repo

from .config import config
from .workflow_config import WorkflowConfig


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def pull_workflow_definitions(
    workflow_definition_directory: str, repository: str, branch: str = ""
):
    if not os.path.exists(workflow_definition_directory):
        os.makedirs(workflow_definition_directory)
        Repo.clone_from(repository, workflow_definition_directory)
    else:
        repo = Repo(workflow_definition_directory)
        repo.remotes.origin.pull()

        if branch:
            repo.git.checkout(branch)


def app_to_workflow_config():
    return WorkflowConfig(
        workflow_dir=config.app.workflow_dir,
        workflow_definition_dir=config.app.workflow_definition_dir,
        workflow_definition_branch=config.app.workflow_definition_branch,
        workflow_definition_repo=config.app.workflow_definition_repo,
        default_storage_prefix=config.snakemake.default_storage_prefix,
        storage_s3_endpoint_url=config.snakemake.storage_s3_endpoint_url,
        storage_s3_access_key=config.snakemake.storage_s3_access_key,
        storage_s3_secret_key=config.snakemake.storage_s3_secret_key,
        auth_tes_url=config.snakemake.tes_url,
        oidc_client_id=config.app.oidc_client_id,
        oidc_client_secret=config.app.oidc_client_secret,
        oidc_url=config.app.oidc_url,
        oidc_audience=config.app.oidc_audience,
        container_image=config.snakemake.snakemake_container_image,
        jobs=config.snakemake.snakemake_jobs,
        inbox_host=config.snakemake.inbox_host,
        download_host=config.snakemake.download_host,
        tmp_dir=config.snakemake.tmp_dir,
    )
