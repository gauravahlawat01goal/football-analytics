"""Player ID extraction and database building.

This module builds a comprehensive player database from lineup data,
extracting player IDs, names, positions, and appearance data.

Key features:
- Player ID extraction from lineup data
- Player appearance tracking
- Position history
- Key player identification
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from ..utils.file_io import load_json as load_json_file
from ..utils.logging_utils import get_logger
from .formations import FormationParser


class PlayerIDExtractor:
    """
    Build and manage player database from lineup data.
    
    Extracts player information from all matches to create a comprehensive
    player database with IDs, positions, and statistics.
    
    Args:
        data_dir: Base directory containing raw data
    
    Example:
        >>> extractor = PlayerIDExtractor()
        >>> players_df = extractor.extract_all_players([fixture1, fixture2, ...])
        >>> key_players = extractor.find_key_players(players_df)
        >>> print(f"Gravenberch ID: {key_players['Gravenberch']}")
    """
    
    # Key players to identify for Liverpool analysis
    KEY_PLAYERS = {
        "Gravenberch": ["Gravenberch", "Ryan Gravenberch"],
        "Trent Alexander-Arnold": ["Trent", "Alexander-Arnold", "T. Alexander-Arnold"],
        "Andrew Robertson": ["Robertson", "A. Robertson", "Andy Robertson"],
        "Virgil van Dijk": ["Van Dijk", "Virgil", "V. van Dijk"],
        "Mohamed Salah": ["Salah", "M. Salah", "Mo Salah"],
        "Luis Díaz": ["Díaz", "Diaz", "L. Díaz", "Luis Diaz"],
    }
    
    def __init__(self, data_dir: str = "data/raw"):
        """Initialize player ID extractor."""
        self.data_dir = Path(data_dir)
        self.logger = get_logger(self.__class__.__name__)
        self.formation_parser = FormationParser(data_dir)
    
    def extract_all_players(
        self,
        fixture_ids: list[int],
        team_name: str = "Liverpool"
    ) -> pd.DataFrame:
        """
        Extract all players from a list of fixtures.
        
        Args:
            fixture_ids: List of fixture IDs to process
            team_name: Team name to filter (default: "Liverpool")
        
        Returns:
            DataFrame with player database
        
        Example:
            >>> extractor = PlayerIDExtractor()
            >>> fixture_ids = [18841624, 18841629, ...]
            >>> players = extractor.extract_all_players(fixture_ids)
            >>> print(f"Found {len(players)} unique players")
        """
        players_database = {}
        
        self.logger.info(f"Extracting players from {len(fixture_ids)} fixtures...")
        
        for fixture_id in fixture_ids:
            try:
                lineups = self.formation_parser.parse_lineups(fixture_id)
                
                if len(lineups) == 0:
                    continue
                
                # Filter for team
                team_lineup = lineups[lineups["team_name"] == team_name]
                
                # Process each player
                for _, player_row in team_lineup.iterrows():
                    player_id = player_row["player_id"]
                    
                    if pd.isna(player_id):
                        continue
                    
                    player_id = int(player_id)
                    
                    # Add to database or update existing
                    if player_id not in players_database:
                        players_database[player_id] = {
                            "player_id": player_id,
                            "player_name": player_row["player_name"],
                            "positions": set(),
                            "jersey_numbers": set(),
                            "appearances": 0,
                            "starts": 0,
                            "captain_appearances": 0,
                        }
                    
                    # Update player data
                    player_entry = players_database[player_id]
                    
                    if not pd.isna(player_row["position"]):
                        player_entry["positions"].add(player_row["position"])
                    
                    if not pd.isna(player_row["jersey_number"]):
                        player_entry["jersey_numbers"].add(int(player_row["jersey_number"]))
                    
                    player_entry["appearances"] += 1
                    
                    if player_row.get("starting", False):
                        player_entry["starts"] += 1
                    
                    if player_row.get("captain", False):
                        player_entry["captain_appearances"] += 1
            
            except Exception as e:
                self.logger.warning(f"Failed to process fixture {fixture_id}: {e}")
                continue
        
        # Convert to DataFrame
        if not players_database:
            self.logger.warning("No players found!")
            return pd.DataFrame()
        
        players_df = pd.DataFrame.from_dict(players_database, orient="index")
        
        # Convert sets to strings
        players_df["positions"] = players_df["positions"].apply(
            lambda x: ", ".join(sorted(x)) if x else ""
        )
        players_df["jersey_numbers"] = players_df["jersey_numbers"].apply(
            lambda x: ", ".join(map(str, sorted(x))) if x else ""
        )
        
        # Sort by appearances
        players_df = players_df.sort_values("appearances", ascending=False)
        
        self.logger.info(f"✅ Extracted {len(players_df)} unique players")
        self.logger.info(f"   Total appearances: {players_df['appearances'].sum()}")
        
        return players_df
    
    def find_key_players(self, players_df: pd.DataFrame) -> dict:
        """
        Identify specific key players of interest.
        
        Searches for key players using name variations and returns their IDs.
        
        Args:
            players_df: Players DataFrame
        
        Returns:
            Dictionary mapping player names to IDs
        
        Example:
            >>> extractor = PlayerIDExtractor()
            >>> key_players = extractor.find_key_players(players_df)
            >>> if key_players.get("Gravenberch"):
            ...     print(f"Found Gravenberch: ID {key_players['Gravenberch']}")
        """
        found_players = {}
        
        for canonical_name, name_variants in self.KEY_PLAYERS.items():
            player_id = None
            
            # Try each name variant
            for name_variant in name_variants:
                matches = players_df[
                    players_df["player_name"].str.contains(
                        name_variant, case=False, na=False, regex=False
                    )
                ]
                
                if len(matches) > 0:
                    # Use the player with most appearances if multiple matches
                    player_id = matches.iloc[0]["player_id"]
                    player_name = matches.iloc[0]["player_name"]
                    
                    self.logger.info(f"✅ Found {canonical_name}: "
                                   f"{player_name} (ID: {player_id})")
                    break
            
            if player_id:
                found_players[canonical_name] = {
                    "player_id": int(player_id),
                    "player_name": player_name,
                    "appearances": int(matches.iloc[0]["appearances"]),
                }
            else:
                self.logger.warning(f"❌ NOT FOUND: {canonical_name}")
                found_players[canonical_name] = None
        
        return found_players
    
    def get_player_by_name(
        self,
        players_df: pd.DataFrame,
        name_query: str
    ) -> Optional[pd.Series]:
        """
        Search for a player by name (fuzzy matching).
        
        Args:
            players_df: Players DataFrame
            name_query: Name to search for
        
        Returns:
            Player series or None if not found
        
        Example:
            >>> extractor = PlayerIDExtractor()
            >>> player = extractor.get_player_by_name(players_df, "Salah")
            >>> if player is not None:
            ...     print(f"Found: {player['player_name']} (ID: {player['player_id']})")
        """
        matches = players_df[
            players_df["player_name"].str.contains(
                name_query, case=False, na=False, regex=False
            )
        ]
        
        if len(matches) == 0:
            return None
        
        # Return player with most appearances if multiple matches
        return matches.iloc[0]
    
    def save_player_database(
        self,
        players_df: pd.DataFrame,
        output_path: str = "data/processed/metadata/liverpool_players.csv"
    ) -> Path:
        """
        Save player database to CSV.
        
        Args:
            players_df: Players DataFrame
            output_path: Output file path
        
        Returns:
            Path to saved file
        
        Example:
            >>> extractor = PlayerIDExtractor()
            >>> output_path = extractor.save_player_database(players_df)
            >>> print(f"Saved to: {output_path}")
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        players_df.to_csv(output_file, index=False)
        
        self.logger.info(f"✅ Player database saved to: {output_file}")
        
        return output_file
    
    def save_key_player_ids(
        self,
        key_players: dict,
        output_path: str = "data/processed/metadata/key_player_ids.json"
    ) -> Path:
        """
        Save key player IDs to JSON.
        
        Args:
            key_players: Dictionary from find_key_players()
            output_path: Output file path
        
        Returns:
            Path to saved file
        
        Example:
            >>> extractor = PlayerIDExtractor()
            >>> output_path = extractor.save_key_player_ids(key_players)
            >>> print(f"Saved to: {output_path}")
        """
        import json
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON
        with open(output_file, 'w') as f:
            json.dump(key_players, f, indent=2)
        
        self.logger.info(f"✅ Key player IDs saved to: {output_file}")
        
        return output_file
    
    def get_player_statistics(
        self,
        players_df: pd.DataFrame,
        player_id: int
    ) -> Optional[dict]:
        """
        Get statistics for a specific player.
        
        Args:
            players_df: Players DataFrame
            player_id: Player ID
        
        Returns:
            Dictionary with player statistics or None
        
        Example:
            >>> extractor = PlayerIDExtractor()
            >>> stats = extractor.get_player_statistics(players_df, 123456)
            >>> if stats:
            ...     print(f"Appearances: {stats['appearances']}")
            ...     print(f"Positions: {stats['positions']}")
        """
        player_row = players_df[players_df["player_id"] == player_id]
        
        if len(player_row) == 0:
            return None
        
        player = player_row.iloc[0]
        
        return {
            "player_id": int(player["player_id"]),
            "player_name": player["player_name"],
            "positions": player["positions"],
            "jersey_numbers": player["jersey_numbers"],
            "appearances": int(player["appearances"]),
            "starts": int(player["starts"]),
            "captain_appearances": int(player["captain_appearances"]),
            "start_percentage": player["starts"] / player["appearances"] * 100 if player["appearances"] > 0 else 0,
        }
