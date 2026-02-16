"""Unit tests for utility modules."""

import json
import logging
import time

from football_analytics.utils import (
    RateLimiter,
    backup_directory,
    file_exists,
    load_json,
    save_json,
    setup_logging,
)


class TestFileIO:
    """Tests for file I/O utilities."""

    def test_save_and_load_json(self, tmp_path):
        """Test saving and loading JSON files."""
        data = {"team": "Liverpool", "id": 8}
        filepath = tmp_path / "test.json"

        # Save
        result_path = save_json(data, filepath)
        assert result_path == filepath
        assert filepath.exists()

        # Load
        loaded_data = load_json(filepath)
        assert loaded_data == data

    def test_save_json_creates_parent_dirs(self, tmp_path):
        """Test that save_json creates parent directories."""
        filepath = tmp_path / "nested" / "dir" / "test.json"
        data = {"test": "data"}

        save_json(data, filepath)

        assert filepath.exists()
        assert filepath.parent.exists()

    def test_file_exists(self, tmp_path):
        """Test file existence check."""
        existing_file = tmp_path / "exists.json"
        existing_file.touch()

        assert file_exists(existing_file) is True
        assert file_exists(tmp_path / "not_exists.json") is False

    def test_backup_directory(self, tmp_path):
        """Test directory backup."""
        # Create source directory with files
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.json").write_text('{"a": 1}')
        (source_dir / "file2.json").write_text('{"b": 2}')

        # Backup
        backup_dir = tmp_path / "backup"
        result = backup_directory(source_dir, backup_dir)

        assert result.exists()
        assert (result / "file1.json").exists()
        assert (result / "file2.json").exists()

        # Verify content
        assert json.loads((result / "file1.json").read_text()) == {"a": 1}


class TestRateLimiter:
    """Tests for rate limiter."""

    def test_first_request_no_wait(self):
        """Test that first request doesn't wait."""
        limiter = RateLimiter(delay=1.0)
        wait_time = limiter.wait()

        assert wait_time == 0.0
        assert limiter.request_count == 1

    def test_rate_limiting_enforced(self):
        """Test that rate limiter enforces delay."""
        limiter = RateLimiter(delay=0.5)

        # First request
        limiter.wait()

        # Second request immediately - should wait
        start = time.time()
        wait_time = limiter.wait()
        elapsed = time.time() - start

        assert wait_time >= 0.4  # Allow small timing variance
        assert elapsed >= 0.4
        assert limiter.request_count == 2

    def test_no_wait_if_enough_time_passed(self):
        """Test no wait if enough time has passed naturally."""
        limiter = RateLimiter(delay=0.2)

        limiter.wait()
        time.sleep(0.3)  # Wait longer than delay

        wait_time = limiter.wait()
        assert wait_time == 0.0

    def test_reset(self):
        """Test rate limiter reset."""
        limiter = RateLimiter(delay=1.0)
        limiter.wait()
        limiter.wait()

        assert limiter.request_count == 2

        limiter.reset()

        assert limiter.request_count == 0
        assert limiter.last_request_time is None

    def test_get_stats(self):
        """Test getting rate limiter statistics."""
        limiter = RateLimiter(delay=2.0)
        limiter.wait()

        stats = limiter.get_stats()

        assert stats["request_count"] == 1
        assert stats["delay"] == 2.0
        assert stats["last_request_time"] is not None


class TestLogging:
    """Tests for logging utilities."""

    def test_setup_logging_creates_log_file(self, tmp_path):
        """Test that setup_logging creates log file."""
        log_file = tmp_path / "test.log"

        setup_logging(level="INFO", log_file=str(log_file))

        # Log something
        logger = logging.getLogger(__name__)
        logger.info("Test message")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_setup_logging_console_only(self, tmp_path, caplog):
        """Test logging without file output."""
        setup_logging(level="INFO", log_file=None, console_output=True)

        logger = logging.getLogger(__name__)
        with caplog.at_level(logging.INFO):
            logger.info("Console test")

        assert "Console test" in caplog.text

    def test_different_log_levels(self, tmp_path):
        """Test different logging levels."""
        log_file = tmp_path / "levels.log"

        setup_logging(level="WARNING", log_file=str(log_file))
        logger = logging.getLogger(__name__)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        content = log_file.read_text()

        # DEBUG and INFO should not be logged
        assert "Debug message" not in content
        assert "Info message" not in content

        # WARNING and ERROR should be logged
        assert "Warning message" in content
        assert "Error message" in content
