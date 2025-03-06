import os
import uuid

from flask import Flask
from git import Repo

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


def app_to_workflow_config(app: Flask):
    return WorkflowConfig(
        workflow_dir=app.config["APP_WORKFLOW_DIR"],
        workflow_definition_dir=app.config["APP_WORKFLOW_DEFINITION_DIR"],
        workflow_definition_branch=app.config["APP_WORKFLOW_DEFINITION_BRANCH"],
        workflow_definition_repo=app.config["APP_WORKFLOW_DEFINITION_REPO"],
        default_storage_prefix=app.config["SNAKEMAKE_DEFAULT_STORAGE_PREFIX"],
        storage_s3_endpoint_url=app.config["SNAKEMAKE_STORAGE_S3_ENDPOINT_URL"],
        storage_s3_access_key=app.config["SNAKEMAKE_STORAGE_S3_ACCESS_KEY"],
        storage_s3_secret_key=app.config["SNAKEMAKE_STORAGE_S3_SECRET_KEY"],
        auth_tes_url=app.config["SNAKEMAKE_TES_URL"],
        oidc_client_id=app.config["APP_OIDC_CLIENT_ID"],
        oidc_client_secret=app.config["APP_OIDC_CLIENT_SECRET"],
        oidc_url=app.config["APP_OIDC_URL"],
        oidc_audience=app.config["APP_OIDC_AUDIENCE"],
        container_image=app.config["SNAKEMAKE_SNAKEMAKE_CONTAINER_IMAGE"],
        jobs=app.config["SNAKEMAKE_SNAKEMAKE_JOBS"],
        inbox_host=app.config["SNAKEMAKE_INBOX_HOST"],
        download_host=app.config["SNAKEMAKE_DOWNLOAD_HOST"],
        tmp_dir=app.config["SNAKEMAKE_TMP_DIR"],
    )
