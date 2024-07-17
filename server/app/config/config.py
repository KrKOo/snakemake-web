from pydantic import BaseModel


class AppConfig(BaseModel):
    secret_key: str
    log_dir: str
    web_dir: str
    workflow_dir: str
    workflow_definition_dir: str
    workflow_definition_repo: str
    workflow_definition_branch: str


class SnakemakeConfig(BaseModel):
    snakemake_container_image: str
    snakemake_jobs: int
    default_storage_prefix: str
    tes_url: str
    tes_basic_auth_user: str
    tes_basic_auth_password: str
    tes_oidc_url: str
    tes_oidc_client_id: str
    tes_oidc_client_secret: str
    tes_oidc_audience: str
    storage_s3_endpoint_url: str
    storage_s3_access_key: str
    storage_s3_secret_key: str


class CeleryConfig(BaseModel):
    broker_url: str
    result_backend: str


class MongoConfig(BaseModel):
    mongodb_uri: str


class Config(BaseModel):
    app: AppConfig
    snakemake: SnakemakeConfig
    celery: CeleryConfig
    mongo: MongoConfig
