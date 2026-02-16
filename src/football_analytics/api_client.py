"""SportsMonk API client for fetching football data."""

import os
from typing import Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class SportsMonkClient:
    """Client for interacting with the SportsMonk API."""

    BASE_URL = "https://api.sportmonks.com/v3/football"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the SportsMonk API client.

        Args:
            api_key: API key for authentication. If not provided, will look for
                    SPORTSMONK_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("SPORTSMONK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set as SPORTSMONK_API_KEY environment variable"
            )
        self.session = requests.Session()
        self.session.headers.update({"Authorization": self.api_key})

    def _make_request(
        self, endpoint: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Make a request to the SportsMonk API.

        Args:
            endpoint: API endpoint to call
            params: Query parameters for the request

        Returns:
            JSON response from the API

        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_leagues(self) -> dict[str, Any]:
        """Fetch all available football leagues."""
        return self._make_request("leagues")

    def get_teams(self, league_id: int) -> dict[str, Any]:
        """
        Fetch teams for a specific league.

        Args:
            league_id: ID of the league

        Returns:
            Teams data
        """
        return self._make_request(f"teams/season/{league_id}")

    def get_fixtures(self, league_id: int) -> dict[str, Any]:
        """
        Fetch fixtures for a specific league.

        Args:
            league_id: ID of the league

        Returns:
            Fixtures data
        """
        return self._make_request(f"fixtures/season/{league_id}")

    def search_team(self, team_name: str) -> dict[str, Any]:
        """
        Search for a team by name.

        Args:
            team_name: Name of the team to search for

        Returns:
            Team search results
        """
        return self._make_request(f"teams/search/{team_name}")

    def get_team_by_id(self, team_id: int) -> dict[str, Any]:
        """
        Get detailed team information by ID.

        Args:
            team_id: ID of the team

        Returns:
            Team data
        """
        return self._make_request(f"teams/{team_id}")

    def get_seasons(self) -> dict[str, Any]:
        """
        Fetch all available seasons.

        Returns:
            Seasons data
        """
        return self._make_request("seasons")

    def get_team_fixtures(
        self, team_id: int, season_id: int, include: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Fetch fixtures for a specific team in a season.

        Args:
            team_id: ID of the team
            season_id: ID of the season
            include: Comma-separated list of includes (e.g., "ballCoordinates,events")

        Returns:
            Fixtures data
        """
        params = {}
        if include:
            params["include"] = include

        return self._make_request(f"fixtures/between/{season_id}/{team_id}", params)

    def get_fixture_details(self, fixture_id: int, include: Optional[str] = None) -> dict[str, Any]:
        """
        Get detailed fixture information including ball coordinates, events, etc.

        Args:
            fixture_id: ID of the fixture
            include: Comma-separated list of includes
                    (e.g., "ballCoordinates,events,lineups.detailedPosition,formations,statistics")

        Returns:
            Detailed fixture data
        """
        params = {}
        if include:
            params["include"] = include

        return self._make_request(f"fixtures/{fixture_id}", params)

    def get_player_stats(self, player_id: int, season_id: int) -> dict[str, Any]:
        """
        Get player statistics for a specific season.

        Args:
            player_id: ID of the player
            season_id: ID of the season

        Returns:
            Player statistics data
        """
        return self._make_request(
            f"players/{player_id}", {"include": f"statistics.season:{season_id}"}
        )

    def get_statistic_types(self) -> dict[str, Any]:
        """
        Get all available statistic type definitions.

        Returns:
            Statistic types data
        """
        return self._make_request("types")
