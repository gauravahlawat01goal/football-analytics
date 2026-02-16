"""Tests for SportsMonk API client."""

import pytest
from football_analytics.api_client import SportsMonkClient


def test_client_initialization_without_key():
    """Test that client raises error when API key is not provided."""
    with pytest.raises(ValueError, match="API key must be provided"):
        SportsMonkClient()
