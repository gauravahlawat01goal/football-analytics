import pandas as pd
import numpy as np

class UnderstatProcessor:
    """Processor for Understat xG and shot data."""
    
    @staticmethod
    def calculate_true_shot_distance(df: pd.DataFrame, x_col: str = 'x', y_col: str = 'y', pitch_length: float = 105.0, pitch_width: float = 68.0) -> pd.DataFrame:
        """
        Calculate true Euclidean distance in meters from the goal center.
        Understat coordinates are 0-1. Goal center is at x=1.0, y=0.5.
        """
        df = df.copy()
        # Distance = sqrt( ((1-x) * pitch_length)^2 + ((0.5-y) * pitch_width)^2 )
        df['real_distance_m'] = np.sqrt(
            ((1 - df[x_col]) * pitch_length) ** 2 + 
            ((0.5 - df[y_col]) * pitch_width) ** 2
        )
        return df

    @staticmethod
    def filter_by_date(df: pd.DataFrame, start_date: str = None, end_date: str = None, date_col: str = 'date') -> pd.DataFrame:
        """Filter matches/shots by a date range (useful for isolating manager tenures)."""
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        if start_date:
            df = df[df[date_col] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df[date_col] <= pd.to_datetime(end_date)]
        return df

    @staticmethod
    def calculate_match_npxg(shots_df: pd.DataFrame, match_id_col: str = 'understat_match_id', xg_col: str = 'xg') -> pd.DataFrame:
        """
        Aggregate Non-Penalty xG (npxG) at the match level.
        Filters out 'Penalty' situations before aggregating.
        """
        if 'situation' not in shots_df.columns:
            raise ValueError("Shots dataframe must contain 'situation' column to filter penalties.")
            
        npxg_shots = shots_df[shots_df['situation'] != 'Penalty']
        match_npxg = npxg_shots.groupby(match_id_col)[xg_col].sum().reset_index()
        match_npxg.rename(columns={xg_col: 'npxG'}, inplace=True)
        
        return match_npxg
