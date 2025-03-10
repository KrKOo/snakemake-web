import yaml
from typing import Any, Dict
from pydantic import ValidationError
from .config import Config


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """Recursively flatten a nested dictionary."""
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key.upper(), v))
    return dict(items)


class YAMLConfig:
    """Custom config loader for Flask that flattens nested YAML configs."""
    
    def __init__(self, path: str):
        with open(path, "r") as f:
            raw_config = yaml.safe_load(f)
        
        try:
            self._config = Config(**raw_config)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}")
        
        self._flat_config = flatten_dict(self._config.model_dump())

    def to_dict(self) -> dict:
        """Return the flattened configuration dictionary."""
        return self._flat_config