#!/usr/bin/env python3
"""
Sample script demonstrating the data processing pipeline.

This script shows how to use the processing modules to:
1. Validate data quality
2. Parse ball coordinates and events
3. Link events to coordinates
4. Extract player database
5. Generate processed datasets

Usage:
    python scripts/03_process_match_data.py --fixture-id 18841624
    python scripts/03_process_match_data.py --all  # Process all fixtures
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from football_analytics.processors import (
    BallCoordinateProcessor,
    EventProcessor,
    FormationParser,
    PlayerIDExtractor,
)
from football_analytics.utils import DataQualityValidator, setup_logging

logger = setup_logging(__name__)


def process_single_fixture(fixture_id: int):
    """
    Process a single fixture through the complete pipeline.
    
    Args:
        fixture_id: Fixture ID to process
    """
    logger.info("=" * 80)
    logger.info(f"PROCESSING FIXTURE {fixture_id}")
    logger.info("=" * 80)
    
    # Step 1: Validate data quality
    logger.info("\n1. Validating data quality...")
    validator = DataQualityValidator()
    quality_report = validator.validate_fixture(fixture_id)
    
    logger.info(f"   Status: {quality_report['status']}")
    logger.info(f"   Quality Score: {quality_report['quality_score']}/100")
    
    if quality_report['status'] == 'FAIL':
        logger.error(f"   ❌ Data quality check failed!")
        for issue in quality_report['issues']:
            logger.error(f"      - {issue}")
        return False
    
    if quality_report['warnings']:
        for warning in quality_report['warnings']:
            logger.warning(f"   ⚠️  {warning}")
    
    # Step 2: Parse ball coordinates
    logger.info("\n2. Processing ball coordinates...")
    ball_processor = BallCoordinateProcessor()
    coords_df = ball_processor.parse_coordinates(fixture_id)
    
    logger.info(f"   ✅ Parsed {len(coords_df)} ball coordinates")
    logger.info(f"   Zones: {coords_df['pitch_zone'].value_counts().to_dict()}")
    
    # Step 3: Parse events
    logger.info("\n3. Processing events...")
    event_processor = EventProcessor()
    events_df = event_processor.parse_events(fixture_id)
    
    logger.info(f"   ✅ Parsed {len(events_df)} events")
    logger.info(f"   Categories: {events_df['event_category'].value_counts().to_dict()}")
    
    # Step 4: Link events to coordinates
    logger.info("\n4. Linking events to ball coordinates...")
    coords_df = ball_processor.solve_timestamp_problem(coords_df, events_df)
    events_df = event_processor.link_to_ball_coordinates(events_df, coords_df)
    
    linked = events_df['ball_x'].notna().sum()
    link_pct = linked / len(events_df) * 100 if len(events_df) > 0 else 0
    logger.info(f"   ✅ Linked {linked}/{len(events_df)} events ({link_pct:.1f}%)")
    
    # Step 5: Infer possession
    logger.info("\n5. Inferring possession...")
    coords_df = ball_processor.infer_possession(coords_df, events_df)
    
    inferred = coords_df['possession_team'].notna().sum()
    infer_pct = inferred / len(coords_df) * 100 if len(coords_df) > 0 else 0
    logger.info(f"   ✅ Inferred possession for {inferred}/{len(coords_df)} coordinates ({infer_pct:.1f}%)")
    
    # Step 6: Parse formations and lineups
    logger.info("\n6. Processing formations and lineups...")
    formation_parser = FormationParser()
    lineups_df = formation_parser.parse_lineups(fixture_id)
    formations_df = formation_parser.parse_formations(fixture_id)
    
    logger.info(f"   ✅ Parsed {len(lineups_df)} lineup entries")
    logger.info(f"   ✅ Parsed {len(formations_df)} formation records")
    
    # Step 7: Save processed data
    logger.info("\n7. Saving processed data...")
    output_dir = Path("data/processed/fixtures") / str(fixture_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    coords_df.to_parquet(output_dir / "ball_coordinates.parquet", index=False)
    events_df.to_csv(output_dir / "events.csv", index=False)
    lineups_df.to_csv(output_dir / "lineups.csv", index=False)
    formations_df.to_csv(output_dir / "formations.csv", index=False)
    
    logger.info(f"   ✅ Saved to {output_dir}")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"✅ FIXTURE {fixture_id} PROCESSED SUCCESSFULLY")
    logger.info("=" * 80)
    
    return True


def process_all_fixtures():
    """Process all fixtures found in data/raw directory."""
    logger.info("Processing all fixtures...")
    
    data_dir = Path("data/raw")
    fixture_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.isdigit()]
    fixture_ids = [int(d.name) for d in fixture_dirs]
    
    logger.info(f"Found {len(fixture_ids)} fixtures to process")
    
    success_count = 0
    fail_count = 0
    
    for i, fixture_id in enumerate(fixture_ids, 1):
        logger.info(f"\n[{i}/{len(fixture_ids)}] Processing fixture {fixture_id}...")
        
        try:
            if process_single_fixture(fixture_id):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to process fixture {fixture_id}: {e}")
            fail_count += 1
            continue
    
    logger.info("\n" + "=" * 80)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total fixtures: {len(fixture_ids)}")
    logger.info(f"✅ Successful: {success_count}")
    logger.info(f"❌ Failed: {fail_count}")
    logger.info("=" * 80)


def extract_player_database():
    """Extract complete player database from all fixtures."""
    logger.info("Extracting player database...")
    
    data_dir = Path("data/raw")
    fixture_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.isdigit()]
    fixture_ids = [int(d.name) for d in fixture_dirs]
    
    logger.info(f"Processing {len(fixture_ids)} fixtures...")
    
    extractor = PlayerIDExtractor()
    players_df = extractor.extract_all_players(fixture_ids, team_name="Liverpool")
    
    # Find key players
    key_players = extractor.find_key_players(players_df)
    
    # Save databases
    extractor.save_player_database(players_df)
    extractor.save_key_player_ids(key_players)
    
    logger.info("✅ Player database extraction complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Process football match data through the complete pipeline"
    )
    parser.add_argument(
        "--fixture-id",
        type=int,
        help="Process a single fixture by ID"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all fixtures"
    )
    parser.add_argument(
        "--extract-players",
        action="store_true",
        help="Extract player database from all fixtures"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate data quality (don't process)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.fixture_id, args.all, args.extract_players]):
        parser.error("Must specify --fixture-id, --all, or --extract-players")
    
    try:
        if args.validate_only:
            # Just validate
            validator = DataQualityValidator()
            
            if args.fixture_id:
                report = validator.validate_fixture(args.fixture_id)
                logger.info(f"Validation: {report['status']} (Score: {report['quality_score']}/100)")
            elif args.all:
                data_dir = Path("data/raw")
                fixture_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.isdigit()]
                fixture_ids = [int(d.name) for d in fixture_dirs]
                results_df = validator.validate_multiple_fixtures(fixture_ids)
                validator.save_validation_report(results_df)
        
        elif args.extract_players:
            extract_player_database()
        
        elif args.fixture_id:
            success = process_single_fixture(args.fixture_id)
            sys.exit(0 if success else 1)
        
        elif args.all:
            process_all_fixtures()
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Processing interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
