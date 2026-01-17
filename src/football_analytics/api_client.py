"""SportsMonk API client for fetching football data."""

import os
from typing import Any, Dict, Optional

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
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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

    def get_leagues(self) -> Dict[str, Any]:
        """Fetch all available football leagues."""
        return self._make_request("leagues")

    def get_teams(self, league_id: int) -> Dict[str, Any]:
        """
        Fetch teams for a specific league.

        Args:
            league_id: ID of the league

        Returns:
            Teams data
        """
        return self._make_request(f"teams/season/{league_id}")

    def get_fixtures(self, league_id: int) -> Dict[str, Any]:
        """
        Fetch fixtures for a specific league.

        Args:
            league_id: ID of the league

        Returns:
            Fixtures data
        """
        return self._make_request(f"fixtures/season/{league_id}")
