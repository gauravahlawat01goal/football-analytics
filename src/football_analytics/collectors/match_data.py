"""Match data collector for downloading detailed fixture information.

Downloads all available includes for each fixture:
- ballCoordinates: Ball position tracking data
- events: Match events (passes, shots, tackles, etc.)
- lineups: Player lineups with positions
- formations: Team formations
- statistics: Match statistics
- participants: Team information
- scores: Score details

Strategy:
- One API call per include (cannot combine multiple includes)
- Save each include to separate JSON file
- Resume capability (skip existing files)
- Progress tracking

TODO (Framework Evolution):
    - Parallel downloads with asyncio (respect rate limits)
    - Automatic data validation after download
    - Checksum verification for data integrity
    - Incremental updates (only fetch new matches)
    - Smart scheduling (download during off-peak hours)
"""

from typing import Any

from football_analytics.utils import save_json

from .base import BaseCollector


class MatchDataCollector(BaseCollector):
    """
    Collect detailed match data for fixtures.

    Downloads all 7 available includes for each fixture:
    1. ballCoordinates - Ball tracking data
    2. events - Match events
    3. lineups - Player lineups
    4. formations - Team formations
    5. statistics - Match statistics
    6. participants - Team information
    7. scores - Score details

    Args:
        output_dir: Base directory for match data
        rate_limit_seconds: API rate limit delay
        resume: Skip existing files

    Example:
        >>> collector = MatchDataCollector()
        >>> fixtures = [{"fixture_id": 19134454, "name": "Ipswich vs Liverpool"}]
        >>> results = collector.collect_all_fixtures(fixtures)
        >>> results[19134454]["ballCoordinates"]
        True
    """

    # All available includes from SportsMonk API
    INCLUDES = [
        "ballCoordinates",
        "events",
        "lineups",
        "formations",
        "statistics",
        "participants",
        "scores",
    ]

    def collect_all_fixtures(
        self, fixtures_list: list[dict[str, Any]]
    ) -> dict[int, dict[str, bool]]:
        """
        Download all includes for all fixtures.

        Args:
            fixtures_list: List of fixture metadata (from FixtureCollector)

        Returns:
            Dictionary mapping fixture_id -> include_name -> success status

        Example:
            >>> collector = MatchDataCollector()
            >>> fixtures = [{"fixture_id": 123, "name": "Team A vs Team B"}]
            >>> results = collector.collect_all_fixtures(fixtures)
            >>> results[123]["ballCoordinates"]  # True if successful
            True
        """
        total_fixtures = len(fixtures_list)
        total_calls = total_fixtures * len(self.INCLUDES)
        completed_calls = 0

        self.logger.info(f"Starting collection for {total_fixtures} fixtures")
        self.logger.info(f"Total API calls needed: {total_calls}")
        self.logger.info(f"Estimated time: ~{(total_calls * 6) / 60:.1f} minutes")

        results = {}

        for idx, fixture in enumerate(fixtures_list, 1):
            fixture_id = fixture["fixture_id"]
            fixture_name = fixture.get("name", f"Fixture {fixture_id}")

            self.logger.info(
                f"\n[{idx}/{total_fixtures}] Collecting: {fixture_name} " f"(ID: {fixture_id})"
            )

            fixture_results = self._collect_fixture(fixture_id)
            results[fixture_id] = fixture_results

            # Update progress
            completed_calls += len(self.INCLUDES)
            progress = (completed_calls / total_calls) * 100

            successful = sum(fixture_results.values())
            failed = len(self.INCLUDES) - successful

            self.logger.info(
                f"  Progress: {progress:.1f}% ({completed_calls}/{total_calls}) | "
                f"Fixture: {successful} succeeded, {failed} failed"
            )

        # Final statistics
        self._log_collection_summary(results)

        return results

    def _collect_fixture(self, fixture_id: int) -> dict[str, bool]:
        """
        Collect all includes for a single fixture.

        Args:
            fixture_id: Fixture ID to collect

        Returns:
            Dictionary mapping include_name -> success status
        """
        # Create fixture directory
        fixture_dir = self.output_dir / str(fixture_id)
        fixture_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        for include_name in self.INCLUDES:
            output_path = fixture_dir / f"{include_name}.json"

            # Resume: skip if file exists
            if self.should_skip(output_path):
                results[include_name] = True
                continue

            try:
                # Rate limit
                self.rate_limiter.wait()

                # Fetch data
                data = self.client.get_fixture_details(fixture_id=fixture_id, include=include_name)
                self.increment_api_calls()

                # Save to file
                save_json(data, output_path)
                self.increment_files_created()

                results[include_name] = True
                self.logger.debug(f"  ✓ {include_name}")

            except Exception as e:
                self.logger.error(f"  ✗ {include_name}: {str(e)[:100]}")
                self.increment_errors()
                results[include_name] = False

        return results

    def collect_single_include(
        self, fixture_id: int, include_name: str, force: bool = False
    ) -> bool:
        """
        Collect a single include for a fixture.

        Useful for re-fetching failed includes or updating specific data.

        Args:
            fixture_id: Fixture ID
            include_name: Name of include to fetch
            force: If True, re-download even if file exists

        Returns:
            True if successful, False otherwise

        Example:
            >>> collector = MatchDataCollector()
            >>> success = collector.collect_single_include(
            ...     fixture_id=19134454,
            ...     include_name="ballCoordinates",
            ...     force=True
            ... )

        TODO (Framework Evolution):
            - Add validation after download
            - Compare with existing file to detect changes
            - Support partial updates (delta downloads)
        """
        if include_name not in self.INCLUDES:
            self.logger.error(
                f"Invalid include name: {include_name}. " f"Valid options: {self.INCLUDES}"
            )
            return False

        fixture_dir = self.output_dir / str(fixture_id)
        fixture_dir.mkdir(parents=True, exist_ok=True)
        output_path = fixture_dir / f"{include_name}.json"

        # Check if should skip
        if not force and self.should_skip(output_path):
            return True

        try:
            self.rate_limiter.wait()

            data = self.client.get_fixture_details(fixture_id=fixture_id, include=include_name)
            self.increment_api_calls()

            save_json(data, output_path)
            self.increment_files_created()

            self.logger.info(f"✓ Collected {include_name} for fixture {fixture_id}")
            return True

        except Exception as e:
            self.logger.error(f"✗ Failed to collect {include_name} for fixture {fixture_id}: {e}")
            self.increment_errors()
            return False

    def retry_failed_includes(
        self, results: dict[int, dict[str, bool]]
    ) -> dict[int, dict[str, bool]]:
        """
        Retry all failed includes from a previous collection.

        Args:
            results: Results dictionary from collect_all_fixtures()

        Returns:
            Updated results dictionary

        Example:
            >>> collector = MatchDataCollector()
            >>> results = collector.collect_all_fixtures(fixtures)
            >>> # Some failed, retry them
            >>> updated_results = collector.retry_failed_includes(results)
        """
        self.logger.info("Retrying failed includes...")

        retry_count = 0
        success_count = 0

        for fixture_id, includes in results.items():
            for include_name, success in includes.items():
                if not success:
                    retry_count += 1
                    self.logger.info(f"Retrying: fixture {fixture_id} / {include_name}")

                    new_success = self.collect_single_include(
                        fixture_id=fixture_id, include_name=include_name, force=True
                    )

                    results[fixture_id][include_name] = new_success
                    if new_success:
                        success_count += 1

        self.logger.info(f"Retry complete: {success_count}/{retry_count} now successful")

        return results

    def _log_collection_summary(self, results: dict[int, dict[str, bool]]) -> None:
        """Log summary statistics for collection."""
        total_fixtures = len(results)
        total_includes = total_fixtures * len(self.INCLUDES)

        successful_includes = sum(sum(includes.values()) for includes in results.values())

        failed_includes = total_includes - successful_includes
        success_rate = (successful_includes / total_includes * 100) if total_includes > 0 else 0

        stats = self.get_stats()

        self.logger.info("\n" + "=" * 60)
        self.logger.info("COLLECTION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Fixtures processed: {total_fixtures}")
        self.logger.info(f"Total includes: {total_includes}")
        self.logger.info(f"Successful: {successful_includes}")
        self.logger.info(f"Failed: {failed_includes}")
        self.logger.info(f"Success rate: {success_rate:.1f}%")
        self.logger.info(f"API calls made: {stats['api_calls']}")
        self.logger.info(f"Files created: {stats['files_created']}")
        self.logger.info(f"Files skipped: {stats['files_skipped']}")
        self.logger.info(f"Errors: {stats['errors']}")
        self.logger.info("=" * 60)
