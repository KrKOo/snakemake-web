from pydantic import BaseModel


class AppConfig(BaseModel):
    secret_key: str
    log_dir: str
    web_dir: str
    workflow_dir: str
    workflow_definition_dir: str
    workflow_definition_repo: str
    workflow_definition_branch: str
    oidc_url: str
    oidc_client_id: str
    oidc_client_secret: str
    oidc_audience: str


class SnakemakeConfig(BaseModel):
    snakemake_container_image: str
    snakemake_jobs: int
    default_storage_prefix: str
    tes_url: str
    storage_s3_endpoint_url: str
    storage_s3_access_key: str
    storage_s3_secret_key: str
    inbox_host: str
    download_host: str
    tmp_dir: str


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