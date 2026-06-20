import yaml
from pathlib import Path
from copy import deepcopy


def load_config(path: str) -> dict:
    path = Path(path)
    with open(path) as f:
        cfg = yaml.safe_load(f)

    if "defaults" in cfg:
        base_path = path.parent / cfg.pop("defaults")
        base = load_config(base_path)
        cfg = merge_configs(base, cfg)

    return cfg


def merge_configs(base: dict, override: dict) -> dict:
    result = deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = merge_configs(result[k], v)
        else:
            result[k] = v
    return result


class ConfigNamespace:
    """Dot-access wrapper for nested config dicts."""

    def __init__(self, d: dict):
        for k, v in d.items():
            setattr(self, k, ConfigNamespace(v) if isinstance(v, dict) else v)

    def __repr__(self):
        return str(self.__dict__)
