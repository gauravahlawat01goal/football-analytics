"""Data processors for football analytics.

This package contains modules for processing and transforming raw football data:
- Ball coordinate processing
- Event data processing  
- Formation and lineup parsing
- Player position analysis
"""

from .ball_coordinates import BallCoordinateProcessor
from .events import EventProcessor
from .formations import FormationParser
from .player_database import PlayerIDExtractor

__all__ = [
    "BallCoordinateProcessor",
    "EventProcessor",
    "FormationParser",
    "PlayerIDExtractor",
]
