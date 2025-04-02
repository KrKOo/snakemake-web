from typing import Dict
from pydantic import BaseModel

from app.config import Config


class WorkflowConfig(BaseModel):
    workflow_dir: str
    workflow_definition_dir: str
    workflow_definition_repo: str
    workflow_definition_branch: str
    default_storage_prefix: str
    storage_s3_endpoint_url: str
    storage_s3_access_key: str
    storage_s3_secret_key: str
    auth_tes_url: str
    oidc_client_id: str
    oidc_client_secret: str
    oidc_url: str
    oidc_audience: str
    container_image: str
    jobs: int
    inbox_host: str
    download_host: str
    tmp_dir: str


    @classmethod
    def from_app_config(cls, config: Config) -> "WorkflowConfig":
        data: Dict[str, str | int] = {
            "workflow_dir": config.app.workflow_dir,
            "workflow_definition_dir": config.app.workflow_definition_dir,
            "workflow_definition_repo": config.app.workflow_definition_repo,
            "workflow_definition_branch": config.app.workflow_definition_branch,
            "default_storage_prefix": config.snakemake.default_storage_prefix,
            "storage_s3_endpoint_url": config.snakemake.storage_s3_endpoint_url,
            "storage_s3_access_key": config.snakemake.storage_s3_access_key,
            "storage_s3_secret_key": config.snakemake.storage_s3_secret_key,
            "auth_tes_url": config.snakemake.tes_url,
            "oidc_client_id": config.app.oidc_client_id,
            "oidc_client_secret": config.app.oidc_client_secret,
            "oidc_url": config.app.oidc_url,
            "oidc_audience": config.app.oidc_audience,
            "container_image": config.snakemake.snakemake_container_image,
            "jobs": config.snakemake.snakemake_jobs,
            "inbox_host": config.snakemake.inbox_host,
            "download_host": config.snakemake.download_host,
            "tmp_dir": config.snakemake.tmp_dir,
        }

        return cls.model_validate(data)