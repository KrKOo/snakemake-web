from typing import TypedDict


class WorkflowConfig(TypedDict):
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
    result_bucket: str
    inbox_host: str
    download_host: str
    tmp_dir: str
