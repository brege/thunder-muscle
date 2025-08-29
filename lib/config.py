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

def get_extraction_filters(config):
    """Get extraction filters from config"""
    return config.get('filters', {})

def should_filter_email(email, filters):
    """Check if email should be filtered out based on config filters"""
    if not filters:
        return False
    
    # Check ignore_from_domains (backward compatibility with ignore_domains)
    ignore_from_domains = filters.get('ignore_from_domains', filters.get('ignore_domains', []))
    if ignore_from_domains:
        domain = email.get('from_domain', '').lower()
        for ignore_pattern in ignore_from_domains:
            if ignore_pattern.startswith('*.'):
                if domain.endswith(ignore_pattern[2:].lower()):
                    return True
            elif domain == ignore_pattern.lower():
                return True
    
    # Check include_from_domains (overrides ignore, backward compatibility)
    include_from_domains = filters.get('include_from_domains', filters.get('include_domains', []))
    if include_from_domains:
        domain = email.get('from_domain', '').lower()
        included = False
        for include_pattern in include_from_domains:
            if include_pattern.startswith('*.'):
                if domain.endswith(include_pattern[2:].lower()):
                    included = True
                    break
            elif domain == include_pattern.lower():
                included = True
                break
        if not included:
            return True
    
    # Check ignore_to_domains
    ignore_to_domains = filters.get('ignore_to_domains', [])
    if ignore_to_domains:
        to_field = email.get('to', '').lower()
        for ignore_pattern in ignore_to_domains:
            if ignore_pattern.lower() in to_field:
                return True
    
    # Check ignore_folders
    ignore_folders = filters.get('ignore_folders', [])
    if ignore_folders:
        folder = email.get('folder', '').lower()
        for ignore_folder in ignore_folders:
            if ignore_folder.lower() in folder:
                return True
    
    # Check date ranges
    date_after = filters.get('date_after')
    date_before = filters.get('date_before')
    if date_after or date_before:
        email_date = email.get('date', '')
        if date_after and email_date < date_after:
            return True
        if date_before and email_date > date_before:
            return True
    
    return False