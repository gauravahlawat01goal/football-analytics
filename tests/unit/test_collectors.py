"""Unit tests for data collectors."""

from unittest.mock import Mock, patch

from football_analytics.collectors import FixtureCollector, MatchDataCollector
from football_analytics.collectors.base import BaseCollector


class TestBaseCollector:
    """Tests for BaseCollector."""

    def test_initialization(self, tmp_path):
        """Test base collector initializes correctly."""
        collector = BaseCollector(output_dir=str(tmp_path))

        assert collector.output_dir == tmp_path
        assert tmp_path.exists()
        assert collector.resume is True
        assert collector.stats["api_calls"] == 0

    def test_should_skip_when_resume_enabled(self, tmp_path):
        """Test should_skip returns True for existing files when resume enabled."""
        collector = BaseCollector(output_dir=str(tmp_path), resume=True)

        existing_file = tmp_path / "existing.json"
        existing_file.touch()

        assert collector.should_skip(existing_file) is True
        assert collector.stats["files_skipped"] == 1

    def test_should_not_skip_when_resume_disabled(self, tmp_path):
        """Test should_skip returns False when resume disabled."""
        collector = BaseCollector(output_dir=str(tmp_path), resume=False)

        existing_file = tmp_path / "existing.json"
        existing_file.touch()

        assert collector.should_skip(existing_file) is False

    def test_statistics_tracking(self, tmp_path):
        """Test statistics are tracked correctly."""
        collector = BaseCollector(output_dir=str(tmp_path))

        collector.increment_api_calls()
        collector.increment_files_created()
        collector.increment_errors()

        stats = collector.get_stats()
        assert stats["api_calls"] == 1
        assert stats["files_created"] == 1
        assert stats["errors"] == 1

        collector.reset_stats()
        stats = collector.get_stats()
        assert stats["api_calls"] == 0


class TestFixtureCollector:
    """Tests for FixtureCollector."""

    @patch("football_analytics.collectors.fixtures.SportsMonkClient")
    def test_initialization(self, mock_client_class, tmp_path):
        """Test fixture collector initializes with team_id."""
        collector = FixtureCollector(team_id=8, output_dir=str(tmp_path))

        assert collector.team_id == 8
        assert collector.output_dir == tmp_path

    def test_has_team(self, tmp_path):
        """Test _has_team correctly identifies team in fixture."""
        with patch("football_analytics.collectors.fixtures.SportsMonkClient"):
            collector = FixtureCollector(team_id=8, output_dir=str(tmp_path))

        fixture_with_team = {
            "participants": [{"id": 8, "name": "Liverpool"}, {"id": 14, "name": "Arsenal"}]
        }

        fixture_without_team = {
            "participants": [{"id": 1, "name": "Chelsea"}, {"id": 2, "name": "Man City"}]
        }

        assert collector._has_team(fixture_with_team, 8) is True
        assert collector._has_team(fixture_without_team, 8) is False

    def test_extract_fixture_metadata(self, tmp_path):
        """Test fixture metadata extraction."""
        with patch("football_analytics.collectors.fixtures.SportsMonkClient"):
            collector = FixtureCollector(team_id=8, output_dir=str(tmp_path))

        fixture = {
            "id": 19134454,
            "season_id": 23614,
            "league_id": 8,
            "starting_at": "2024-08-17T12:00:00",
            "participants": [{"id": 14, "name": "Ipswich Town"}, {"id": 8, "name": "Liverpool"}],
        }

        metadata = collector._extract_fixture_metadata(fixture)

        assert metadata["fixture_id"] == 19134454
        assert metadata["season_id"] == 23614
        assert metadata["home_team"] == "Ipswich Town"
        assert metadata["away_team"] == "Liverpool"
        assert metadata["name"] == "Ipswich Town vs Liverpool"

    def test_add_season_date_range(self, tmp_path):
        """Test adding custom season date ranges."""
        with patch("football_analytics.collectors.fixtures.SportsMonkClient"):
            collector = FixtureCollector(team_id=8, output_dir=str(tmp_path))

        collector.add_season_date_range(99999, "2025-08-01", "2026-05-31")

        assert 99999 in collector.SEASON_DATE_RANGES
        assert collector.SEASON_DATE_RANGES[99999] == ("2025-08-01", "2026-05-31")


