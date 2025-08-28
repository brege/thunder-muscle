#!/usr/bin/env python3
"""
Configuration management for Thunder Muscle
"""
import yaml
from pathlib import Path

def load_config(config_file='config.yaml'):
    """Load configuration from YAML file"""
    config_path = Path(config_file)
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_profile_path(config, profile_arg=None):
    """Get Thunderbird profile path from config or argument"""
    if profile_arg:
        return profile_arg
    
    profile_name = config.get('data', {}).get('profile')
    if profile_name:
        return f"assets/{profile_name}"
    
    raise ValueError("No profile specified in config or arguments")

def get_output_format(config, format_arg=None):
    """Get output format from config or argument"""
    if format_arg:
        return format_arg
    
    return config.get('data', {}).get('default_format', 'json')

def get_data_directory(config):
    """Get data directory from config"""
    return config.get('data', {}).get('directory', 'data')