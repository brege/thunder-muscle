#!/usr/bin/env python3
"""
Profile backup tool for Thunder Muscle
"""
import argparse
import shutil
import sys
from pathlib import Path


def backup_profile(source, destination, exclude_patterns=None):
    """Backup Thunderbird profile with exclusions"""
    source_path = Path(source).expanduser()
    dest_path = Path(destination)

    if not source_path.exists():
        print(f"Error: Source profile path does not exist: {source_path}")
        return False

    print(f"Backing up profile from {source_path} to {dest_path}")

    # Create destination directory
    dest_path.mkdir(parents=True, exist_ok=True)

    exclude_patterns = exclude_patterns or []
    copied_count = 0
    skipped_count = 0

    def should_exclude(file_path):
        """Check if file should be excluded based on patterns"""
        file_name = file_path.name
        for pattern in exclude_patterns:
            if pattern.endswith("*"):
                if file_name.startswith(pattern[:-1]):
                    return True
            elif pattern.startswith("*"):
                if file_name.endswith(pattern[1:]):
                    return True
            elif file_name == pattern:
                return True
        return False

    # Copy files and directories
    for item in source_path.rglob("*"):
        if item.is_file() and not should_exclude(item):
            relative_path = item.relative_to(source_path)
            dest_file = dest_path / relative_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                shutil.copy2(item, dest_file)
                copied_count += 1
            except PermissionError:
                print(f"Warning: Permission denied copying {item}")
                skipped_count += 1
        elif should_exclude(item):
            skipped_count += 1

    print("Profile backup completed: ")
    print(f"{copied_count} files copied, {skipped_count} skipped")
    return True


def main():
    parser = argparse.ArgumentParser(description="Backup Thunderbird profile")
    parser.add_argument("source", help="Source profile path")
    parser.add_argument("destination", help="Destination backup path")
    parser.add_argument(
        "--exclude-patterns",
        nargs="*",
        default=[],
        help="File patterns to exclude from backup",
    )

    args = parser.parse_args()

    success = backup_profile(args.source, args.destination, args.exclude_patterns)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
