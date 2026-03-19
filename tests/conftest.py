"""Test fixtures for Tennis ELO tests"""

import pytest
import sqlite3
import sys

sys.path.insert(0, "src")

from tennis_elo import TennisPredictionEngine, PlayerNameResolver


def create_test_db(path=None):
    """Create test database with sample data"""
    if path:
        conn = sqlite3.connect(path)
    else:
        conn = sqlite3.connect(":memory:")

    cur = conn.cursor()

    # Create schema
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY,
            player_name TEXT NOT NULL,
            tour TEXT NOT NULL,
            country TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS elo_ratings (
            rating_id INTEGER PRIMARY KEY,
            player_id INTEGER,
            overall_elo REAL DEFAULT 1500,
            hard_elo REAL DEFAULT 1500,
            clay_elo REAL DEFAULT 1500,
            grass_elo REAL DEFAULT 1500,
            peak_elo REAL DEFAULT 1500,
            atp_rank INTEGER,
            rating_date TEXT,
            FOREIGN KEY (player_id) REFERENCES players
        );
        
        CREATE TABLE IF NOT EXISTS yelo_ratings (
            yelo_id INTEGER PRIMARY KEY,
            player_id INTEGER,
            yelo_rating REAL DEFAULT 1500,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            season_year INTEGER,
            FOREIGN KEY (player_id) REFERENCES players
        );
        
        CREATE TABLE IF NOT EXISTS tournaments (
            tournament_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            tour TEXT,
            surface TEXT,
            category TEXT,
            location TEXT,
            country TEXT,
            start_date TEXT,
            end_date TEXT
        );
        
        CREATE TABLE IF NOT EXISTS player_aliases (
            alias_id INTEGER PRIMARY KEY,
            player_id INTEGER,
            alias_name TEXT NOT NULL,
            alias_type TEXT DEFAULT 'manual',
            source TEXT DEFAULT 'manual',
            FOREIGN KEY (player_id) REFERENCES players
        );
    """)

    # Insert test players (5 columns)
    test_players = [
        (1, "Carlos Alcaraz", "ATP", "Spain", "2026-01-01"),
        (2, "Jannik Sinner", "ATP", "Italy", "2026-01-01"),
        (3, "Novak Djokovic", "ATP", "Serbia", "2026-01-01"),
        (4, "Aryna Sabalenka", "WTA", "Belarus", "2026-01-01"),
        (5, "Iga Swiatek", "WTA", "Poland", "2026-01-01"),
    ]
    cur.executemany("INSERT OR IGNORE INTO players VALUES (?, ?, ?, ?, ?)", test_players)

    # Insert test ELO ratings
    test_elos = [
        (1, 1, 2580.5, 2560.0, 2600.0, 2520.0, 2620.0, 2, "2026-03-15"),
        (2, 2, 2550.0, 2540.0, 2520.0, 2580.0, 2570.0, 1, "2026-03-15"),
        (3, 3, 2500.0, 2510.0, 2490.0, 2530.0, 2550.0, 3, "2026-03-15"),
        (4, 4, 2400.0, 2420.0, 2380.0, 2390.0, 2450.0, 5, "2026-03-15"),
        (5, 5, 2450.0, 2430.0, 2470.0, 2400.0, 2500.0, 1, "2026-03-15"),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO elo_ratings 
        (rating_id, player_id, overall_elo, hard_elo, clay_elo, grass_elo, peak_elo, atp_rank, rating_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        test_elos,
    )

    # Insert test yELO ratings
    test_yelos = [
        (1, 1, 2600.0, 15, 3, 2026),
        (2, 2, 2550.0, 12, 5, 2026),
        (3, 3, 2480.0, 8, 4, 2026),
        (4, 4, 2380.0, 18, 5, 2026),
        (5, 5, 2420.0, 20, 3, 2026),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO yelo_ratings (yelo_id, player_id, yelo_rating, wins, losses, season_year)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        test_yelos,
    )

    # Insert test tournaments
    test_tournaments = [
        (1, "Wimbledon", "ATP", "grass", "Grand Slam", "London", "UK", "2026-06-30", "2026-07-13"),
        (
            2,
            "French Open",
            "ATP",
            "clay",
            "Grand Slam",
            "Paris",
            "France",
            "2026-05-25",
            "2026-06-08",
        ),
        (3, "US Open", "ATP", "hard", "Grand Slam", "New York", "USA", "2026-08-25", "2026-09-08"),
        (
            4,
            "Australian Open",
            "ATP",
            "hard",
            "Grand Slam",
            "Melbourne",
            "Australia",
            "2026-01-12",
            "2026-01-26",
        ),
        (
            5,
            "Indian Wells Open",
            "ATP",
            "hard",
            "Masters 1000",
            "Indian Wells",
            "USA",
            "2026-03-05",
            "2026-03-16",
        ),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO tournaments 
        (tournament_id, name, tour, surface, category, location, country, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        test_tournaments,
    )

    # Insert test aliases (including Alcaraz short form)
    test_aliases = [
        (1, 3, "Djoko", "nickname", "manual"),
        (2, 3, "Nole", "nickname", "manual"),
        (3, 1, "Carlitos", "nickname", "manual"),
        (4, 2, "Jan", "nickname", "manual"),
        (5, 1, "Alcaraz", "short_form", "auto"),
        (6, 2, "Sinner", "short_form", "auto"),
        (7, 3, "Djokovic", "short_form", "auto"),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO player_aliases (alias_id, player_id, alias_name, alias_type, source)
        VALUES (?, ?, ?, ?, ?)
    """,
        test_aliases,
    )

    conn.commit()
    return conn


@pytest.fixture
def test_db_path(tmp_path):
    """Fixture providing path to temporary test database"""
    db_path = tmp_path / "test_tennis_elo.db"
    create_test_db(str(db_path))
    return str(db_path)


@pytest.fixture
def resolver(test_db_path):
    """Fixture for PlayerNameResolver with test database"""
    return PlayerNameResolver(db_path=test_db_path)


@pytest.fixture
def engine(test_db_path):
    """Fixture for TennisPredictionEngine with test database"""
    return TennisPredictionEngine(db_path=test_db_path)
