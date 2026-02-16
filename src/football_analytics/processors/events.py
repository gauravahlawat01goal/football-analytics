"""Event data processing and analysis.

This module processes match event data, handling:
- Event parsing and categorization
- Linking events to ball coordinates
- Player action extraction
- Defensive and offensive event analysis

Key features:
- Structured event categorization
- Event-coordinate synchronization
- Player involvement tracking
- Team action analysis
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from ..utils.file_io import load_json as load_json_file
from ..utils.logging_utils import get_logger


class EventProcessor:
    """
    Parse and analyze match events.
    
    Handles event data extraction, categorization, and linking to
    ball coordinates for comprehensive match analysis.
    
    Args:
        data_dir: Base directory containing raw data
    
    Example:
        >>> processor = EventProcessor()
        >>> events_df = processor.parse_events(18841624)
        >>> events_df = processor.link_to_ball_coordinates(events_df, coords_df)
        >>> print(f"Linked {events_df['ball_x'].notna().sum()} events to coordinates")
    """
    
    # Event categories for tactical analysis
    DEFENSIVE_ACTIONS = ["tackle", "interception", "clearance", "block", "blocked"]
    PASSING_EVENTS = ["pass", "key_pass", "cross"]
    PROGRESSIVE_ACTIONS = ["carry", "progressive_pass", "through_ball", "dribble"]
    SET_PIECES = ["corner", "free_kick", "throw_in", "goal_kick"]
    GOAL_RELATED = ["goal", "assist", "shot", "shot_on_target", "penalty"]
    
    def __init__(self, data_dir: str = "data/raw"):
        """Initialize event processor."""
        self.data_dir = Path(data_dir)
        self.logger = get_logger(self.__class__.__name__)
    
    def parse_events(self, fixture_id: int, season: Optional[str] = None) -> pd.DataFrame:
        """
        Extract and categorize events from match data.
        
        Args:
            fixture_id: Fixture ID to process
            season: Optional season identifier
        
        Returns:
            DataFrame with parsed and categorized events
        
        Example:
            >>> processor = EventProcessor()
            >>> events = processor.parse_events(18841624)
            >>> print(events[['minute', 'event_type', 'player_name', 'team_name']].head())
        """
        # Load raw JSON
        fixture_dir = self.data_dir / str(fixture_id)
        events_file = fixture_dir / "events.json"
        
        if not events_file.exists():
            self.logger.error(f"Events file not found for fixture {fixture_id}")
            return pd.DataFrame()
        
        events_data = load_json_file(events_file)
        
        # Extract events from API response
        if "data" in events_data:
            events_list = events_data["data"]
        else:
            events_list = events_data
        
        if not events_list:
            self.logger.warning(f"No events in file for fixture {fixture_id}")
            return pd.DataFrame()
        
        # Parse each event
        parsed_events = []
        for event in events_list:
            parsed_event = self._parse_single_event(event, fixture_id)
            if parsed_event:
                parsed_events.append(parsed_event)
        
        # Convert to DataFrame
        df = pd.DataFrame(parsed_events)
        
        if len(df) > 0:
            # Add event categories
            df["event_category"] = df["event_type"].apply(self.categorize_event)
            
            # Sort by minute
            df = df.sort_values("minute").reset_index(drop=True)
            
            self.logger.info(f"Parsed {len(df)} events for fixture {fixture_id}")
        
        return df
    
    def _parse_single_event(self, event: dict, fixture_id: int) -> Optional[dict]:
        """
        Parse a single event dict into structured format.
        
        Args:
            event: Raw event dictionary
            fixture_id: Fixture ID
        
        Returns:
            Parsed event dictionary or None if invalid
        """
        try:
            # Extract event type (handle nested structure)
            event_type_data = event.get("type", {})
            if isinstance(event_type_data, dict):
                event_type = event_type_data.get("name", "Unknown")
                event_type_id = event_type_data.get("id")
            else:
                event_type = str(event_type_data) if event_type_data else "Unknown"
                event_type_id = None
            
            # Extract player info (handle nested structure)
            player_data = event.get("player", {})
            if isinstance(player_data, dict):
                player_id = player_data.get("id")
                player_name = player_data.get("display_name", "Unknown")
            else:
                player_id = None
                player_name = "Unknown"
            
            # Extract team info (handle nested structure)
            participant_data = event.get("participant", {})
            if isinstance(participant_data, dict):
                team_id = participant_data.get("id")
                team_name = participant_data.get("name", "Unknown")
            else:
                team_id = None
                team_name = "Unknown"
            
            # Build parsed event
            parsed_event = {
                "event_id": event.get("id"),
                "fixture_id": fixture_id,
                "minute": event.get("minute"),
                "extra_minute": event.get("extra_minute", 0),
                "period_id": event.get("period_id"),
                "event_type": event_type,
                "event_type_id": event_type_id,
                "player_id": player_id,
                "player_name": player_name,
                "team_id": team_id,
                "team_name": team_name,
                "result": event.get("result"),
                "info": event.get("info"),
                "sort_order": event.get("sort_order"),
            }
            
            return parsed_event
        
        except Exception as e:
            self.logger.warning(f"Failed to parse event: {e}")
            return None
    
    def categorize_event(self, event_type: str) -> str:
        """
        Group events into tactical categories.
        
        Args:
            event_type: Raw event type string
        
        Returns:
            Category: "defensive_action", "passing", "progressive", 
                     "set_piece", "goal_related", or "other"
        
        Example:
            >>> processor = EventProcessor()
            >>> category = processor.categorize_event("Interception")
            >>> print(category)  # "defensive_action"
        """
        if not isinstance(event_type, str):
            return "other"
        
        event_lower = event_type.lower()
        
        # Check each category
        if any(action in event_lower for action in self.DEFENSIVE_ACTIONS):
            return "defensive_action"
        elif any(action in event_lower for action in self.PASSING_EVENTS):
            return "passing"
        elif any(action in event_lower for action in self.PROGRESSIVE_ACTIONS):
            return "progressive"
        elif any(action in event_lower for action in self.SET_PIECES):
            return "set_piece"
        elif any(action in event_lower for action in self.GOAL_RELATED):
            return "goal_related"
        else:
            return "other"
    
    def link_to_ball_coordinates(
        self,
        events_df: pd.DataFrame,
        coords_df: pd.DataFrame,
        tolerance_seconds: float = 5.0
    ) -> pd.DataFrame:
        """
        Link events to ball coordinates by timestamp.
        
        Finds the ball position at each event time and adds coordinate
        information to the events DataFrame.
        
        Args:
            events_df: Events DataFrame
            coords_df: Ball coordinates with estimated_minute
            tolerance_seconds: Maximum time difference for matching
        
        Returns:
            Events DataFrame with ball_x, ball_y, ball_zone columns added
        
        Example:
            >>> processor = EventProcessor()
            >>> events_df = processor.link_to_ball_coordinates(events_df, coords_df)
            >>> linked_pct = events_df['ball_x'].notna().sum() / len(events_df) * 100
            >>> print(f"Linked: {linked_pct:.1f}%")
        """
        from .ball_coordinates import BallCoordinateProcessor
        
        # Initialize columns
        events_df["ball_x"] = None
        events_df["ball_y"] = None
        events_df["ball_zone"] = None
        events_df["link_confidence"] = None
        
        # Ensure coordinates have estimated_minute
        if "estimated_minute" not in coords_df.columns:
            self.logger.warning("Coordinates missing estimated_minute - cannot link")
            return events_df
        
        ball_processor = BallCoordinateProcessor()
        
        # Link each event
        for idx, event in events_df.iterrows():
            closest_coord = ball_processor.link_event_to_coordinate(
                event, coords_df, tolerance_seconds
            )
            
            if closest_coord is not None:
                events_df.at[idx, "ball_x"] = closest_coord["x"]
                events_df.at[idx, "ball_y"] = closest_coord["y"]
                events_df.at[idx, "ball_zone"] = closest_coord.get("pitch_zone", "unknown")
                
                # Calculate confidence based on time difference
                time_diff = abs(closest_coord.get("estimated_minute", 0) - event.get("minute", 0))
                if time_diff < 0.05:  # 3 seconds
                    events_df.at[idx, "link_confidence"] = "high"
                elif time_diff < 0.083:  # 5 seconds
                    events_df.at[idx, "link_confidence"] = "medium"
                else:
                    events_df.at[idx, "link_confidence"] = "low"
        
        # Report linking success
        linked = events_df["ball_x"].notna().sum()
        total = len(events_df)
        success_rate = linked / total * 100 if total > 0 else 0
        
        self.logger.info(f"Event-coordinate linking: {linked}/{total} ({success_rate:.1f}%)")
        
        if success_rate < 80:
            self.logger.warning(f"⚠️  Low linking success rate: {success_rate:.1f}%")
        
        return events_df
    
    def get_player_events(
        self,
        events_df: pd.DataFrame,
        player_id: int
    ) -> pd.DataFrame:
        """
        Extract all events for a specific player.
        
        Args:
            events_df: Events DataFrame
            player_id: Player ID to filter
        
        Returns:
            Filtered DataFrame with player's events
        
        Example:
            >>> processor = EventProcessor()
            >>> gravenberch_events = processor.get_player_events(events_df, 123456)
            >>> print(f"Gravenberch had {len(gravenberch_events)} events")
        """
        return events_df[events_df["player_id"] == player_id].copy()
    
    def get_team_events(
        self,
        events_df: pd.DataFrame,
        team_id: int,
        category: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Extract events for a specific team, optionally filtered by category.
        
        Args:
            events_df: Events DataFrame
            team_id: Team ID to filter
            category: Optional event category filter
        
        Returns:
            Filtered DataFrame
        
        Example:
            >>> processor = EventProcessor()
            >>> liverpool_defensive = processor.get_team_events(
            ...     events_df, team_id=8, category="defensive_action"
            ... )
            >>> print(f"Liverpool defensive actions: {len(liverpool_defensive)}")
        """
        team_events = events_df[events_df["team_id"] == team_id].copy()
        
        if category:
            team_events = team_events[team_events["event_category"] == category]
        
        return team_events
    
    def calculate_event_summary(self, events_df: pd.DataFrame) -> dict:
        """
        Calculate summary statistics for events.
        
        Args:
            events_df: Events DataFrame
        
        Returns:
            Dictionary with event statistics
        
        Example:
            >>> processor = EventProcessor()
            >>> summary = processor.calculate_event_summary(events_df)
            >>> print(f"Total events: {summary['total_events']}")
            >>> print(f"By category: {summary['by_category']}")
        """
        summary = {
            "total_events": len(events_df),
            "by_category": events_df["event_category"].value_counts().to_dict(),
            "by_team": events_df["team_name"].value_counts().to_dict(),
            "minute_range": (
                events_df["minute"].min(),
                events_df["minute"].max()
            ) if len(events_df) > 0 else (None, None),
        }
        
        # Add linking stats if available
        if "ball_x" in events_df.columns:
            linked = events_df["ball_x"].notna().sum()
            summary["coordinates_linked"] = linked
            summary["link_success_rate"] = linked / len(events_df) * 100 if len(events_df) > 0 else 0
        
        return summary
