from pydantic import ValidationError
from .config import Config
import yaml


def load_config(file_path: str) -> Config:
    with open(file_path, "r") as f:
        config_dict = yaml.safe_load(f)

    try:
        config = Config(**config_dict)
    except ValidationError as e:
        print("Config validation error:", e)
        raise

    return config
