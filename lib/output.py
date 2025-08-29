#!/usr/bin/env python3
"""
Output format adapters for Thunder Muscle data
"""
import json
import csv
import yaml
from pathlib import Path


def write_json(data, output_file):
    """Write data as JSON"""
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)


def write_csv(data, output_file):
    """Write data as CSV"""
    if not data:
        with open(output_file, "w") as f:
            f.write("")
        return

    # Handle nested structures by flattening the most useful part
    if isinstance(data, dict):
        # For analysis results, extract the top_domains list if it exists
        if "pattern_analysis" in data and "top_domains" in data["pattern_analysis"]:
            csv_data = data["pattern_analysis"]["top_domains"]
        elif "top_domains" in data:
            csv_data = data["top_domains"]
        else:
            # Convert single dict to list of dicts
            csv_data = [data]
    elif isinstance(data, list):
        csv_data = data
    else:
        csv_data = [{"value": str(data)}]

    if not csv_data:
        with open(output_file, "w") as f:
            f.write("")
        return

    fieldnames = csv_data[0].keys()
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)


def write_yaml(data, output_file):
    """Write data as YAML"""
    with open(output_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def write_data(data, output_file, format_type=None):
    """Write data in specified format, auto-detect from extension if not
    specified"""
    output_path = Path(output_file)

    if format_type is None:
        ext = output_path.suffix.lower()
        if ext == ".json":
            format_type = "json"
        elif ext == ".csv":
            format_type = "csv"
        elif ext in [".yaml", ".yml"]:
            format_type = "yaml"
        else:
            format_type = "json"

    if format_type == "json":
        write_json(data, output_file)
    elif format_type == "csv":
        write_csv(data, output_file)
    elif format_type == "yaml":
        write_yaml(data, output_file)
    else:
        raise ValueError(f"Unsupported format: {format_type}")

    return format_type
