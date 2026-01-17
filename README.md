# Football Analytics

Football data analysis for European leagues using the SportsMonk API.

## Overview

This project provides tools and utilities for fetching, processing, and analyzing football data from European leagues using the [SportsMonk API](https://www.sportmonks.com/). The goal is to enable data-driven insights into team performance, player statistics, and match outcomes.

## Features

- Fetch data from SportsMonk API for multiple European leagues
- Process and transform raw API data into structured formats
- Calculate team and player statistics
- Export data to various formats (CSV, JSON, Parquet)
- Data visualization and analysis capabilities

## Project Structure

```
football-analytics/
├── src/
│   └── football_analytics/
│       ├── __init__.py
│       ├── api_client.py       # SportsMonk API client
│       └── data_processor.py   # Data processing utilities
├── tests/                      # Unit tests
├── notebooks/                  # Jupyter notebooks for analysis
├── data/
│   ├── raw/                   # Raw data from API
│   └── processed/             # Processed datasets
├── docs/                      # Documentation
├── pyproject.toml             # Project dependencies and configuration
└── README.md
```

## Setup

### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)
- SportsMonk API key ([Get one here](https://www.sportmonks.com/))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/football-analytics.git
cd football-analytics
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. Add your SportsMonk API key to `.env`:
```
SPORTSMONK_API_KEY=your_api_key_here
```

## Usage

### Basic API Client Usage

```python
from football_analytics.api_client import SportsMonkClient

# Initialize the client
client = SportsMonkClient()

# Fetch all leagues
leagues = client.get_leagues()

# Fetch teams for a specific league
teams = client.get_teams(league_id=271)  # Premier League

# Fetch fixtures
fixtures = client.get_fixtures(league_id=271)
```

### Data Processing

```python
from football_analytics.data_processor import DataProcessor

# Convert fixtures to DataFrame
processor = DataProcessor()
fixtures_df = processor.fixtures_to_dataframe(fixtures)

# Calculate team statistics
stats = processor.calculate_team_stats(fixtures_df, team_id=1)
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

This project uses Black and Ruff for code formatting and linting:

```bash
# Format code with Black
poetry run black src/ tests/

# Lint and auto-fix with Ruff
poetry run ruff check --fix src/ tests/
```

### Project Standards

- Line length: 100 characters
- Python version: 3.10+
- Type hints encouraged for all functions
- Follow PEP 8 style guidelines

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Format your code with Black and Ruff
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Data provided by [SportsMonk API](https://www.sportmonks.com/)
- European football leagues and organizations

## Contact

For questions or suggestions, please open an issue on GitHub.