class TestMatchDataCollector:
    """Tests for MatchDataCollector."""

    @patch("football_analytics.collectors.match_data.SportsMonkClient")
    def test_initialization(self, mock_client_class, tmp_path):
        """Test match data collector initializes correctly."""
        collector = MatchDataCollector(output_dir=str(tmp_path))

        assert collector.output_dir == tmp_path
        assert len(collector.INCLUDES) == 7
        assert "ballCoordinates" in collector.INCLUDES

    @patch("football_analytics.collectors.match_data.SportsMonkClient")
    def test_collect_fixture_creates_directory(self, mock_client_class, tmp_path):
        """Test that collecting a fixture creates its directory."""
        mock_client = Mock()
        mock_client.get_fixture_details.return_value = {"data": {}}

        with patch(
            "football_analytics.collectors.match_data.SportsMonkClient", return_value=mock_client
        ):
            collector = MatchDataCollector(output_dir=str(tmp_path))
            collector._collect_fixture(12345)

        fixture_dir = tmp_path / "12345"
        assert fixture_dir.exists()
        assert fixture_dir.is_dir()

    @patch("football_analytics.collectors.match_data.SportsMonkClient")
    def test_collect_fixture_saves_all_includes(self, mock_client_class, tmp_path):
        """Test that all includes are fetched and saved."""
        mock_client = Mock()
        mock_client.get_fixture_details.return_value = {"data": {"test": "data"}}

        with patch(
            "football_analytics.collectors.match_data.SportsMonkClient", return_value=mock_client
        ):
            collector = MatchDataCollector(output_dir=str(tmp_path), rate_limit_seconds=0)
            results = collector._collect_fixture(12345)

        # Check all includes were attempted
        assert len(results) == 7
        assert all(results.values())  # All should succeed

        # Check files were created
        fixture_dir = tmp_path / "12345"
        for include in collector.INCLUDES:
            assert (fixture_dir / f"{include}.json").exists()

    @patch("football_analytics.collectors.match_data.SportsMonkClient")
    def test_resume_skips_existing_files(self, mock_client_class, tmp_path):
        """Test that resume skips existing files."""
        mock_client = Mock()
        mock_client.get_fixture_details.return_value = {"data": {}}

        with patch(
            "football_analytics.collectors.match_data.SportsMonkClient", return_value=mock_client
        ):
            collector = MatchDataCollector(
                output_dir=str(tmp_path), resume=True, rate_limit_seconds=0
            )

            # Create existing file
            fixture_dir = tmp_path / "12345"
            fixture_dir.mkdir()
            existing_file = fixture_dir / "ballCoordinates.json"
            existing_file.write_text('{"existing": "data"}')

            results = collector._collect_fixture(12345)

        # ballCoordinates should show as successful but not call API
        assert results["ballCoordinates"] is True

        # Other includes should have been fetched
        assert mock_client.get_fixture_details.call_count == 6  # 7 total - 1 skipped

    @patch("football_analytics.collectors.match_data.SportsMonkClient")
    def test_collect_single_include(self, mock_client_class, tmp_path):
        """Test collecting a single include."""
        mock_client = Mock()
        mock_client.get_fixture_details.return_value = {"data": {"test": "data"}}

        with patch(
            "football_analytics.collectors.match_data.SportsMonkClient", return_value=mock_client
        ):
            collector = MatchDataCollector(output_dir=str(tmp_path), rate_limit_seconds=0)

            success = collector.collect_single_include(
                fixture_id=12345, include_name="ballCoordinates"
            )

        assert success is True
        assert (tmp_path / "12345" / "ballCoordinates.json").exists()

    @patch("football_analytics.collectors.match_data.SportsMonkClient")
    def test_invalid_include_name(self, mock_client_class, tmp_path):
        """Test that invalid include name returns False."""
        with patch("football_analytics.collectors.match_data.SportsMonkClient"):
            collector = MatchDataCollector(output_dir=str(tmp_path))

            success = collector.collect_single_include(
                fixture_id=12345, include_name="invalidInclude"
            )

        assert success is False
