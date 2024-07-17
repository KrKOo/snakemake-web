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
    auth_tes_oidc_client_id: str
    auth_tes_oidc_client_secret: str
    auth_tes_oidc_url: str
    auth_tes_oidc_audience: str
    container_image: str
    jobs: int
