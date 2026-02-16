"""Fixture collector for finding team fixtures across seasons.

Collects fixture metadata (IDs, dates, opponents) for a specific team
across one or more seasons.

Strategy:
- Search by date (API provides fixtures/date/{date} endpoint)
- Check every week throughout the season (Aug-May for Premier League)
- Filter results for specific team
- Save consolidated fixture list

TODO (Framework Evolution):
    - Add support for cup competitions (Champions League, FA Cup)
    - Add opponent strength classification (top 6, mid-table, relegation)
    - Add home/away split statistics
    - Add fixture difficulty calculator
    - Cache season date ranges per league
"""

from datetime import datetime, timedelta
from typing import Any

from football_analytics.utils import save_json

from .base import BaseCollector


class FixtureCollector(BaseCollector):
    """
    Collect all fixtures for a specific team across seasons.

    Args:
        team_id: SportsMonk team ID
        output_dir: Directory for saving fixture data
        rate_limit_seconds: API rate limit delay
        resume: Skip existing fixture lists

    Example:
        >>> collector = FixtureCollector(team_id=8)  # Liverpool
        >>> fixtures = collector.collect_fixtures_for_seasons([21646, 23614])
        >>> len(fixtures)  # Number of fixtures found
        57
    """

    # Season date ranges (can be overridden per league)
    # TODO: Move to configuration file when building framework
    SEASON_DATE_RANGES = {
        21646: ("2023-08-01", "2024-05-31"),  # 2023/24
        23614: ("2024-08-01", "2025-05-31"),  # 2024/25
    }

    def __init__(self, team_id: int, **kwargs):
        """Initialize fixture collector for specific team."""
        super().__init__(**kwargs)
        self.team_id = team_id
        self.logger.info(f"FixtureCollector initialized for team_id={team_id}")

    def collect_fixtures_for_seasons(
        self, season_ids: list[int], search_interval_days: int = 7
    ) -> list[dict[str, Any]]:
        """
        Find all fixtures for team across multiple seasons.

        Args:
            season_ids: List of season IDs to search
            search_interval_days: Days between searches (default: 7)

        Returns:
            List of fixture metadata dictionaries

        Example:
            >>> collector = FixtureCollector(team_id=8)
            >>> fixtures = collector.collect_fixtures_for_seasons([21646])
            >>> fixtures[0]["fixture_id"]
            18841624
        """
        all_fixtures = []

        for season_id in season_ids:
            self.logger.info(f"Collecting fixtures for season {season_id}")

            fixtures = self._find_fixtures_for_season(
                season_id=season_id, search_interval_days=search_interval_days
            )

            self.logger.info(f"Found {len(fixtures)} fixtures for season {season_id}")
            all_fixtures.extend(fixtures)

        # Sort by date
        all_fixtures.sort(key=lambda x: x.get("date", ""))

        # Save consolidated fixture list
        output_path = self.output_dir / "fixtures_list.json"
        save_json(all_fixtures, output_path)
        self.increment_files_created()

        self.logger.info(
            f"Collected {len(all_fixtures)} total fixtures, " f"saved to {output_path}"
        )

        return all_fixtures

    def _find_fixtures_for_season(
        self, season_id: int, search_interval_days: int = 7
    ) -> list[dict[str, Any]]:
        """
        Find all fixtures for one season by date-range search.

        Args:
            season_id: Season ID to search
            search_interval_days: Days between search queries

        Returns:
            List of fixture metadata for this season
        """
        # Get season date range
        if season_id not in self.SEASON_DATE_RANGES:
            self.logger.warning(f"Unknown season_id {season_id}, using default date range")
            start_date = datetime(2023, 8, 1)
            end_date = datetime(2024, 5, 31)
        else:
            start_str, end_str = self.SEASON_DATE_RANGES[season_id]
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_str, "%Y-%m-%d")

        fixtures = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")

            try:
                # Rate limit
                self.rate_limiter.wait()

                # Fetch fixtures for this date
                result = self.client._make_request(
                    f"fixtures/date/{date_str}", params={"include": "participants"}
                )
                self.increment_api_calls()

                # Filter for our team
                for fixture in result.get("data", []):
                    if self._has_team(fixture, self.team_id):
                        fixture_meta = self._extract_fixture_metadata(fixture)
                        fixtures.append(fixture_meta)

                        self.logger.info(
                            f"  ✓ Found: {fixture_meta['name']} "
                            f"(ID: {fixture_meta['fixture_id']}, Date: {date_str})"
                        )

            except Exception as e:
                error_str = str(e)
                # 404 is expected when no matches on that date
                if "404" not in error_str:
                    self.logger.warning(f"Error fetching {date_str}: {error_str}")
                    self.increment_errors()

            current_date += timedelta(days=search_interval_days)

        return fixtures

    def _has_team(self, fixture: dict[str, Any], team_id: int) -> bool:
        """
        Check if team participates in fixture.

        Args:
            fixture: Fixture data from API
            team_id: Team ID to check for

        Returns:
            True if team is in fixture, False otherwise
        """
        participants = fixture.get("participants", [])
        return any(p.get("id") == team_id for p in participants)

    def _extract_fixture_metadata(self, fixture: dict[str, Any]) -> dict[str, Any]:
        """
        Extract relevant metadata from fixture response.

        Args:
            fixture: Raw fixture data from API

        Returns:
            Dictionary with essential fixture information
        """
        participants = fixture.get("participants", [])

        # Extract team names
        home_team = "Unknown"
        away_team = "Unknown"

        if len(participants) >= 2:
            home_team = participants[0].get("name", "Unknown")
            away_team = participants[1].get("name", "Unknown")

        return {
            "fixture_id": fixture["id"],
            "season_id": fixture.get("season_id"),
            "league_id": fixture.get("league_id"),
            "date": fixture.get("starting_at"),
            "name": f"{home_team} vs {away_team}",
            "home_team": home_team,
            "away_team": away_team,
            "home_team_id": participants[0].get("id") if participants else None,
            "away_team_id": participants[1].get("id") if len(participants) > 1 else None,
            "state_id": fixture.get("state_id"),
        }

    def add_season_date_range(self, season_id: int, start_date: str, end_date: str) -> None:
        """
        Add custom date range for a season.

        Useful when extending to other leagues/competitions with different
        season schedules.

        Args:
            season_id: Season ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Example:
            >>> collector = FixtureCollector(team_id=8)
            >>> collector.add_season_date_range(99999, "2025-08-01", "2026-05-31")

        TODO (Framework Evolution):
            - Load date ranges from configuration file
            - Auto-detect date ranges from league calendar API
            - Support mid-season competitions (World Cup breaks, etc.)
        """
        self.SEASON_DATE_RANGES[season_id] = (start_date, end_date)
        self.logger.info(f"Added season date range: {season_id} -> {start_date} to {end_date}")
