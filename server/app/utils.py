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
    workflow_definition_directory: str, repo: str, branch: str = None
):
    if not os.path.exists(workflow_definition_directory):
        os.makedirs(workflow_definition_directory)
        Repo.clone_from(repo, workflow_definition_directory)
    else:
        repo = Repo(workflow_definition_directory)
        repo.remotes.origin.pull()

    if branch:
        repo.git.checkout(branch)


def app_to_workflow_config(app: Flask):
    return WorkflowConfig(
        workflow_dir=app.config.get("WORKFLOW_DIR", ""),
        workflow_definition_dir=app.config.get("WORKFLOW_DEFINITION_DIR", ""),
        workflow_definition_branch=app.config.get("WORKFLOW_DEFINITION_BRANCH", ""),
        workflow_definition_repo=app.config.get("WORKFLOW_DEFINITION_REPO", ""),
        default_storage_prefix=app.config.get("DEFAULT_STORAGE_PREFIX", ""),
        storage_s3_endpoint_url=app.config.get("STORAGE_S3_ENDPOINT_URL", ""),
        storage_s3_access_key=app.config.get("STORAGE_S3_ACCESS_KEY", ""),
        storage_s3_secret_key=app.config.get("STORAGE_S3_SECRET_KEY", ""),
        auth_tes_url=app.config.get("TES_URL", ""),
        auth_tes_oidc_client_id=app.config.get("OIDC_CLIENT_ID", ""),
        auth_tes_oidc_client_secret=app.config.get("OIDC_CLIENT_SECRET", ""),
        auth_tes_oidc_url=app.config.get("OIDC_URL", ""),
        auth_tes_oidc_audience=app.config.get("OIDC_AUDIENCE", ""),
        container_image=app.config.get("SNAKEMAKE_CONTAINER_IMAGE", ""),
        jobs=app.config.get("SNAKEMAKE_JOBS", 1),
    )
