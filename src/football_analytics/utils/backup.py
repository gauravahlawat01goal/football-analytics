"""Backup and checkpoint management for data collection.

This module provides a multi-layer backup strategy to prevent data loss:
1. Primary storage: data/raw/
2. Local backup: data/backup/
3. External backup: Configurable external storage (e.g., Dropbox)

Key features:
- Automatic backup on save
- Checkpoint creation at milestones
- Resumable operations
- Compression for external storage
"""

import json
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..utils.logging_utils import get_logger


class BackupManager:
    """
    Multi-tier backup manager for data protection.
    
    Implements three-tier backup strategy:
    1. Primary: data/raw/
    2. Local backup: data/backup/
    3. External: Configurable external path
    
    Args:
        primary_dir: Primary data directory (default: data/raw)
        backup_dir: Local backup directory (default: data/backup)
        external_dir: External backup path (optional)
    
    Example:
        >>> backup = BackupManager()
        >>> backup.save_with_backup(data, "fixtures/2023/match_123.json")
        >>> backup.create_checkpoint("after_collection")
    """
    
    # Constants
    MAX_CHECKPOINT_NAME_LENGTH = 100
    
    def __init__(
        self,
        primary_dir: str = "data/raw",
        backup_dir: str = "data/backup", 
        external_dir: Optional[str] = None
    ):
        """Initialize backup manager."""
        # Input validation
        if not isinstance(primary_dir, str) or not primary_dir.strip():
            raise ValueError(f"Invalid primary_dir: {primary_dir}")
        
        if not isinstance(backup_dir, str) or not backup_dir.strip():
            raise ValueError(f"Invalid backup_dir: {backup_dir}")
        
        if external_dir is not None and (not isinstance(external_dir, str) or not external_dir.strip()):
            raise ValueError(f"Invalid external_dir: {external_dir}")
        
        self.primary = Path(primary_dir)
        self.local_backup = Path(backup_dir)
        
        # External backup (optional)
        if external_dir:
            self.external_backup = Path(external_dir).expanduser()
        else:
            # Default to user's home directory if available
            home = Path.home()
            self.external_backup = home / "football-analytics-backup"
        
        # Create all directories
        try:
            for path in [self.primary, self.local_backup, self.external_backup]:
                path.mkdir(parents=True, exist_ok=True)
        except (IOError, OSError) as e:
            raise ValueError(f"Failed to create directories: {e}")
        
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Backup manager initialized:")
        self.logger.info(f"  Primary: {self.primary}")
        self.logger.info(f"  Local backup: {self.local_backup}")
        self.logger.info(f"  External backup: {self.external_backup}")
    
    def _sanitize_filepath(self, filepath: str) -> Path:
        """
        Sanitize and validate filepath to prevent directory traversal.
        
        Args:
            filepath: Relative filepath to sanitize
        
        Returns:
            Sanitized Path object
        
        Raises:
            ValueError: If filepath is invalid or contains path traversal
        """
        if not isinstance(filepath, str) or not filepath.strip():
            raise ValueError(f"Invalid filepath: {filepath}")
        
        # Convert to Path and resolve
        path = Path(filepath)
        
        # Check for absolute paths
        if path.is_absolute():
            raise ValueError(f"Absolute paths not allowed: {filepath}")
        
        # Check for path traversal attempts
        if '..' in path.parts:
            raise ValueError(f"Path traversal detected: {filepath}")
        
        # Resolve against primary to check final path
        resolved = (self.primary / path).resolve()
        
        # Ensure resolved path is within primary directory
        try:
            resolved.relative_to(self.primary.resolve())
        except ValueError:
            raise ValueError(f"Path escapes primary directory: {filepath}")
        
        return path
    
    def save_with_backup(self, data: Any, filepath: str) -> Path:
        """
        Save data to primary location and backup simultaneously.
        
        Args:
            data: Data to save (will be JSON serialized)
            filepath: Relative path within data directory
        
        Returns:
            Path to primary file
        
        Example:
            >>> backup = BackupManager()
            >>> data = {"fixture_id": 123, "events": [...]}
            >>> backup.save_with_backup(data, "fixtures/2023/match_123.json")
        """
        # Sanitize filepath to prevent path traversal
        sanitized_path = self._sanitize_filepath(filepath)
        
        # Save to primary
        primary_path = self.primary / sanitized_path
        
        try:
            primary_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(primary_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved to primary: {primary_path}")
            
            # Immediate backup to local
            backup_path = self.local_backup / sanitized_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(primary_path, backup_path)
            
            self.logger.debug(f"Backed up to: {backup_path}")
            
            return primary_path
        
        except (IOError, OSError, TypeError) as e:
            self.logger.error(f"Failed to save with backup {filepath}: {e}")
            raise
    
    def create_checkpoint(self, checkpoint_name: str) -> Path:
        """
        Create compressed checkpoint of all collected data.
        
        Creates a tar.gz archive of the primary data directory
        and saves it to external storage.
        
        Args:
            checkpoint_name: Name for this checkpoint
        
        Returns:
            Path to checkpoint file
        
        Example:
            >>> backup = BackupManager()
            >>> checkpoint_path = backup.create_checkpoint("after_phase1")
            Checkpoint created: after_phase1_20260216_143022.tar.gz
            Size: 125.3 MB
        """
        # Input validation
        if not isinstance(checkpoint_name, str) or not checkpoint_name.strip():
            raise ValueError(f"Invalid checkpoint_name: {checkpoint_name}")
        
        # Sanitize checkpoint name
        checkpoint_name = checkpoint_name.strip()
        if len(checkpoint_name) > self.MAX_CHECKPOINT_NAME_LENGTH:
            raise ValueError(f"checkpoint_name too long (max {self.MAX_CHECKPOINT_NAME_LENGTH} chars)")
        
        # Check for invalid characters that could cause issues
        invalid_chars = ['/', '\\', '..', '\0']
        if any(char in checkpoint_name for char in invalid_chars):
            raise ValueError(f"checkpoint_name contains invalid characters: {checkpoint_name}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = f"{checkpoint_name}_{timestamp}.tar.gz"
        
        self.logger.info(f"Creating checkpoint: {checkpoint_file}")
        
        # Create tar.gz in external backup
        tar_path = self.external_backup / checkpoint_file
        
        try:
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(self.primary, arcname="data_raw")
                tar.add(self.local_backup, arcname="data_backup")
            
            size_mb = tar_path.stat().st_size / 1024 / 1024
            
            self.logger.info(f"✅ Checkpoint created: {checkpoint_file}")
            self.logger.info(f"   Size: {size_mb:.1f} MB")
            self.logger.info(f"   Location: {tar_path}")
            
            return tar_path
        
        except Exception as e:
            self.logger.error(f"❌ Failed to create checkpoint: {e}")
            raise
    
    def restore_from_checkpoint(self, checkpoint_path: Path) -> None:
        """
        Restore data from a checkpoint archive.
        
        Args:
            checkpoint_path: Path to checkpoint tar.gz file
        
        Example:
            >>> backup = BackupManager()
            >>> backup.restore_from_checkpoint(Path("backup/checkpoint_20260216.tar.gz"))
        """
        # Input validation
        if not isinstance(checkpoint_path, (str, Path)):
            raise ValueError(f"checkpoint_path must be str or Path, got {type(checkpoint_path)}")
        
        checkpoint_path = Path(checkpoint_path)
        
        if not checkpoint_path.exists():
            raise ValueError(f"Checkpoint file does not exist: {checkpoint_path}")
        
        if not checkpoint_path.is_file():
            raise ValueError(f"Checkpoint path is not a file: {checkpoint_path}")
        
        if not checkpoint_path.suffix == '.gz':
            raise ValueError(f"Invalid checkpoint file format (must be .tar.gz): {checkpoint_path}")
        
        self.logger.info(f"Restoring from checkpoint: {checkpoint_path}")
        
        try:
            with tarfile.open(checkpoint_path, "r:gz") as tar:
                # Validate all members before extraction (security check)
                for member in tar.getmembers():
                    # Check for absolute paths
                    if member.name.startswith('/'):
                        raise ValueError(f"Unsafe tar member (absolute path): {member.name}")
                    
                    # Check for path traversal
                    if '..' in member.name:
                        raise ValueError(f"Unsafe tar member (path traversal): {member.name}")
                    
                    # Check for links (symlinks can be used for attacks)
                    if member.issym() or member.islnk():
                        raise ValueError(f"Unsafe tar member (link): {member.name}")
                
                # Extract to parent directory
                extract_path = self.primary.parent
                tar.extractall(extract_path)
            
            self.logger.info("✅ Checkpoint restored successfully")
        
        except Exception as e:
            self.logger.error(f"❌ Failed to restore checkpoint: {e}")
            raise
    
    def get_checkpoint_list(self) -> list[dict]:
        """
        Get list of available checkpoints.
        
        Returns:
            List of checkpoint metadata dictionaries
        
        Example:
            >>> backup = BackupManager()
            >>> checkpoints = backup.get_checkpoint_list()
            >>> for cp in checkpoints:
            ...     print(f"{cp['name']}: {cp['size_mb']:.1f} MB")
        """
        checkpoints = []
        
        for checkpoint_file in self.external_backup.glob("*.tar.gz"):
            stats = checkpoint_file.stat()
            checkpoints.append({
                "name": checkpoint_file.stem,
                "path": checkpoint_file,
                "size_mb": stats.st_size / 1024 / 1024,
                "created": datetime.fromtimestamp(stats.st_mtime),
            })
        
        # Sort by creation time (newest first)
        checkpoints.sort(key=lambda x: x["created"], reverse=True)
        
        return checkpoints
    
    def verify_backup_integrity(self, filepath: str) -> bool:
        """
        Verify that backup exists and matches primary file.
        
        Args:
            filepath: Relative path to verify
        
        Returns:
            True if backup is valid, False otherwise
        
        Example:
            >>> backup = BackupManager()
            >>> if backup.verify_backup_integrity("fixtures/2023/match_123.json"):
            ...     print("Backup is valid")
        """
        # Sanitize filepath
        try:
            sanitized_path = self._sanitize_filepath(filepath)
        except ValueError as e:
            self.logger.warning(f"Invalid filepath: {e}")
            return False
        
        primary_path = self.primary / sanitized_path
        backup_path = self.local_backup / sanitized_path
        
        # Check both files exist
        if not primary_path.exists():
            self.logger.warning(f"Primary file missing: {filepath}")
            return False
        
        if not backup_path.exists():
            self.logger.warning(f"Backup file missing: {filepath}")
            return False
        
        # Compare file sizes (quick check)
        try:
            primary_size = primary_path.stat().st_size
            backup_size = backup_path.stat().st_size
            
            if primary_size != backup_size:
                self.logger.warning(f"Size mismatch for {filepath}: "
                                  f"primary={primary_size}, backup={backup_size}")
                return False
        except (IOError, OSError) as e:
            self.logger.warning(f"Failed to check file sizes for {filepath}: {e}")
            return False
        
        return True
    
    def get_backup_stats(self) -> dict:
        """
        Get statistics about backup storage.
        
        Returns:
            Dictionary with backup statistics
        
        Example:
            >>> backup = BackupManager()
            >>> stats = backup.get_backup_stats()
            >>> print(f"Total backup size: {stats['total_size_mb']:.1f} MB")
        """
        def get_dir_size(path: Path) -> int:
            """Calculate total size of directory."""
            total = 0
            for f in path.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
            return total
        
        primary_size = get_dir_size(self.primary)
        backup_size = get_dir_size(self.local_backup)
        
        checkpoints = self.get_checkpoint_list()
        checkpoint_size = sum(cp["size_mb"] * 1024 * 1024 for cp in checkpoints)
        
        return {
            "primary_size_mb": primary_size / 1024 / 1024,
            "backup_size_mb": backup_size / 1024 / 1024,
            "checkpoint_size_mb": checkpoint_size / 1024 / 1024,
            "total_size_mb": (primary_size + backup_size + checkpoint_size) / 1024 / 1024,
            "num_checkpoints": len(checkpoints),
        }
