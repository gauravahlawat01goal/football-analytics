"""Ball coordinate processing and possession inference.

This module processes raw ball coordinate data from the API, handling:
- Coordinate parsing and normalization
- Timestamp synchronization with events
- Possession inference
- Pitch zone categorization
- Validation against official statistics

Key challenges solved:
1. Ball coordinates lack accurate timestamps -> Use sequence + event sync
2. No possession data -> Infer from events with confidence levels
3. Coordinate normalization -> Convert to standard pitch zones
"""

import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ..utils.file_io import load_json as load_json_file
from ..utils.logging_utils import get_logger


class BallCoordinateProcessor:
    """
    Process and enrich ball coordinate data.
    
    Handles parsing, timestamp synchronization, possession inference,
    and zone categorization for ball tracking data.
    
    Args:
        data_dir: Base directory containing raw data
    
    Example:
        >>> processor = BallCoordinateProcessor()
        >>> df = processor.parse_coordinates(18841624)
        >>> df = processor.infer_possession(df, events_df)
        >>> print(f"Possession inference: {df['possession_team'].notna().sum()} / {len(df)}")
    """
    
    # Pitch zones (normalized coordinates)
    DEFENSIVE_THIRD_X = 0.34
    ATTACKING_THIRD_X = 0.67
    LEFT_WING_Y = 0.25
    RIGHT_WING_Y = 0.75
    
    def __init__(self, data_dir: str = "data/raw"):
        """Initialize ball coordinate processor."""
        self.data_dir = Path(data_dir)
        self.logger = get_logger(self.__class__.__name__)
    
    def parse_coordinates(self, fixture_id: int, season: Optional[str] = None) -> pd.DataFrame:
        """
        Parse ball coordinates from JSON to DataFrame with derived fields.
        
        Args:
            fixture_id: Fixture ID to process
            season: Optional season identifier (e.g., "2023-24")
        
        Returns:
            DataFrame with parsed coordinates and derived fields
        
        Example:
            >>> processor = BallCoordinateProcessor()
            >>> df = processor.parse_coordinates(18841624)
            >>> print(df.columns)
            ['x', 'y', 'fixture_id', 'sequence', 'pitch_zone', 'width_zone', ...]
        """
        # Load raw JSON
        fixture_dir = self.data_dir / str(fixture_id)
        coords_file = fixture_dir / "ballCoordinates.json"
        
        if not coords_file.exists():
            self.logger.error(f"Ball coordinates not found for fixture {fixture_id}")
            return pd.DataFrame()
        
        coords_data = load_json_file(coords_file)
        
        # Extract coordinates from API response
        if "data" in coords_data:
            coords_list = coords_data["data"]
        else:
            coords_list = coords_data
        
        if not coords_list:
            self.logger.warning(f"No ball coordinates in file for fixture {fixture_id}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(coords_list)
        
        # Convert data types
        df["x"] = pd.to_numeric(df["x"], errors="coerce")
        df["y"] = pd.to_numeric(df["y"], errors="coerce")
        df["fixture_id"] = fixture_id
        
        # Add sequence number if not present
        if "sequence" not in df.columns:
            df["sequence"] = range(len(df))
        
        # Parse timer if available (e.g., "45:32" -> minute=45, second=32)
        if "timer" in df.columns:
            df = self._parse_timer(df)
        
        # Derive pitch zones
        df["pitch_zone"] = df["x"].apply(self.categorize_pitch_zone)
        df["width_zone"] = df["y"].apply(self.categorize_width_zone)
        df["distance_to_goal"] = df.apply(self.calculate_distance_to_goal, axis=1)
        
        self.logger.info(f"Parsed {len(df)} ball coordinates for fixture {fixture_id}")
        
        return df
    
    def _parse_timer(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse timer field into minute and second columns.
        
        Args:
            df: DataFrame with timer column
        
        Returns:
            DataFrame with minute and second columns added
        """
        def parse_time(timer_str):
            """Parse '45:32' -> (45, 32)"""
            if pd.isna(timer_str) or not isinstance(timer_str, str):
                return pd.Series([None, None])
            
            try:
                parts = timer_str.split(":")
                if len(parts) == 2:
                    return pd.Series([int(parts[0]), int(parts[1])])
            except (ValueError, AttributeError):
                pass
            
            return pd.Series([None, None])
        
        df[["minute", "second"]] = df["timer"].apply(parse_time)
        
        return df
    
    def categorize_pitch_zone(self, x: float) -> str:
        """
        Categorize X coordinate into pitch thirds.
        
        Args:
            x: Normalized X coordinate (0.0 - 1.0)
        
        Returns:
            Zone name: "defensive_third", "middle_third", "attacking_third"
        
        Example:
            >>> processor = BallCoordinateProcessor()
            >>> zone = processor.categorize_pitch_zone(0.2)
            >>> print(zone)  # "defensive_third"
        """
        if pd.isna(x):
            return "unknown"
        
        if x < self.DEFENSIVE_THIRD_X:
            return "defensive_third"
        elif x < self.ATTACKING_THIRD_X:
            return "middle_third"
        else:
            return "attacking_third"
    
    def categorize_width_zone(self, y: float) -> str:
        """
        Categorize Y coordinate into width zones.
        
        Args:
            y: Normalized Y coordinate (0.0 - 1.0)
        
        Returns:
            Zone name: "left_wing", "center", "right_wing"
        
        Example:
            >>> processor = BallCoordinateProcessor()
            >>> zone = processor.categorize_width_zone(0.15)
            >>> print(zone)  # "left_wing"
        """
        if pd.isna(y):
            return "unknown"
        
        if y < self.LEFT_WING_Y:
            return "left_wing"
        elif y < self.RIGHT_WING_Y:
            return "center"
        else:
            return "right_wing"
    
    def calculate_distance_to_goal(self, row: pd.Series) -> float:
        """
        Calculate distance from ball to attacking goal.
        
        Args:
            row: DataFrame row with x and y coordinates
        
        Returns:
            Distance to goal (normalized 0-1)
        
        Example:
            >>> processor = BallCoordinateProcessor()
            >>> distance = processor.calculate_distance_to_goal(pd.Series({"x": 0.8, "y": 0.5}))
        """
        x, y = row["x"], row["y"]
        
        if pd.isna(x) or pd.isna(y):
            return np.nan
        
        # Goal is at x=1.0, y=0.5 (center)
        goal_x, goal_y = 1.0, 0.5
        
        distance = np.sqrt((x - goal_x)**2 + (y - goal_y)**2)
        
        return distance
    
    def solve_timestamp_problem(
        self,
        coords_df: pd.DataFrame,
        events_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Solve timestamp synchronization between coordinates and events.
        
        Problem: Ball coordinates may lack accurate timestamps
        Solution: Use sequence numbers + event timestamps to infer time
        
        Args:
            coords_df: Ball coordinates DataFrame
            events_df: Events DataFrame with minute field
        
        Returns:
            Coordinates DataFrame with estimated_minute field
        
        Example:
            >>> processor = BallCoordinateProcessor()
            >>> coords_df = processor.solve_timestamp_problem(coords_df, events_df)
            >>> print(coords_df["estimated_minute"].describe())
        """
        # Strategy 1: If period_id and minute available, use directly
        if "minute" in coords_df.columns and coords_df["minute"].notna().sum() > len(coords_df) * 0.8:
            self.logger.info("Using timer field for timestamps")
            coords_df["estimated_minute"] = coords_df["minute"] + coords_df.get("second", 0) / 60
            return coords_df
        
        # Strategy 2: If period_id available, sync by period
        if "period_id" in coords_df.columns and "period_id" in events_df.columns:
            self.logger.info("Using period-based synchronization")
            return self._sync_by_period(coords_df, events_df)
        
        # Strategy 3: Use sequence numbers + match duration
        self.logger.info("Using sequence-based time estimation")
        return self._estimate_time_from_sequence(coords_df)
    
    def _sync_by_period(
        self,
        coords_df: pd.DataFrame,
        events_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Synchronize coordinates with events using period information.
        
        Args:
            coords_df: Coordinates with period_id
            events_df: Events with period_id and minute
        
        Returns:
            Coordinates with estimated_minute
        """
        coords_df["estimated_minute"] = np.nan
        
        for period_id in coords_df["period_id"].unique():
            if pd.isna(period_id):
                continue
            
            period_coords = coords_df["period_id"] == period_id
            period_events = events_df[events_df["period_id"] == period_id]
            
            if len(period_events) == 0:
                continue
            
            # Get time range from events
            min_minute = period_events["minute"].min()
            max_minute = period_events["minute"].max()
            duration = max_minute - min_minute
            
            if duration <= 0:
                duration = 45  # Default period duration
            
            # Map sequence within period to time
            period_mask = coords_df["period_id"] == period_id
            period_sequences = coords_df.loc[period_mask, "sequence"]
            
            if len(period_sequences) > 0:
                # Normalize sequences within period
                period_seq_min = period_sequences.min()
                period_seq_max = period_sequences.max()
                period_seq_range = period_seq_max - period_seq_min
                
                if period_seq_range > 0:
                    normalized_seq = (period_sequences - period_seq_min) / period_seq_range
                    estimated_time = min_minute + (normalized_seq * duration)
                    coords_df.loc[period_mask, "estimated_minute"] = estimated_time
        
        return coords_df
    
    def _estimate_time_from_sequence(self, coords_df: pd.DataFrame) -> pd.DataFrame:
        """
        Estimate timestamps from sequence numbers assuming 90-minute match.
        
        Args:
            coords_df: Coordinates with sequence numbers
        
        Returns:
            Coordinates with estimated_minute
        """
        total_coords = len(coords_df)
        
        # Assume 90 minutes base + some stoppage time
        # Typical: 6-8 coordinates per minute
        assumed_duration = 95  # minutes (90 + ~5 stoppage)
        
        coords_df["estimated_minute"] = (
            coords_df["sequence"] / total_coords * assumed_duration
        )
        
        return coords_df
    
    def link_event_to_coordinate(
        self,
        event: pd.Series,
        coords_df: pd.DataFrame,
        tolerance_seconds: float = 5.0
    ) -> Optional[pd.Series]:
        """
        Find closest ball coordinate to an event.
        
        Args:
            event: Event series with minute field
            coords_df: Coordinates with estimated_minute
            tolerance_seconds: Maximum time difference to accept (seconds)
        
        Returns:
            Coordinate row or None if not found
        
        Example:
            >>> processor = BallCoordinateProcessor()
            >>> event = events_df.iloc[0]
            >>> coord = processor.link_event_to_coordinate(event, coords_df)
            >>> if coord is not None:
            ...     print(f"Ball at ({coord['x']:.2f}, {coord['y']:.2f})")
        """
        event_minute = event.get("minute")
        
        if pd.isna(event_minute) or "estimated_minute" not in coords_df.columns:
            return None
        
        tolerance_minutes = tolerance_seconds / 60
        
        # Find coordinates within tolerance
        time_diff = abs(coords_df["estimated_minute"] - event_minute)
        within_tolerance = coords_df[time_diff <= tolerance_minutes]
        
        if len(within_tolerance) == 0:
            return None
        
        # Return closest one
        closest_idx = time_diff[within_tolerance.index].idxmin()
        closest = coords_df.loc[closest_idx]
        
        return closest
    
    def infer_possession(
        self,
        coords_df: pd.DataFrame,
        events_df: pd.DataFrame,
        liverpool_team_id: int = 8
    ) -> pd.DataFrame:
        """
        Infer which team has possession at each coordinate.
        
        Strategy: Use events as possession markers, interpolate between events
        
        Args:
            coords_df: Ball coordinates with estimated_minute
            events_df: Events with team_id and minute
            liverpool_team_id: Liverpool's team ID
        
        Returns:
            Coordinates with possession_team and possession_confidence columns
        
        Example:
            >>> processor = BallCoordinateProcessor()
            >>> coords_df = processor.infer_possession(coords_df, events_df)
            >>> possession_rate = (coords_df["possession_team"] == 8).sum() / len(coords_df)
            >>> print(f"Liverpool possession: {possession_rate*100:.1f}%")
        """
        # Initialize possession columns
        coords_df["possession_team"] = None
        coords_df["possession_confidence"] = None
        
        # Possession-indicating events
        possession_events = [
            "pass", "shot", "cross", "dribble", "touch",
            "goal_kick", "throw_in", "corner", "free_kick"
        ]
        
        # Filter for possession events
        if "type_name" in events_df.columns:
            type_col = "type_name"
        elif "event_type" in events_df.columns:
            type_col = "event_type"
        else:
            self.logger.warning("No event type column found - cannot infer possession")
            return coords_df
        
        poss_events = events_df[
            events_df[type_col].str.lower().str.contains("|".join(possession_events), na=False)
        ].copy()
        
        poss_events = poss_events.sort_values("minute")
        
        # For each coordinate, find nearest possession event
        for idx, coord in coords_df.iterrows():
            if "estimated_minute" not in coord or pd.isna(coord["estimated_minute"]):
                continue
            
            coord_time = coord["estimated_minute"]
            
            # Find events before and after
            events_before = poss_events[poss_events["minute"] <= coord_time]
            events_after = poss_events[poss_events["minute"] > coord_time]
            
            if len(events_before) > 0:
                last_event = events_before.iloc[-1]
                time_since_event = coord_time - last_event["minute"]
                
                # Assign possession based on time proximity
                if time_since_event < 0.17:  # 10 seconds
                    coords_df.at[idx, "possession_team"] = last_event.get("team_id")
                    coords_df.at[idx, "possession_confidence"] = "high"
                elif time_since_event < 0.33:  # 20 seconds
                    coords_df.at[idx, "possession_team"] = last_event.get("team_id")
                    coords_df.at[idx, "possession_confidence"] = "medium"
                else:
                    # Check if next event is from different team (indicates turnover)
                    if len(events_after) > 0:
                        next_event = events_after.iloc[0]
                        time_to_next = next_event["minute"] - coord_time
                        
                        if time_to_next < 0.33 and next_event.get("team_id") != last_event.get("team_id"):
                            # Likely turnover period - assign to next team
                            coords_df.at[idx, "possession_team"] = next_event.get("team_id")
                            coords_df.at[idx, "possession_confidence"] = "low"
                        else:
                            # Use last known possession
                            coords_df.at[idx, "possession_team"] = last_event.get("team_id")
                            coords_df.at[idx, "possession_confidence"] = "low"
        
        # Count possession inference success
        inferred_count = coords_df["possession_team"].notna().sum()
        inferred_pct = inferred_count / len(coords_df) * 100
        
        self.logger.info(f"Possession inferred for {inferred_count}/{len(coords_df)} coordinates ({inferred_pct:.1f}%)")
        
        return coords_df
    
    def validate_possession_inference(
        self,
        coords_df: pd.DataFrame,
        official_possession: Optional[float],
        liverpool_team_id: int = 8
    ) -> dict:
        """
        Validate inferred possession against official statistics.
        
        Args:
            coords_df: Coordinates with possession_team
            official_possession: Official possession percentage (0-100)
            liverpool_team_id: Liverpool's team ID
        
        Returns:
            Validation results dictionary
        
        Example:
            >>> processor = BallCoordinateProcessor()
            >>> validation = processor.validate_possession_inference(coords_df, 62.5)
            >>> print(f"Validation: {validation['validation']}")
            >>> print(f"Difference: {validation['difference']:.1f}%")
        """
        # Calculate possession from coordinates
        total_coords = len(coords_df)
        liverpool_coords = (coords_df["possession_team"] == liverpool_team_id).sum()
        
        if total_coords == 0:
            return {"validation": "ERROR - No coordinates"}
        
        calculated_possession = liverpool_coords / total_coords * 100
        
        if official_possession is None:
            return {
                "calculated": calculated_possession,
                "official": None,
                "validation": "UNABLE - No official stats"
            }
        
        difference = abs(calculated_possession - official_possession)
        
        if difference < 5:
            validation = "PASSED - Within 5%"
        elif difference < 10:
            validation = "WARNING - Within 10%"
        else:
            validation = "FAILED - Difference >10%"
        
        return {
            "calculated": calculated_possession,
            "official": official_possession,
            "difference": difference,
            "validation": validation
        }
