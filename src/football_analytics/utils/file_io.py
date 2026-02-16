"""File I/O utilities for reading/writing JSON and managing backups.

This module provides simple, reusable functions for file operations used
throughout the football analytics pipeline.

TODO (Framework Evolution):
    - Add support for other formats (CSV, Parquet, Feather)
    - Implement compression (gzip, bz2) for storage efficiency
    - Add checksum validation for data integrity
    - Cloud storage support (S3, Google Cloud Storage)
"""

import json
import shutil
from pathlib import Path
from typing import Any, Union


def save_json(
    data: Union[dict[str, Any], list], filepath: Union[str, Path], indent: int = 2
) -> Path:
    """
    Save data to JSON file with pretty formatting.

    Creates parent directories if they don't exist.

    Args:
        data: Dictionary or list to save
        filepath: Path where to save the JSON file
        indent: Number of spaces for indentation (default: 2)

    Returns:
        Path object of the saved file

    Example:
        >>> save_json({"team": "Liverpool"}, "data/teams.json")
        PosixPath('data/teams.json')
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)

    return filepath


def load_json(filepath: Union[str, Path]) -> Union[dict[str, Any], list]:
    """
    Load JSON file and return parsed data.

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed JSON data (dict or list)

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON

    Example:
        >>> data = load_json("data/teams.json")
        >>> data["team"]
        'Liverpool'
    """
    filepath = Path(filepath)

    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def file_exists(filepath: Union[str, Path]) -> bool:
    """
    Check if file exists.

    Args:
        filepath: Path to check

    Returns:
        True if file exists, False otherwise

    Example:
        >>> file_exists("data/teams.json")
        True
    """
    return Path(filepath).exists()


def backup_directory(
    source_dir: Union[str, Path], backup_dir: Union[str, Path] = "data/backup"
) -> Path:
    """
    Create a backup copy of an entire directory.

    Preserves directory structure. If backup already exists, it will be
    overwritten.

    Args:
        source_dir: Directory to backup
        backup_dir: Root directory for backups (default: data/backup)

    Returns:
        Path to the backup directory

    Example:
        >>> backup_directory("data/raw/12345")
        PosixPath('data/backup/12345')

    TODO (Framework Evolution):
        - Add incremental backups (only copy changed files)
        - Add timestamp-based backup versions
        - Add backup rotation (keep last N backups)
        - Add compression for space efficiency
    """
    source_dir = Path(source_dir)
    backup_dir = Path(backup_dir)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    # Create backup path preserving structure
    # e.g., data/raw/12345 → data/backup/12345
    relative_path = source_dir.name
    backup_path = backup_dir / relative_path

    # Remove existing backup if present
    if backup_path.exists():
        shutil.rmtree(backup_path)

    # Copy directory
    shutil.copytree(source_dir, backup_path)

    return backup_path


def get_file_size_mb(filepath: Union[str, Path]) -> float:
    """
    Get file size in megabytes.

    Args:
        filepath: Path to file

    Returns:
        File size in MB

    Example:
        >>> get_file_size_mb("data/large_file.json")
        15.3
    """
    filepath = Path(filepath)
    size_bytes = filepath.stat().st_size
    return size_bytes / (1024 * 1024)


def ensure_directory(dirpath: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        dirpath: Directory path

    Returns:
        Path object of the directory

    Example:
        >>> ensure_directory("data/processed")
        PosixPath('data/processed')
    """
    dirpath = Path(dirpath)
    dirpath.mkdir(parents=True, exist_ok=True)
    return dirpath
