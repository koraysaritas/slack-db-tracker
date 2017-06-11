import os
import sys
from pathlib import Path
import yaml


def is_worker_active(config, worker_name):
    try:
        return config[worker_name]["active"]
    except KeyError:
        return False


def get_config(debug=False):
    print("Reading config.")
    config_path = os.path.join(Path().resolve(), "config-dev.yaml" if debug else "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.load(f)
    except FileNotFoundError:
        print(str.format("Config file not found at location: {config_path}", config_path=config_path))
        sys.exit(1)
