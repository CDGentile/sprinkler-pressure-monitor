"""
Configuration loader with environment variable support.

Loads config from YAML file and expands environment variables
using ${VAR} or ${VAR:-default} syntax.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False

logger = logging.getLogger(__name__)

# Pattern for environment variable substitution
# Matches ${VAR} or ${VAR:-default}
ENV_VAR_PATTERN = re.compile(r'\$\{([^}:]+)(?::-([^}]*))?\}')


def _load_dotenv_file(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from .env file.

    Args:
        env_path: Optional path to .env file. If None, searches in
                  current directory and parent directories.

    Returns:
        True if .env file was loaded, False otherwise
    """
    if not _HAS_DOTENV:
        logger.debug("python-dotenv not installed, skipping .env loading")
        return False

    if env_path:
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment from {env_path}")
            return True
        else:
            logger.warning(f".env file not found: {env_path}")
            return False

    # Search for .env file
    load_dotenv()  # This searches current and parent directories

    # Check if we found one
    for search_path in [Path.cwd(), Path.cwd().parent]:
        env_file = search_path / ".env"
        if env_file.exists():
            logger.info(f"Loaded environment from {env_file}")
            return True

    logger.debug("No .env file found")
    return False


def expand_env_vars(value: Any) -> Any:
    """
    Recursively expand environment variables in config values.

    Supports:
    - ${VAR} - replaced with env var value, empty string if not set
    - ${VAR:-default} - replaced with env var value, or default if not set

    Args:
        value: Config value (can be str, dict, list, or other)

    Returns:
        Value with environment variables expanded
    """
    if isinstance(value, str):
        return _expand_string(value)
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    else:
        return value


def _expand_string(value: str) -> Union[str, int, float, bool]:
    """
    Expand environment variables in a string value.

    Also handles type conversion for common patterns.
    """
    def replacer(match):
        var_name = match.group(1)
        default = match.group(2)

        env_value = os.environ.get(var_name)

        if env_value is not None:
            return env_value
        elif default is not None:
            return default
        else:
            logger.warning(f"Environment variable {var_name} not set and no default provided")
            return ""

    result = ENV_VAR_PATTERN.sub(replacer, value)

    # Try type conversion for simple values
    if result == value:
        # No substitution happened, return as-is
        return value

    # Check if the entire string was a variable (for type conversion)
    if ENV_VAR_PATTERN.fullmatch(value):
        return _convert_type(result)

    return result


def _convert_type(value: str) -> Union[str, int, float, bool]:
    """
    Convert string to appropriate Python type.

    Handles: int, float, bool, None
    """
    # Boolean
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    if value.lower() in ("false", "no", "0", "off"):
        return False

    # None
    if value.lower() in ("null", "none", ""):
        return None

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    return value


def load_config(path: str = "config.yaml", site: str = "main_site") -> Dict:
    """
    Load configuration from YAML file with environment variable expansion.

    Loads .env file, reads the YAML config, expands ${VAR:-default} references,
    then merges the selected site config with global sections.

    Args:
        path: Path to YAML config file
        site: Site name to load (e.g., 'main_site', 'aux_site')

    Returns:
        Merged configuration dictionary for the selected site

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If sites section missing or site not found
    """
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load .env file (look in same directory as config)
    _load_dotenv_file(config_path.parent / ".env")

    # Load YAML config
    logger.info(f"Loading config from {config_path}")

    with open(config_path, "r") as f:
        full_config = yaml.safe_load(f)

    if full_config is None:
        full_config = {}

    # Expand environment variables
    full_config = expand_env_vars(full_config)
    logger.debug("Environment variables expanded in config")

    # Validate and extract site config
    if "sites" not in full_config:
        raise ValueError("No 'sites' key found in configuration.")

    if site not in full_config["sites"]:
        available = list(full_config["sites"].keys())
        raise ValueError(
            f"Site '{site}' not found in configuration. "
            f"Available sites: {available}"
        )

    selected_site_config = full_config["sites"][site]

    # Merge selected site config with top-level config sections
    merged_config = {
        "sensor": selected_site_config["sensor"],
        "sampling": full_config.get("sampling", {}),
        "simulation": full_config.get("simulation", {}),
        "mqtt": full_config.get("mqtt", {}),
        "outputs": full_config.get("outputs", {}),
        "influxdb": full_config.get("influxdb", {}),
        "logging": full_config.get("logging", {}),
    }

    # Set location from site name if not explicitly set in influxdb config
    if "influxdb" in merged_config:
        if not merged_config["influxdb"].get("location") or \
           merged_config["influxdb"]["location"] == "unknown":
            merged_config["influxdb"]["location"] = site

    return merged_config
