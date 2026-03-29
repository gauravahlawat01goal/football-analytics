"""Match statistics processing.

Flattens raw statistics.json API responses into a clean CSV per fixture.
Each row is one (type_id, team) stat entry for a match.
"""

from pathlib import Path

import pandas as pd

from ..utils.file_io import load_json
from ..utils.logging_utils import get_logger


class StatisticsProcessor:
    """
    Parse match statistics from raw API responses.

    Reads statistics.json for each fixture and flattens the nested structure
    into a tidy CSV with one row per (type_id, participant) pair.

    Args:
        data_dir: Directory containing raw fixture subdirectories.

    Example:
        >>> processor = StatisticsProcessor()
        >>> df = processor.parse_statistics(19134607)
        >>> print(df.columns.tolist())
        ['fixture_id', 'type_id', 'participant_id', 'location', 'value']
    """

    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.logger = get_logger(self.__class__.__name__)

    def parse_statistics(self, fixture_id: int) -> pd.DataFrame:
        """
        Flatten statistics.json for a single fixture into a DataFrame.

        Args:
            fixture_id: Fixture ID to process.

        Returns:
            DataFrame with columns: fixture_id, type_id, participant_id, location, value.
            Empty DataFrame if file not found or no statistics present.
        """
        stats_file = self.data_dir / str(fixture_id) / "statistics.json"

        if not stats_file.exists():
            self.logger.error(f"statistics.json not found for fixture {fixture_id}")
            return pd.DataFrame()

        try:
            raw = load_json(stats_file)
        except Exception as e:
            self.logger.error(f"Failed to load statistics.json for fixture {fixture_id}: {e}")
            return pd.DataFrame()

        # API response: raw["data"]["statistics"] is the list of stat entries
        data = raw.get("data", {})
        stats_list = data.get("statistics", [])

        if not stats_list:
            self.logger.warning(f"No statistics entries for fixture {fixture_id}")
            return pd.DataFrame()

        rows = []
        for entry in stats_list:
            rows.append({
                "fixture_id": fixture_id,
                "type_id": entry.get("type_id"),
                "participant_id": entry.get("participant_id"),
                "location": entry.get("location"),
                "value": (entry.get("data") or {}).get("value"),
            })

        df = pd.DataFrame(rows)
        self.logger.info(f"Parsed {len(df)} statistics entries for fixture {fixture_id}")
        return df

    def save_statistics(
        self,
        df: pd.DataFrame,
        fixture_id: int,
        output_dir: str = "data/processed/fixtures",
    ) -> Path:
        """
        Save statistics DataFrame to CSV.

        Args:
            df: DataFrame from parse_statistics().
            fixture_id: Fixture ID (used to create output path).
            output_dir: Base output directory.

        Returns:
            Path to the saved CSV file.
        """
        out_path = Path(output_dir) / str(fixture_id) / "statistics.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False, encoding="utf-8")
        self.logger.info(f"Saved statistics CSV to {out_path}")
        return out_path
