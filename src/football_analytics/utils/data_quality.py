"""Data quality validation framework.

This module provides comprehensive data quality checks for collected
football match data, including:
- Completeness validation
- Data integrity checks
- Statistical validation
- Quality scoring

Key features:
- Multi-level validation (file, data, content)
- Quality metrics and scoring
- Automated reporting
- Threshold-based pass/fail
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from ..utils.file_io import load_json as load_json_file
from ..utils.logging_utils import get_logger


class DataQualityValidator:
    """
    Validate quality of collected match data.
    
    Performs comprehensive quality checks on raw data to ensure
    completeness and integrity for analysis.
    
    Args:
        data_dir: Base directory containing raw data
        min_ball_coordinates: Minimum ball coordinates per match
        min_events: Minimum events per match
        min_lineups: Minimum lineup entries per match
    
    Example:
        >>> validator = DataQualityValidator()
        >>> quality_report = validator.validate_fixture(18841624)
        >>> print(f"Quality score: {quality_report['quality_score']}/100")
        >>> print(f"Status: {quality_report['status']}")
    """
    
    # Quality thresholds
    MIN_BALL_COORDINATES = 500  # Minimum coordinates per match
    MIN_EVENTS = 50  # Minimum events per match
    MIN_LINEUPS = 20  # Minimum lineup entries (2 teams * 11 players)
    EVENT_LINK_SUCCESS_THRESHOLD = 80.0  # Percentage
    
    def __init__(
        self,
        data_dir: str = "data/raw",
        min_ball_coordinates: int = MIN_BALL_COORDINATES,
        min_events: int = MIN_EVENTS,
        min_lineups: int = MIN_LINEUPS
    ):
        """Initialize data quality validator."""
        self.data_dir = Path(data_dir)
        self.min_ball_coordinates = min_ball_coordinates
        self.min_events = min_events
        self.min_lineups = min_lineups
        self.logger = get_logger(self.__class__.__name__)
    
    def validate_fixture(self, fixture_id: int) -> dict:
        """
        Validate all data for a single fixture.
        
        Args:
            fixture_id: Fixture ID to validate
        
        Returns:
            Dictionary with validation results and quality score
        
        Example:
            >>> validator = DataQualityValidator()
            >>> report = validator.validate_fixture(18841624)
            >>> if report['status'] == 'PASS':
            ...     print("✅ Data quality is good")
            >>> else:
            ...     print(f"⚠️  Issues: {report['issues']}")
        """
        fixture_dir = self.data_dir / str(fixture_id)
        
        # Initialize report
        report = {
            "fixture_id": fixture_id,
            "status": "UNKNOWN",
            "quality_score": 0,
            "checks": {},
            "issues": [],
            "warnings": [],
        }
        
        # Check 1: File existence
        file_check = self._check_files_exist(fixture_dir)
        report["checks"]["files"] = file_check
        
        if not file_check["passed"]:
            report["status"] = "FAIL"
            report["issues"].extend(file_check["issues"])
            return report
        
        # Check 2: Ball coordinates quality
        coords_check = self._check_ball_coordinates(fixture_dir)
        report["checks"]["ball_coordinates"] = coords_check
        
        if not coords_check["passed"]:
            report["issues"].extend(coords_check["issues"])
        if coords_check.get("warnings"):
            report["warnings"].extend(coords_check["warnings"])
        
        # Check 3: Events quality
        events_check = self._check_events(fixture_dir)
        report["checks"]["events"] = events_check
        
        if not events_check["passed"]:
            report["issues"].extend(events_check["issues"])
        
        # Check 4: Lineups quality
        lineups_check = self._check_lineups(fixture_dir)
        report["checks"]["lineups"] = lineups_check
        
        if not lineups_check["passed"]:
            report["issues"].extend(lineups_check["issues"])
        
        # Calculate quality score (0-100)
        report["quality_score"] = self._calculate_quality_score(report["checks"])
        
        # Determine overall status
        if len(report["issues"]) == 0:
            report["status"] = "PASS"
        elif report["quality_score"] >= 70:
            report["status"] = "PASS_WITH_WARNINGS"
        else:
            report["status"] = "FAIL"
        
        self.logger.info(f"Fixture {fixture_id}: {report['status']} "
                        f"(Score: {report['quality_score']}/100)")
        
        return report
    
    def _check_files_exist(self, fixture_dir: Path) -> dict:
        """
        Check that all required files exist.
        
        Args:
            fixture_dir: Fixture directory path
        
        Returns:
            Check result dictionary
        """
        required_files = [
            "ballCoordinates.json",
            "events.json",
            "lineups.json",
            "formations.json",
            "statistics.json",
            "participants.json",
            "scores.json",
        ]
        
        missing_files = []
        existing_files = []
        
        for filename in required_files:
            filepath = fixture_dir / filename
            if filepath.exists():
                existing_files.append(filename)
            else:
                missing_files.append(filename)
        
        passed = len(missing_files) == 0
        
        result = {
            "passed": passed,
            "existing_files": existing_files,
            "missing_files": missing_files,
            "issues": [],
        }
        
        if not passed:
            result["issues"].append(f"Missing files: {', '.join(missing_files)}")
        
        return result
    
    def _check_ball_coordinates(self, fixture_dir: Path) -> dict:
        """
        Check ball coordinates data quality.
        
        Args:
            fixture_dir: Fixture directory path
        
        Returns:
            Check result dictionary
        """
        coords_file = fixture_dir / "ballCoordinates.json"
        
        try:
            coords_data = load_json_file(coords_file)
            
            # Extract coordinates
            if "data" in coords_data:
                coords_list = coords_data["data"]
            else:
                coords_list = coords_data
            
            count = len(coords_list)
            
            # Check minimum threshold
            passed = count >= self.min_ball_coordinates
            
            # Check for valid coordinates
            valid_coords = 0
            for coord in coords_list[:100]:  # Sample first 100
                try:
                    x = float(coord.get("x", 0))
                    y = float(coord.get("y", 0))
                    if 0 <= x <= 1.1 and -0.1 <= y <= 1.1:
                        valid_coords += 1
                except (ValueError, TypeError):
                    pass
            
            valid_pct = valid_coords / min(100, count) * 100 if count > 0 else 0
            
            result = {
                "passed": passed,
                "count": count,
                "valid_percentage": valid_pct,
                "issues": [],
                "warnings": [],
            }
            
            if not passed:
                result["issues"].append(
                    f"Ball coordinates below threshold: {count} < {self.min_ball_coordinates}"
                )
            
            if valid_pct < 95:
                result["warnings"].append(
                    f"Some invalid coordinates detected: {valid_pct:.1f}% valid"
                )
            
            return result
        
        except Exception as e:
            return {
                "passed": False,
                "count": 0,
                "issues": [f"Failed to read ball coordinates: {e}"],
                "warnings": [],
            }
    
    def _check_events(self, fixture_dir: Path) -> dict:
        """
        Check events data quality.
        
        Args:
            fixture_dir: Fixture directory path
        
        Returns:
            Check result dictionary
        """
        events_file = fixture_dir / "events.json"
        
        try:
            events_data = load_json_file(events_file)
            
            # Extract events
            if "data" in events_data:
                events_list = events_data["data"]
            else:
                events_list = events_data
            
            count = len(events_list)
            
            # Check minimum threshold
            passed = count >= self.min_events
            
            # Check for essential fields
            has_minute = 0
            has_type = 0
            has_player = 0
            
            for event in events_list[:50]:  # Sample first 50
                if event.get("minute") is not None:
                    has_minute += 1
                if event.get("type"):
                    has_type += 1
                if event.get("player"):
                    has_player += 1
            
            sample_size = min(50, count)
            
            result = {
                "passed": passed,
                "count": count,
                "has_minute_pct": has_minute / sample_size * 100 if sample_size > 0 else 0,
                "has_type_pct": has_type / sample_size * 100 if sample_size > 0 else 0,
                "has_player_pct": has_player / sample_size * 100 if sample_size > 0 else 0,
                "issues": [],
            }
            
            if not passed:
                result["issues"].append(
                    f"Events below threshold: {count} < {self.min_events}"
                )
            
            return result
        
        except Exception as e:
            return {
                "passed": False,
                "count": 0,
                "issues": [f"Failed to read events: {e}"],
            }
    
    def _check_lineups(self, fixture_dir: Path) -> dict:
        """
        Check lineups data quality.
        
        Args:
            fixture_dir: Fixture directory path
        
        Returns:
            Check result dictionary
        """
        lineups_file = fixture_dir / "lineups.json"
        
        try:
            lineups_data = load_json_file(lineups_file)
            
            # Extract lineups
            if "data" in lineups_data:
                lineups_list = lineups_data["data"]
            else:
                lineups_list = lineups_data
            
            count = len(lineups_list)
            
            # Check minimum threshold
            passed = count >= self.min_lineups
            
            # Count starting players
            starting_count = sum(1 for lineup in lineups_list if lineup.get("starting", False))
            
            result = {
                "passed": passed,
                "count": count,
                "starting_count": starting_count,
                "issues": [],
            }
            
            if not passed:
                result["issues"].append(
                    f"Lineups below threshold: {count} < {self.min_lineups}"
                )
            
            # Expect ~22 starting players (11 per team)
            if starting_count < 20:
                result["issues"].append(
                    f"Insufficient starting players: {starting_count} < 20"
                )
            
            return result
        
        except Exception as e:
            return {
                "passed": False,
                "count": 0,
                "issues": [f"Failed to read lineups: {e}"],
            }
    
    def _calculate_quality_score(self, checks: dict) -> int:
        """
        Calculate overall quality score (0-100).
        
        Args:
            checks: Dictionary of check results
        
        Returns:
            Quality score (0-100)
        """
        scores = []
        
        # Files check (20 points)
        if checks.get("files", {}).get("passed"):
            files_score = 20
        else:
            missing = len(checks.get("files", {}).get("missing_files", []))
            files_score = max(0, 20 - missing * 3)
        scores.append(files_score)
        
        # Ball coordinates check (30 points)
        coords_check = checks.get("ball_coordinates", {})
        if coords_check.get("passed"):
            coords_score = 30
        else:
            count = coords_check.get("count", 0)
            coords_score = min(30, count / self.min_ball_coordinates * 30)
        scores.append(coords_score)
        
        # Events check (30 points)
        events_check = checks.get("events", {})
        if events_check.get("passed"):
            events_score = 30
        else:
            count = events_check.get("count", 0)
            events_score = min(30, count / self.min_events * 30)
        scores.append(events_score)
        
        # Lineups check (20 points)
        lineups_check = checks.get("lineups", {})
        if lineups_check.get("passed"):
            lineups_score = 20
        else:
            count = lineups_check.get("count", 0)
            lineups_score = min(20, count / self.min_lineups * 20)
        scores.append(lineups_score)
        
        total_score = int(sum(scores))
        
        return total_score
    
    def validate_multiple_fixtures(
        self,
        fixture_ids: list[int]
    ) -> pd.DataFrame:
        """
        Validate multiple fixtures and return summary report.
        
        Args:
            fixture_ids: List of fixture IDs to validate
        
        Returns:
            DataFrame with validation results
        
        Example:
            >>> validator = DataQualityValidator()
            >>> results = validator.validate_multiple_fixtures([18841624, 18841629, ...])
            >>> print(results[results['status'] != 'PASS'])
        """
        results = []
        
        self.logger.info(f"Validating {len(fixture_ids)} fixtures...")
        
        for fixture_id in fixture_ids:
            report = self.validate_fixture(fixture_id)
            
            results.append({
                "fixture_id": fixture_id,
                "status": report["status"],
                "quality_score": report["quality_score"],
                "num_issues": len(report["issues"]),
                "num_warnings": len(report["warnings"]),
                "ball_coords_count": report["checks"].get("ball_coordinates", {}).get("count", 0),
                "events_count": report["checks"].get("events", {}).get("count", 0),
                "lineups_count": report["checks"].get("lineups", {}).get("count", 0),
            })
        
        results_df = pd.DataFrame(results)
        
        # Summary statistics
        total = len(results_df)
        passed = (results_df["status"] == "PASS").sum()
        passed_with_warnings = (results_df["status"] == "PASS_WITH_WARNINGS").sum()
        failed = (results_df["status"] == "FAIL").sum()
        
        self.logger.info("=" * 60)
        self.logger.info("VALIDATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total fixtures: {total}")
        self.logger.info(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
        self.logger.info(f"⚠️  Passed with warnings: {passed_with_warnings} ({passed_with_warnings/total*100:.1f}%)")
        self.logger.info(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
        self.logger.info(f"Average quality score: {results_df['quality_score'].mean():.1f}/100")
        self.logger.info("=" * 60)
        
        return results_df
    
    def save_validation_report(
        self,
        results_df: pd.DataFrame,
        output_path: str = "data/processed/metadata/data_quality_report.csv"
    ) -> Path:
        """
        Save validation report to CSV.
        
        Args:
            results_df: Validation results DataFrame
            output_path: Output file path
        
        Returns:
            Path to saved file
        
        Example:
            >>> validator = DataQualityValidator()
            >>> output_path = validator.save_validation_report(results_df)
            >>> print(f"Report saved to: {output_path}")
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        results_df.to_csv(output_file, index=False)
        
        self.logger.info(f"✅ Validation report saved to: {output_file}")
        
        return output_file
