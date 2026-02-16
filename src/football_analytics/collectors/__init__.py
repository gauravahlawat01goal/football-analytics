"""Data collectors for football analytics.

This package provides high-level collectors for gathering football data
from the SportsMonk API.

Collectors handle:
- API communication
- Rate limiting
- Error handling
- Resume capability
- Progress tracking
- Data saving

TODO (Framework Evolution):
    - Add caching layer to avoid re-downloading
    - Add parallel collection with asyncio
    - Add data validation on collection
    - Add automatic retry on transient failures
"""

from .fixtures import FixtureCollector
from .match_data import MatchDataCollector

__all__ = ["FixtureCollector", "MatchDataCollector"]
