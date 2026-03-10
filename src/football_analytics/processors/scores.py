"""Match scores processing.

Flattens raw scores.json API responses into a clean CSV per fixture.
Each row is one period-level score entry (1ST_HALF, 2ND_HALF, CURRENT, etc.).

Note: scores.json contains period aggregates only, NOT minute-by-minute state.
For reconstructing in-match game state use goal events from events.csv.
"""

from pathlib import Path

import pandas as pd

from ..utils.file_io import load_json
from ..utils.logging_utils import get_logger


class ScoresProcessor:
    """
    Parse match scores from raw API responses.

    Reads scores.json for each fixture and flattens the nested structure
    into a tidy CSV with one row per (period, participant) score entry.

    Args:
        data_dir: Directory containing raw fixture subdirectories.

    Example:
        >>> processor = ScoresProcessor()
        >>> df = processor.parse_scores(19134607)
        >>> print(df[['description', 'participant', 'goals']])
        # description  participant  goals
        # 1ST_HALF     home         1
        # 1ST_HALF     away         0
        # 2ND_HALF     home         2
        # 2ND_HALF     away         0
        # CURRENT      home         2
        # CURRENT      away         0
    """

    def __init__(self, data_dir: str = "data/backup"):
        self.data_dir = Path(data_dir)
        self.logger = get_logger(self.__class__.__name__)

    def parse_scores(self, fixture_id: int) -> pd.DataFrame:
        """
        Flatten scores.json for a single fixture into a DataFrame.

        Args:
            fixture_id: Fixture ID to process.

        Returns:
            DataFrame with columns: fixture_id, type_id, participant_id,
            description, goals, participant.
            Empty DataFrame if file not found or no scores present.
        """
        scores_file = self.data_dir / str(fixture_id) / "scores.json"

        if not scores_file.exists():
            self.logger.error(f"scores.json not found for fixture {fixture_id}")
            return pd.DataFrame()

        try:
            raw = load_json(scores_file)
        except Exception as e:
            self.logger.error(f"Failed to load scores.json for fixture {fixture_id}: {e}")
            return pd.DataFrame()

        data = raw.get("data", {})
        scores_list = data.get("scores", [])

        if not scores_list:
            self.logger.warning(f"No score entries for fixture {fixture_id}")
            return pd.DataFrame()

        rows = []
        for entry in scores_list:
            score = entry.get("score", {})
            rows.append({
                "fixture_id": fixture_id,
                "type_id": entry.get("type_id"),
                "participant_id": entry.get("participant_id"),
                "description": entry.get("description"),
                "goals": score.get("goals"),
                "participant": score.get("participant"),
            })

        df = pd.DataFrame(rows)
        # Sort by period for readability: 1ST_HALF before 2ND_HALF before CURRENT
        period_order = {"1ST_HALF": 0, "2ND_HALF": 1, "2ND_HALF_ONLY": 2, "CURRENT": 3}
        df["_sort"] = df["description"].map(period_order).fillna(99)
        df = df.sort_values(["_sort", "participant"]).drop(columns="_sort").reset_index(drop=True)

        self.logger.info(f"Parsed {len(df)} score entries for fixture {fixture_id}")
        return df

    def save_scores(
        self,
        df: pd.DataFrame,
        fixture_id: int,
        output_dir: str = "data/processed/fixtures",
    ) -> Path:
        """
        Save scores DataFrame to CSV.

        Args:
            df: DataFrame from parse_scores().
            fixture_id: Fixture ID (used to create output path).
            output_dir: Base output directory.

        Returns:
            Path to the saved CSV file.
        """
        out_path = Path(output_dir) / str(fixture_id) / "scores.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False, encoding="utf-8")
        self.logger.info(f"Saved scores CSV to {out_path}")
        return out_path
