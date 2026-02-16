"""Collection manifest for tracking data collection progress.

This module provides a manifest system to track which data has been collected,
enabling resume capability and progress monitoring.

Key features:
- Track completion status for each fixture and include
- Resume interrupted collections
- Progress reporting
- Priority-based ordering
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..utils.logging_utils import get_logger


class CollectionManifest:
    """
    Track and manage data collection progress.
    
    Maintains a manifest of what data has been collected and what remains,
    enabling resume capability and progress reporting.
    
    Args:
        manifest_path: Path to manifest JSON file
        includes: List of data includes to track
    
    Example:
        >>> manifest = CollectionManifest()
        >>> manifest.register_fixture(18841624)
        >>> manifest.mark_complete(18841624, "ballCoordinates")
        >>> progress = manifest.get_progress_summary()
        >>> print(f"Progress: {progress['fixtures_pct']}")
    """
    
    # Default includes in priority order
    DEFAULT_INCLUDES = [
        "ballCoordinates",  # Highest priority - core tracking data
        "events",           # Event data with timestamps
        "lineups",          # Player lineups
        "formations",       # Formation data
        "statistics",       # Match statistics
        "participants",     # Team information
        "scores",           # Scoring information
    ]
    
    def __init__(
        self,
        manifest_path: str = "data/logs/collection_manifest.json",
        includes: Optional[list[str]] = None
    ):
        """Initialize collection manifest."""
        self.manifest_path = Path(manifest_path)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.includes = includes or self.DEFAULT_INCLUDES
        self.manifest = self.load_manifest()
        self.logger = get_logger(self.__class__.__name__)
    
    def load_manifest(self) -> dict:
        """
        Load existing manifest or create new one.
        
        Returns:
            Manifest dictionary
        """
        if self.manifest_path.exists():
            with open(self.manifest_path) as f:
                manifest = json.load(f)
                # Validate structure
                if "fixtures" not in manifest:
                    manifest["fixtures"] = {}
                return manifest
        
        # Create new manifest
        return {
            "created_at": datetime.now().isoformat(),
            "last_updated": None,
            "fixtures": {},
            "includes": self.includes,
            "priority_order": self.includes.copy(),
        }
    
    def save_manifest(self) -> None:
        """Save manifest to disk."""
        self.manifest["last_updated"] = datetime.now().isoformat()
        
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)
        
        self.logger.debug(f"Manifest saved to {self.manifest_path}")
    
    def register_fixture(self, fixture_id: int) -> None:
        """
        Register a fixture for tracking.
        
        Args:
            fixture_id: Fixture ID to register
        
        Example:
            >>> manifest = CollectionManifest()
            >>> manifest.register_fixture(18841624)
        """
        fixture_id_str = str(fixture_id)
        
        if fixture_id_str not in self.manifest["fixtures"]:
            self.manifest["fixtures"][fixture_id_str] = {
                "status": "pending",
                "includes_completed": [],
                "includes_remaining": self.includes.copy(),
                "started_at": None,
                "completed_at": None,
                "errors": [],
            }
            self.save_manifest()
            self.logger.debug(f"Registered fixture: {fixture_id}")
    
    def mark_complete(self, fixture_id: int, include_name: str) -> None:
        """
        Mark an include as successfully collected for a fixture.
        
        Args:
            fixture_id: Fixture ID
            include_name: Name of the include (e.g., "ballCoordinates")
        
        Example:
            >>> manifest = CollectionManifest()
            >>> manifest.mark_complete(18841624, "ballCoordinates")
            >>> manifest.mark_complete(18841624, "events")
        """
        fixture_id_str = str(fixture_id)
        
        # Register if not exists
        if fixture_id_str not in self.manifest["fixtures"]:
            self.register_fixture(fixture_id)
        
        fixture = self.manifest["fixtures"][fixture_id_str]
        
        # Update started_at on first include
        if fixture["status"] == "pending":
            fixture["status"] = "in_progress"
            fixture["started_at"] = datetime.now().isoformat()
        
        # Mark include complete
        if include_name not in fixture["includes_completed"]:
            fixture["includes_completed"].append(include_name)
            self.logger.debug(f"Marked complete: {fixture_id} - {include_name}")
        
        if include_name in fixture["includes_remaining"]:
            fixture["includes_remaining"].remove(include_name)
        
        # Check if fixture fully complete
        if not fixture["includes_remaining"]:
            fixture["status"] = "complete"
            fixture["completed_at"] = datetime.now().isoformat()
            self.logger.info(f"✅ Fixture {fixture_id} fully collected")
        
        self.save_manifest()
    
    def mark_error(self, fixture_id: int, include_name: str, error_msg: str) -> None:
        """
        Record an error for a fixture/include.
        
        Args:
            fixture_id: Fixture ID
            include_name: Name of the include
            error_msg: Error message
        
        Example:
            >>> manifest = CollectionManifest()
            >>> manifest.mark_error(18841624, "ballCoordinates", "API timeout")
        """
        fixture_id_str = str(fixture_id)
        
        if fixture_id_str not in self.manifest["fixtures"]:
            self.register_fixture(fixture_id)
        
        fixture = self.manifest["fixtures"][fixture_id_str]
        
        error_entry = {
            "include": include_name,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
        }
        
        fixture["errors"].append(error_entry)
        self.save_manifest()
        
        self.logger.warning(f"Error recorded: {fixture_id} - {include_name}: {error_msg}")
    
    def get_pending_work(self) -> list[tuple[int, str]]:
        """
        Get list of (fixture_id, include) tuples that need collection.
        
        Returns work prioritized by include type (all ballCoordinates first,
        then all events, etc.)
        
        Returns:
            List of (fixture_id, include_name) tuples
        
        Example:
            >>> manifest = CollectionManifest()
            >>> pending = manifest.get_pending_work()
            >>> for fixture_id, include in pending[:5]:
            ...     print(f"Need to collect: {fixture_id} - {include}")
        """
        pending = []
        
        # Group by include type (collect all of one type before moving to next)
        for include in self.manifest["priority_order"]:
            for fixture_id_str, fixture_data in self.manifest["fixtures"].items():
                if include in fixture_data["includes_remaining"]:
                    fixture_id = int(fixture_id_str)
                    pending.append((fixture_id, include))
        
        return pending
    
    def get_progress_summary(self) -> dict:
        """
        Get human-readable progress summary.
        
        Returns:
            Dictionary with progress metrics
        
        Example:
            >>> manifest = CollectionManifest()
            >>> summary = manifest.get_progress_summary()
            >>> print(f"Fixtures: {summary['fixtures_complete']}")
            >>> print(f"Includes: {summary['includes_complete']}")
            >>> print(f"Estimated time: {summary['estimated_time_remaining']}")
        """
        fixtures = self.manifest["fixtures"]
        
        if not fixtures:
            return {
                "fixtures_complete": "0/0",
                "fixtures_pct": "0.0%",
                "includes_complete": "0/0",
                "includes_pct": "0.0%",
                "estimated_time_remaining": "N/A",
            }
        
        total_fixtures = len(fixtures)
        complete_fixtures = sum(
            1 for f in fixtures.values() if f["status"] == "complete"
        )
        
        total_includes = total_fixtures * len(self.includes)
        complete_includes = sum(
            len(f["includes_completed"]) for f in fixtures.values()
        )
        
        # Calculate percentage
        fixtures_pct = (complete_fixtures / total_fixtures * 100) if total_fixtures > 0 else 0
        includes_pct = (complete_includes / total_includes * 100) if total_includes > 0 else 0
        
        # Estimate time remaining (assuming 6 seconds per API call)
        remaining_includes = total_includes - complete_includes
        estimated_seconds = remaining_includes * 6
        estimated_minutes = estimated_seconds / 60
        
        if estimated_minutes < 60:
            time_str = f"{estimated_minutes:.0f} minutes"
        else:
            time_str = f"{estimated_minutes/60:.1f} hours"
        
        return {
            "fixtures_complete": f"{complete_fixtures}/{total_fixtures}",
            "fixtures_pct": f"{fixtures_pct:.1f}%",
            "includes_complete": f"{complete_includes}/{total_includes}",
            "includes_pct": f"{includes_pct:.1f}%",
            "estimated_time_remaining": time_str if remaining_includes > 0 else "Complete",
        }
    
    def get_fixture_status(self, fixture_id: int) -> Optional[dict]:
        """
        Get status for a specific fixture.
        
        Args:
            fixture_id: Fixture ID
        
        Returns:
            Fixture status dictionary or None if not found
        
        Example:
            >>> manifest = CollectionManifest()
            >>> status = manifest.get_fixture_status(18841624)
            >>> print(f"Status: {status['status']}")
            >>> print(f"Completed: {status['includes_completed']}")
        """
        fixture_id_str = str(fixture_id)
        return self.manifest["fixtures"].get(fixture_id_str)
    
    def get_fixtures_by_status(self, status: str) -> list[int]:
        """
        Get list of fixture IDs by status.
        
        Args:
            status: Status to filter by ("pending", "in_progress", "complete")
        
        Returns:
            List of fixture IDs
        
        Example:
            >>> manifest = CollectionManifest()
            >>> complete = manifest.get_fixtures_by_status("complete")
            >>> print(f"Complete fixtures: {len(complete)}")
        """
        return [
            int(fixture_id)
            for fixture_id, data in self.manifest["fixtures"].items()
            if data["status"] == status
        ]
    
    def reset(self) -> None:
        """
        Reset manifest (clear all progress).
        
        Use with caution - this will clear all tracked progress!
        
        Example:
            >>> manifest = CollectionManifest()
            >>> manifest.reset()
        """
        self.manifest = {
            "created_at": datetime.now().isoformat(),
            "last_updated": None,
            "fixtures": {},
            "includes": self.includes,
            "priority_order": self.includes.copy(),
        }
        self.save_manifest()
        self.logger.warning("Manifest reset - all progress cleared")
