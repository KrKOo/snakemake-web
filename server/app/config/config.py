import os
from typing import Tuple, Type
from pydantic import BaseModel
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource


class AppConfig(BaseModel):
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
    db_name: str


class Config(BaseSettings):
    model_config = SettingsConfigDict(yaml_file=os.environ.get("CONFIG_FILE", "../config.yaml"))

    app: AppConfig
    snakemake: SnakemakeConfig
    celery: CeleryConfig
    mongo: MongoConfig

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (env_settings, dotenv_settings, YamlConfigSettingsSource(settings_cls),)
    

config = Config() # type: ignore