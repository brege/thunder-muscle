#!/usr/bin/env python3
"""
Configuration management for Thunder Muscle
"""
import yaml
from pathlib import Path


def load_config(config_file="config.yaml"):
    """Load configuration from YAML file"""
    config_path = Path(config_file)
    if not config_path.exists():
        return {}

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_profile_path(config, profile_arg=None):
    """Get Thunderbird profile path from config or argument"""
    if profile_arg:
        return profile_arg

    # New config structure
    profile_name = config.get("thunderbird", {}).get("profile")
    if not profile_name:
        # Backward compatibility
        profile_name = config.get("data", {}).get("profile")

    if profile_name:
        return f"assets/{profile_name}"

    raise ValueError("No profile specified in config or arguments")


def get_output_format(config, format_arg=None):
    """Get output format from config or argument"""
    if format_arg:
        return format_arg

    # New config structure
    format_val = config.get("defaults", {}).get("output_format")
    if not format_val:
        # Backward compatibility
        format_val = config.get("data", {}).get("default_format", "json")

    return format_val


def get_data_directory(config):
    """Get data directory from config (deprecated - use get_directories)"""
    # Backward compatibility
    return config.get("data", {}).get("directory", "data")


def get_directories(config):
    """Get directory structure from config"""
    directories = config.get("directories", {})
    return {
        "assets": directories.get("assets", "assets"),
        "output": directories.get("output", "output"),
        "cache": directories.get("cache", "cache"),
    }


def get_output_structure(config):
    """Get output subdirectory structure from config"""
    structure = config.get("output_structure", {})
    return {
        "datasets": structure.get("datasets", "output/datasets"),
        "analysis": structure.get("analysis", "output/analysis"),
        "plots": structure.get("plots", "output/plots"),
    }


def get_default_complete_dataset_path(config):
    """Get path to complete dataset from config"""
    return config.get("defaults", {}).get(
        "complete_dataset", "assets/complete_dataset.json"
    )


def get_default_extract_filename(config):
    """Get default extraction filename from config (deprecated)"""
    # Backward compatibility
    return config.get("data", {}).get(
        "default_extract_filename", "complete_dataset.json"
    )


def should_auto_create_dirs(config):
    """Check if directories should be auto-created"""
    return config.get("workflows", {}).get("auto_create_dirs", True)


def ensure_directories_exist(config):
    """Create necessary directories if they don't exist"""
    if not should_auto_create_dirs(config):
        return

    from pathlib import Path

    # Create main directories
    directories = get_directories(config)
    for dir_path in directories.values():
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # Create output subdirectories
    output_structure = get_output_structure(config)
    for dir_path in output_structure.values():
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def get_extraction_filters(config):
    """Get extraction filters from config"""
    return config.get("filters", {})


def should_filter_email(email, filters):
    """Check if email should be filtered out based on config filters"""
    if not filters:
        return False

    # Check ignore_from_domains (backward compatibility with ignore_domains)
    ignore_from_domains = filters.get(
        "ignore_from_domains", filters.get("ignore_domains", [])
    )
    if ignore_from_domains:
        domain = email.get("from_domain", "").lower()
        for ignore_pattern in ignore_from_domains:
            if ignore_pattern.startswith("*."):
                if domain.endswith(ignore_pattern[2:].lower()):
                    return True
            elif domain == ignore_pattern.lower():
                return True

    # Check include_from_domains (overrides ignore, backward compatibility)
    include_from_domains = filters.get(
        "include_from_domains", filters.get("include_domains", [])
    )
    if include_from_domains:
        domain = email.get("from_domain", "").lower()
        included = False
        for include_pattern in include_from_domains:
            if include_pattern.startswith("*."):
                if domain.endswith(include_pattern[2:].lower()):
                    included = True
                    break
            elif domain == include_pattern.lower():
                included = True
                break
        if not included:
            return True

    # Check ignore_to_domains
    ignore_to_domains = filters.get("ignore_to_domains", [])
    if ignore_to_domains:
        to_field = email.get("to", "").lower()
        for ignore_pattern in ignore_to_domains:
            if ignore_pattern.lower() in to_field:
                return True

    # Check ignore_folders
    ignore_folders = filters.get("ignore_folders", [])
    if ignore_folders:
        folder = email.get("folder", "").lower()
        for ignore_folder in ignore_folders:
            if ignore_folder.lower() in folder:
                return True

    # Check date ranges
    date_after = filters.get("date_after")
    date_before = filters.get("date_before")
    if date_after or date_before:
        email_date = email.get("date", "")
        if date_after and email_date < date_after:
            return True
        if date_before and email_date > date_before:
            return True

    return False
