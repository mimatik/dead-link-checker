"""Configuration storage - CRUD operations on JSON config files"""

import json
import os
from typing import Dict, List

from app.core.config import CONFIG_DIR


def _ensure_config_dir():
    """Ensure configuration directory exists"""
    # Directory is already created in config module
    pass


def _get_config_path(config_id: str) -> str:
    """Get full path to config file"""
    return os.path.join(CONFIG_DIR, f"{config_id}.json")


def list_configs() -> List[Dict]:
    """
    List all available configurations

    Returns:
        List of complete configurations
    """
    _ensure_config_dir()

    configs = []
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith(".json"):
            config_id = filename[:-5]  # Remove .json extension
            try:
                config = get_config(config_id)
                # Add id to config if not present
                config["id"] = config_id
                configs.append(config)
            except Exception:
                # Skip invalid configs
                continue

    return sorted(configs, key=lambda x: x["id"])


def get_config(config_id: str) -> Dict:
    """
    Get configuration by ID

    Args:
        config_id: Configuration identifier

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config doesn't exist
    """
    config_path = _get_config_path(config_id)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration '{config_id}' not found")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_config(config_id: str, config_data: Dict) -> Dict:
    """
    Create new configuration

    Args:
        config_id: Configuration identifier
        config_data: Configuration dictionary

    Returns:
        Created configuration

    Raises:
        ValueError: If config already exists
    """
    _ensure_config_dir()
    config_path = _get_config_path(config_id)

    if os.path.exists(config_path):
        raise ValueError(f"Configuration '{config_id}' already exists")

    # Add id to config data
    config_data["id"] = config_id

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    return config_data


def update_config(config_id: str, config_data: Dict) -> Dict:
    """
    Update existing configuration

    Args:
        config_id: Configuration identifier
        config_data: Configuration dictionary

    Returns:
        Updated configuration

    Raises:
        FileNotFoundError: If config doesn't exist
    """
    config_path = _get_config_path(config_id)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration '{config_id}' not found")

    # Add/update id in config data
    config_data["id"] = config_id

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    return config_data


def delete_config(config_id: str) -> bool:
    """
    Delete configuration

    Args:
        config_id: Configuration identifier

    Returns:
        True if deleted successfully

    Raises:
        FileNotFoundError: If config doesn't exist
    """
    config_path = _get_config_path(config_id)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration '{config_id}' not found")

    os.remove(config_path)
    return True


def get_default_config() -> Dict:
    """Get default configuration template"""
    return {
        "name": "New Configuration",
        "start_url": "https://example.com",
        "timeout": 15,
        "delay": 0.5,
        "max_depth": None,
        "output_dir": "reports",
        "show_skipped_links": False,
        "whitelist_codes": [403, 999],
        "domain_rules": {
            "linkedin.com": {
                "allowed_codes": [999, 429],
                "description": "LinkedIn rate limiting",
            },
            "twitter.com": {
                "allowed_codes": [403],
                "description": "Twitter access restriction",
            },
            "x.com": {
                "allowed_codes": [403],
                "description": "X/Twitter access restriction",
            },
        },
    }
