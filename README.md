# 🎾 Tennis ELO Prediction Engine
[![CI/CD](https://github.com/yourusername/tennis-elo/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/tennis-elo/actions) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive tennis match prediction system using ELO ratings with surface-specific adjustments and sample-size calibrated seasonal form (yELO).

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Surface-Adjusted ELO**: Career ratings weighted by tournament surface (hard, clay, grass)
- **Sample-Size Calibrated yELO**: Seasonal form weighted by matches played
- **Robust Name Resolution**: Fuzzy matching, aliases, typo tolerance
- **ATP + WTA Support**: 895+ players, 50+ tournaments
- **Automated Updates**: Weekly data refresh from Tennis Abstract
- **Research-Based Formula**: Validated against betting markets

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/tennis-elo.git
cd tennis-elo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install package (development mode)
pip install -e .
```

### Basic Usage

```python
from tennis_elo import TennisPredictionEngine

# Initialize engine
engine = TennisPredictionEngine(db_path="data/tennis_elo.db")

# Predict a match
result = engine.predict_match("Alcaraz", "Sinner", "Wimbledon")

# Access results
print(f"Player 1: {result['match']['player1']['name']}")
print(f"Win Probability: {result['match']['player1']['win_percentage']}")
print(f"Favorite: {result['prediction']['favorite']}")
```

### Command Line

```bash
# Run predictions
python -m tennis_elo.prediction_engine

# Or use CLI entry point (after pip install)
tennis-predict
```

## Prediction Formula

### Base Win Probability
```
p = 1 / (1 + 10^((R_B - R_A)/400))
```

### Surface-Adjusted ELO
```
Adjusted = (1 - λ) × StandardELO + λ × SurfaceELO
```

Where λ (lambda) varies by surface and tour:

| Surface | ATP λ | WTA λ |
|---------|-------|-------|
| Hard    | 0.30  | 0.25  |
| Clay    | 0.40  | 0.35  |
| Grass   | 0.50  | 0.45  |

### yELO Weight Calibration

Seasonal form weight increases with matches played:

| Matches | yELO Weight | Reliability |
|---------|-------------|-------------|
| 0-2     | 0%          | Ignored     |
| 3-10    | 5-10%       | Early season|
| 10-20   | 10-18%      | Meaningful  |
| 20+     | 20-25%      | Full weight |

## Project Structure

```
tennis-elo/
├── src/
│   └── tennis_elo/
│       ├── __init__.py          # Package initialization
│       ├── database.py          # Database utility class
│       ├── name_resolver.py     # Player name resolution
│       └── prediction_engine.py # Main prediction engine
├── data/
│   └── tennis_elo.db           # SQLite database
├── scripts/
│   └── refresh_ratings.py      # Weekly data refresh
├── tests/
│   └── test_prediction.py      # Unit tests
├── docs/
│   └── api.md                  # API documentation
├── logs/                        # Refresh logs
├── backups/                     # Database backups
├── config/                      # Configuration files
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project metadata
├── README.md                   # This file
└── WORK_LOG.md                 # Development log
```

## API Reference

### TennisPredictionEngine

```python
engine = TennisPredictionEngine(db_path="data/tennis_elo.db")

# Predict match
result = engine.predict_match(player1, player2, tournament)

# Get player ELO
player_elo = engine.get_player_elo("Alcaraz")

# Get tournament info
tournament = engine.get_tournament_info("Wimbledon")

# Get confidence level
confidence = engine.get_confidence_level(0.65)  # "Moderate"
```

### PlayerNameResolver

```python
from tennis_elo import PlayerNameResolver

resolver = PlayerNameResolver()

# Resolve name
player = resolver.resolve_name("De Minaur", "ATP")

# Search players
results = resolver.search_players("Alex", limit=5)

# Add alias
resolver.add_alias("Zverev", "Sascha", "nickname")
```

### TennisELODatabase

```python
from tennis_elo import TennisELODatabase

db = TennisELODatabase()

# Get top players
top = db.get_top_elo(tour="ATP", limit=10)

# Get tournaments
tournaments = db.get_tournaments(surface="clay")

# Compare players
comparison = db.compare_players("Alcaraz", "Sinner")
```

## Data Sources

- **ELO Ratings**: [Tennis Abstract](https://tennisabstract.com)
- **Tournament Schedule**: ATP/WTA official calendars
- **Update Frequency**: Weekly (Sundays 2 AM)

## Running Tests

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=tennis_elo --cov-report=html
```

## Configuration

Edit `config/settings.py` (create from template):

```python
# Database path
DB_PATH = "data/tennis_elo.db"

# yELO configuration
YELO_CONFIG = {
    "min_matches": 3,
    "max_matches": 20,
    "max_weight_atp": 0.25,
    "max_weight_wta": 0.30,
}

# Surface weights
SURFACE_WEIGHTS = {
    "ATP": {"hard": 0.3, "clay": 0.4, "grass": 0.5},
    "WTA": {"hard": 0.25, "clay": 0.35, "grass": 0.45},
}
```

## Automated Refresh

```bash
# Manual refresh
python scripts/refresh_ratings.py

# Schedule with cron (Sundays 2 AM)
0 2 * * 0 cd /path/to/tennis-elo && python scripts/refresh_ratings.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this in your research:

```bibtex
@software{tennis_elo_2026,
  author = {Tennis ELO Project},
  title = {Tennis ELO Prediction Engine},
  year = {2026},
  url = {https://github.com/yourusername/tennis-elo}
}
```

## Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/tennis-elo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/tennis-elo/discussions)

## Acknowledgments

- [Tennis Abstract](https://tennisabstract.com) for ELO data and research
- [FiveThirtyEight](https://fivethirtyeight.com) for ELO methodology
- ATP and WTA for official tournament data
