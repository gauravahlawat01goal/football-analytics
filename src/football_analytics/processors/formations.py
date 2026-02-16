"""Formation and lineup parsing.

This module processes formation and lineup data, handling:
- Formation structure parsing
- Player position extraction
- Starting XI identification
- Substitution tracking
- Position categorization

Key features:
- Structured formation representation
- Player-position mapping
- Tactical shape analysis
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from ..utils.file_io import load_json as load_json_file
from ..utils.logging_utils import get_logger


class FormationParser:
    """
    Parse and analyze team formations and lineups.
    
    Extracts formation data, player positions, and lineup information
    for tactical analysis.
    
    Args:
        data_dir: Base directory containing raw data
    
    Example:
        >>> parser = FormationParser()
        >>> lineups = parser.parse_lineups(18841624)
        >>> formations = parser.parse_formations(18841624)
        >>> liverpool_lineup = lineups[lineups['team_name'] == 'Liverpool']
    """
    
    # Position categories
    GOALKEEPER_POSITIONS = ["GK", "Goalkeeper"]
    DEFENDER_POSITIONS = ["CB", "LB", "RB", "LWB", "RWB", "DF"]
    MIDFIELDER_POSITIONS = ["CDM", "CM", "CAM", "LM", "RM", "DM", "AM"]
    FORWARD_POSITIONS = ["ST", "CF", "LW", "RW", "FW"]
    
    def __init__(self, data_dir: str = "data/raw"):
        """Initialize formation parser."""
        self.data_dir = Path(data_dir)
        self.logger = get_logger(self.__class__.__name__)
    
    def parse_lineups(self, fixture_id: int, season: Optional[str] = None) -> pd.DataFrame:
        """
        Parse player lineups from match data.
        
        Args:
            fixture_id: Fixture ID to process
            season: Optional season identifier
        
        Returns:
            DataFrame with player lineup information
        
        Example:
            >>> parser = FormationParser()
            >>> lineups = parser.parse_lineups(18841624)
            >>> print(lineups[['player_name', 'position', 'team_name', 'starting']].head())
        """
        # Load raw JSON
        fixture_dir = self.data_dir / str(fixture_id)
        lineups_file = fixture_dir / "lineups.json"
        
        if not lineups_file.exists():
            self.logger.error(f"Lineups file not found for fixture {fixture_id}")
            return pd.DataFrame()
        
        lineups_data = load_json_file(lineups_file)
        
        # Extract lineups from API response
        if "data" in lineups_data:
            lineups_list = lineups_data["data"]
        else:
            lineups_list = lineups_data
        
        if not lineups_list:
            self.logger.warning(f"No lineups in file for fixture {fixture_id}")
            return pd.DataFrame()
        
        # Parse each player
        parsed_lineups = []
        for lineup_entry in lineups_list:
            parsed_entry = self._parse_lineup_entry(lineup_entry, fixture_id)
            if parsed_entry:
                parsed_lineups.append(parsed_entry)
        
        # Convert to DataFrame
        df = pd.DataFrame(parsed_lineups)
        
        if len(df) > 0:
            # Add position categories
            df["position_category"] = df["position"].apply(self.categorize_position)
            
            self.logger.info(f"Parsed {len(df)} lineup entries for fixture {fixture_id}")
        
        return df
    
    def _parse_lineup_entry(self, entry: dict, fixture_id: int) -> Optional[dict]:
        """
        Parse a single lineup entry.
        
        Args:
            entry: Raw lineup dictionary
            fixture_id: Fixture ID
        
        Returns:
            Parsed lineup dictionary or None if invalid
        """
        try:
            # Extract player info
            player_data = entry.get("player", {})
            if isinstance(player_data, dict):
                player_id = player_data.get("id")
                player_name = player_data.get("display_name", "Unknown")
            else:
                player_id = entry.get("player_id")
                player_name = "Unknown"
            
            # Extract team info
            participant_data = entry.get("participant", {})
            if isinstance(participant_data, dict):
                team_id = participant_data.get("id")
                team_name = participant_data.get("name", "Unknown")
            else:
                team_id = entry.get("participant_id")
                team_name = "Unknown"
            
            # Extract position info
            detailed_position = entry.get("detailedPosition", {})
            if isinstance(detailed_position, dict):
                position = detailed_position.get("name", "Unknown")
            else:
                position = entry.get("position", "Unknown")
            
            # Formation field (e.g., "2:2" for center-back)
            formation_field = entry.get("formation_field")
            
            # Parse formation field into position coordinates
            formation_x, formation_y = None, None
            if formation_field and ":" in str(formation_field):
                try:
                    parts = str(formation_field).split(":")
                    if len(parts) == 2:
                        formation_x = int(parts[0])
                        formation_y = int(parts[1])
                except ValueError:
                    pass
            
            parsed_entry = {
                "fixture_id": fixture_id,
                "player_id": player_id,
                "player_name": player_name,
                "team_id": team_id,
                "team_name": team_name,
                "position": position,
                "formation_field": formation_field,
                "formation_x": formation_x,
                "formation_y": formation_y,
                "jersey_number": entry.get("jersey_number"),
                "starting": entry.get("starting", False),
                "captain": entry.get("captain", False),
            }
            
            return parsed_entry
        
        except Exception as e:
            self.logger.warning(f"Failed to parse lineup entry: {e}")
            return None
    
    def categorize_position(self, position: str) -> str:
        """
        Categorize detailed position into broad category.
        
        Args:
            position: Detailed position string (e.g., "Centre-Back")
        
        Returns:
            Category: "Goalkeeper", "Defender", "Midfielder", "Forward", "Unknown"
        
        Example:
            >>> parser = FormationParser()
            >>> category = parser.categorize_position("Centre-Back")
            >>> print(category)  # "Defender"
        """
        if not isinstance(position, str):
            return "Unknown"
        
        position_upper = position.upper()
        
        if any(pos in position_upper for pos in self.GOALKEEPER_POSITIONS):
            return "Goalkeeper"
        elif any(pos in position_upper for pos in self.DEFENDER_POSITIONS):
            return "Defender"
        elif any(pos in position_upper for pos in self.MIDFIELDER_POSITIONS):
            return "Midfielder"
        elif any(pos in position_upper for pos in self.FORWARD_POSITIONS):
            return "Forward"
        else:
            return "Unknown"
    
    def parse_formations(self, fixture_id: int, season: Optional[str] = None) -> pd.DataFrame:
        """
        Parse team formations from match data.
        
        Args:
            fixture_id: Fixture ID to process
            season: Optional season identifier
        
        Returns:
            DataFrame with formation information
        
        Example:
            >>> parser = FormationParser()
            >>> formations = parser.parse_formations(18841624)
            >>> print(formations[['team_name', 'formation', 'location']].head())
        """
        # Load raw JSON
        fixture_dir = self.data_dir / str(fixture_id)
        formations_file = fixture_dir / "formations.json"
        
        if not formations_file.exists():
            self.logger.warning(f"Formations file not found for fixture {fixture_id}")
            return pd.DataFrame()
        
        formations_data = load_json_file(formations_file)
        
        # Extract formations from API response
        if "data" in formations_data:
            formations_list = formations_data["data"]
        else:
            formations_list = formations_data
        
        if not formations_list:
            self.logger.warning(f"No formations in file for fixture {fixture_id}")
            return pd.DataFrame()
        
        # Parse formations
        parsed_formations = []
        for formation in formations_list:
            # Extract participant info
            participant_data = formation.get("participant", {})
            if isinstance(participant_data, dict):
                team_id = participant_data.get("id")
                team_name = participant_data.get("name", "Unknown")
            else:
                team_id = formation.get("participant_id")
                team_name = "Unknown"
            
            parsed_formation = {
                "fixture_id": fixture_id,
                "formation_id": formation.get("id"),
                "team_id": team_id,
                "team_name": team_name,
                "formation": formation.get("formation"),
                "location": formation.get("location"),
                "start_minute": formation.get("start_minute"),
                "end_minute": formation.get("end_minute"),
            }
            
            parsed_formations.append(parsed_formation)
        
        df = pd.DataFrame(parsed_formations)
        
        if len(df) > 0:
            self.logger.info(f"Parsed {len(df)} formations for fixture {fixture_id}")
        
        return df
    
    def get_team_lineup(
        self,
        lineups_df: pd.DataFrame,
        team_id: int,
        starting_only: bool = False
    ) -> pd.DataFrame:
        """
        Extract lineup for a specific team.
        
        Args:
            lineups_df: Lineups DataFrame
            team_id: Team ID to filter
            starting_only: If True, return only starting XI
        
        Returns:
            Filtered DataFrame
        
        Example:
            >>> parser = FormationParser()
            >>> liverpool_starting = parser.get_team_lineup(lineups_df, 8, starting_only=True)
            >>> print(f"Liverpool starting XI: {len(liverpool_starting)} players")
        """
        team_lineup = lineups_df[lineups_df["team_id"] == team_id].copy()
        
        if starting_only:
            team_lineup = team_lineup[team_lineup["starting"] == True]
        
        return team_lineup
    
    def get_player_position(
        self,
        lineups_df: pd.DataFrame,
        player_id: int
    ) -> Optional[dict]:
        """
        Get position information for a specific player in a match.
        
        Args:
            lineups_df: Lineups DataFrame
            player_id: Player ID
        
        Returns:
            Dictionary with player position info or None
        
        Example:
            >>> parser = FormationParser()
            >>> position_info = parser.get_player_position(lineups_df, 123456)
            >>> if position_info:
            ...     print(f"Position: {position_info['position']}")
        """
        player_lineup = lineups_df[lineups_df["player_id"] == player_id]
        
        if len(player_lineup) == 0:
            return None
        
        # Return first match (should only be one per fixture)
        player_row = player_lineup.iloc[0]
        
        return {
            "player_name": player_row["player_name"],
            "position": player_row["position"],
            "position_category": player_row.get("position_category", "Unknown"),
            "formation_field": player_row.get("formation_field"),
            "starting": player_row.get("starting", False),
            "jersey_number": player_row.get("jersey_number"),
        }
    
    def extract_formation_shape(self, formation_str: Optional[str]) -> Optional[dict]:
        """
        Parse formation string (e.g., "4-3-3") into structured shape.
        
        Args:
            formation_str: Formation string (e.g., "4-3-3", "4-2-3-1")
        
        Returns:
            Dictionary with formation structure or None
        
        Example:
            >>> parser = FormationParser()
            >>> shape = parser.extract_formation_shape("4-3-3")
            >>> print(shape)  # {'defenders': 4, 'midfielders': 3, 'forwards': 3}
        """
        if not formation_str or not isinstance(formation_str, str):
            return None
        
        try:
            parts = formation_str.split("-")
            numbers = [int(p) for p in parts]
            
            if len(numbers) == 3:
                return {
                    "defenders": numbers[0],
                    "midfielders": numbers[1],
                    "forwards": numbers[2],
                    "total_outfield": sum(numbers)
                }
            elif len(numbers) == 4:
                return {
                    "defenders": numbers[0],
                    "defensive_midfielders": numbers[1],
                    "attacking_midfielders": numbers[2],
                    "forwards": numbers[3],
                    "total_outfield": sum(numbers)
                }
            else:
                return {"raw": formation_str, "parts": numbers}
        
        except (ValueError, AttributeError):
            return None
    
    def calculate_lineup_summary(self, lineups_df: pd.DataFrame) -> dict:
        """
        Calculate summary statistics for lineups.
        
        Args:
            lineups_df: Lineups DataFrame
        
        Returns:
            Dictionary with lineup statistics
        
        Example:
            >>> parser = FormationParser()
            >>> summary = parser.calculate_lineup_summary(lineups_df)
            >>> print(f"Teams: {summary['num_teams']}")
            >>> print(f"Starting players: {summary['num_starting']}")
        """
        summary = {
            "total_players": len(lineups_df),
            "num_teams": lineups_df["team_id"].nunique(),
            "num_starting": lineups_df["starting"].sum() if "starting" in lineups_df.columns else 0,
            "by_position_category": lineups_df["position_category"].value_counts().to_dict() if "position_category" in lineups_df.columns else {},
            "by_team": lineups_df["team_name"].value_counts().to_dict() if "team_name" in lineups_df.columns else {},
        }
        
        return summary
