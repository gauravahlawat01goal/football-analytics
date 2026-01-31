#!/usr/bin/env python3
"""
Simple script to verify SportsMonk API connection.
"""
import sys
import os
from pathlib import Path
import logging

# Add the src directory to the python path to allow imports if package is not installed
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
src_path = project_root / "src"
sys.path.append(str(src_path))

from football_analytics.api_client import SportsMonkClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting API connection check...")
    
    try:
        # Initialize client
        # This will raise ValueError if API key is missing
        client = SportsMonkClient()
        logger.info("✅ Client initialized successfully (API Key found)")
        
        # Test connection by making a simple request
        logger.info("Attempting to fetch leagues as a connection test...")
        leagues = client.get_leagues()
        
        # Check if we got a valid response
        # The structure of the response depends on the API, but usually contains 'data'
        if leagues:
            data_count = len(leagues.get('data', [])) if isinstance(leagues, dict) else len(leagues)
            logger.info(f"✅ API call successful! Retrieved {data_count} leagues.")
            logger.info("API Connection is working correctly.")
        else:
            logger.warning("⚠️ API call returned empty response.")
            
    except ValueError as e:
        logger.error(f"❌ Configuration Error: {e}")
        logger.info("Please ensure your .env file is set up correctly with SPORTSMONK_API_KEY")
    except Exception as e:
        logger.error(f"❌ API Connection Error: {e}")
        logger.info("Please check your internet connection and API key validity.")

if __name__ == "__main__":
    main()
