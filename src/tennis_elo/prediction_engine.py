#!/usr/bin/env python3
"""Tennis Match Prediction Engine v3
Uses ELO ratings with surface-specific adjustments and sample-size calibrated yELO
Integrated with robust name resolution system
"""

import sqlite3
import math
from datetime import datetime
from typing import Dict, Optional, Any
from .name_resolver import PlayerNameResolver

DB_PATH = "/a0/usr/projects/tennis-elo/tennis_elo.db"


class TennisPredictionEngine:
    """
    Tennis match prediction engine using ELO ratings.
    v3: Integrated with PlayerNameResolver for robust name lookups
    """

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.resolver = PlayerNameResolver(db_path)

        # Surface lambda weights based on research
        self.surface_weights = {
            "ATP": {"hard": 0.3, "clay": 0.4, "grass": 0.5},
            "WTA": {"hard": 0.25, "clay": 0.35, "grass": 0.45},
        }

        # Tournament category multipliers
        self.category_multipliers = {
            "Grand Slam": 1.2,
            "ATP Finals": 1.1,
            "WTA Finals": 1.1,
            "Masters 1000": 1.15,
            "WTA 1000": 1.15,
            "ATP 500": 1.0,
            "WTA 500": 1.0,
            "ATP 250": 0.9,
            "WTA 250": 0.9,
            "default": 1.0,
        }

        # yELO configuration
        self.yelo_config = {
            "min_matches": 3,
            "max_matches": 20,
            "max_weight_atp": 0.25,
            "max_weight_wta": 0.30,
            "curve_type": "sigmoid",
        }

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def resolve_player(self, name: str, tour: Optional[str] = None) -> Optional[Dict]:
        """Resolve player name using name resolver"""
        return self.resolver.resolve_name(name, tour)

    def calculate_yelo_weight(self, matches_played: int, tour: str) -> float:
        """Calculate yELO weight based on sample size"""
        if matches_played < self.yelo_config["min_matches"]:
            return 0.0

        max_weight = (
            self.yelo_config["max_weight_wta"]
            if tour == "WTA"
            else self.yelo_config["max_weight_atp"]
        )

        min_m = self.yelo_config["min_matches"]
        max_m = self.yelo_config["max_matches"]

        normalized = (matches_played - min_m) / (max_m - min_m)
        normalized = max(0, min(1, normalized))

        k = 0.3
        sigmoid_input = k * (normalized * 10 - 5)
        weight = max_weight * (1 / (1 + math.exp(-sigmoid_input)))

        return min(weight, max_weight)

    def get_player_elo(self, player_name: str, tour: Optional[str] = None) -> Optional[Dict]:
        """Get player's current ELO ratings using name resolver"""
        player = self.resolve_player(player_name, tour)
        if not player:
            return None

        conn = self._conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT p.player_name, p.tour, e.overall_elo, e.hard_elo,
                   e.clay_elo, e.grass_elo, e.peak_elo, e.atp_rank
            FROM elo_ratings e
            JOIN players p ON e.player_id = p.player_id
            WHERE p.player_id = ?
            AND e.rating_date = (SELECT MAX(rating_date) FROM elo_ratings)
        """,
            (player["player_id"],),
        )

        row = cur.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_player_yelo(self, player_name: str, tour: Optional[str] = None) -> Optional[Dict]:
        """Get player's current seasonal yELO using name resolver"""
        player = self.resolve_player(player_name, tour)
        if not player:
            return None

        conn = self._conn()
        cur = conn.cursor()
        current_year = datetime.now().year

        cur.execute(
            """
            SELECT p.player_name, p.tour, y.yelo_rating, y.wins, y.losses,
                   y.season_year, (y.wins + y.losses) as matches_played
            FROM yelo_ratings y
            JOIN players p ON y.player_id = p.player_id
            WHERE p.player_id = ? AND y.season_year = ?
        """,
            (player["player_id"], current_year),
        )

        row = cur.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_tournament_info(self, tournament_name: str) -> Optional[Dict]:
        """Get tournament information"""
        conn = self._conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT * FROM tournaments
            WHERE name LIKE ?
            ORDER BY start_date DESC
            LIMIT 1
        """,
            (f"%{tournament_name}%",),
        )

        row = cur.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def calculate_surface_adjusted_elo(
        self, player_elo: Dict, surface: str, tour: str, category: str = "default"
    ) -> tuple:
        """Calculate surface-adjusted ELO"""
        base_lambda = self.surface_weights.get(tour, {}).get(surface, 0.3)
        category_mult = self.category_multipliers.get(category, 1.0)
        effective_lambda = min(base_lambda * category_mult, 0.6)

        surface_elo_map = {
            "hard": player_elo.get("hard_elo", player_elo["overall_elo"]),
            "clay": player_elo.get("clay_elo", player_elo["overall_elo"]),
            "grass": player_elo.get("grass_elo", player_elo["overall_elo"]),
        }

        surface_elo = surface_elo_map.get(surface, player_elo["overall_elo"])
        adjusted_elo = (1 - effective_lambda) * player_elo[
            "overall_elo"
        ] + effective_lambda * surface_elo

        return adjusted_elo, effective_lambda

    def calculate_win_probability(self, elo_a: float, elo_b: float) -> float:
        """Calculate win probability using standard ELO formula"""
        return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

    def predict_match(
        self, player1_name: str, player2_name: str, tournament_name: str
    ) -> Optional[Dict]:
        """Predict match outcome with sample-size calibrated yELO"""
        tournament = self.get_tournament_info(tournament_name)
        if not tournament:
            return {"error": f"Tournament '{tournament_name}' not found"}

        surface = tournament["surface"]
        category = tournament["category"]
        tour = tournament["tour"]

        player1_elo = self.get_player_elo(player1_name, None)
        player2_elo = self.get_player_elo(player2_name, None)

        if not player1_elo:
            return {"error": f"Player '{player1_name}' not found"}
        if not player2_elo:
            return {"error": f"Player '{player2_name}' not found"}

        player1_yelo = self.get_player_yelo(player1_name, None)
        player2_yelo = self.get_player_yelo(player2_name, None)

        p1_surface_elo, p1_lambda = self.calculate_surface_adjusted_elo(
            player1_elo, surface, tour, category
        )
        p2_surface_elo, p2_lambda = self.calculate_surface_adjusted_elo(
            player2_elo, surface, tour, category
        )

        base_p1_prob = self.calculate_win_probability(p1_surface_elo, p2_surface_elo)

        p1_yelo_weight = 0.0
        p2_yelo_weight = 0.0
        p1_yelo_prob = None

        if player1_yelo and player2_yelo:
            p1_matches = player1_yelo.get("matches_played", 0)
            p2_matches = player2_yelo.get("matches_played", 0)

            p1_yelo_weight = self.calculate_yelo_weight(p1_matches, tour)
            p2_yelo_weight = self.calculate_yelo_weight(p2_matches, tour)

            avg_yelo_weight = (p1_yelo_weight + p2_yelo_weight) / 2

            p1_yelo_prob = self.calculate_win_probability(
                player1_yelo["yelo_rating"], player2_yelo["yelo_rating"]
            )

            final_p1_prob = (1 - avg_yelo_weight) * base_p1_prob + avg_yelo_weight * p1_yelo_prob
        else:
            final_p1_prob = base_p1_prob

        p2_final_prob = 1 - final_p1_prob
        elo_diff = abs(p1_surface_elo - p2_surface_elo)

        if final_p1_prob > 0.5:
            favorite = player1_elo["player_name"]
            underdog = player2_elo["player_name"]
        else:
            favorite = player2_elo["player_name"]
            underdog = player1_elo["player_name"]

        return {
            "match": {
                "player1": {
                    "name": player1_elo["player_name"],
                    "tour": player1_elo["tour"],
                    "overall_elo": player1_elo["overall_elo"],
                    "surface_elo": player1_elo.get(f"{surface}_elo", player1_elo["overall_elo"]),
                    "adjusted_elo": round(p1_surface_elo, 1),
                    "yelo": player1_yelo["yelo_rating"] if player1_yelo else None,
                    "yelo_matches": player1_yelo.get("matches_played", 0) if player1_yelo else 0,
                    "yelo_weight": round(p1_yelo_weight, 3) if player1_yelo else 0,
                    "win_probability": round(final_p1_prob, 4),
                    "win_percentage": f"{final_p1_prob:.1%}",
                },
                "player2": {
                    "name": player2_elo["player_name"],
                    "tour": player2_elo["tour"],
                    "overall_elo": player2_elo["overall_elo"],
                    "surface_elo": player2_elo.get(f"{surface}_elo", player2_elo["overall_elo"]),
                    "adjusted_elo": round(p2_surface_elo, 1),
                    "yelo": player2_yelo["yelo_rating"] if player2_yelo else None,
                    "yelo_matches": player2_yelo.get("matches_played", 0) if player2_yelo else 0,
                    "yelo_weight": round(p2_yelo_weight, 3) if player2_yelo else 0,
                    "win_probability": round(p2_final_prob, 4),
                    "win_percentage": f"{p2_final_prob:.1%}",
                },
            },
            "tournament": {
                "name": tournament["name"],
                "surface": surface,
                "category": category,
                "location": f"{tournament['location']}, {tournament['country']}",
            },
            "prediction": {
                "favorite": favorite,
                "underdog": underdog,
                "elo_difference": round(elo_diff, 1),
                "surface_weight_lambda": round((p1_lambda + p2_lambda) / 2, 3),
                "yelo_blend_weight": round(
                    avg_yelo_weight if player1_yelo and player2_yelo else 0, 3
                ),
                "formula": "Final = (1 - w) × SurfaceELO_prob + w × yELO_prob",
                "yelo_weight_formula": "w = max_weight × sigmoid(matches)",
                "sample_size_note": "yELO weight calibrated: 0% at <3 matches, max at 20+ matches",
            },
        }

    def get_confidence_level(self, win_prob: float) -> str:
        """Get confidence level"""
        prob = max(win_prob, 1 - win_prob)
        if prob >= 0.75:
            return "Very High"
        elif prob >= 0.65:
            return "High"
        elif prob >= 0.55:
            return "Moderate"
        else:
            return "Low (Toss-up)"


if __name__ == "__main__":
    engine = TennisPredictionEngine()

    print("=" * 70)
    print("TENNIS PREDICTION ENGINE v3")
    print("With Name Resolution & Sample-Size Calibrated yELO")
    print("=" * 70)

    # Test with previously problematic names
    print("\n🎾 Test: De Minaur vs Fils at Miami Open")
    result = engine.predict_match("De Minaur", "Fils", "Miami Open")

    if result is None:
        print("Error: Could not get prediction result")
    elif "error" not in result:
        p1, p2 = result["match"]["player1"], result["match"]["player2"]
        print(
            f"\n{p1['name']}: {p1['win_percentage']} (yELO: {p1['yelo']}, {p1['yelo_matches']} matches)"
        )
        print(
            f"{p2['name']}: {p2['win_percentage']} (yELO: {p2['yelo']}, {p2['yelo_matches']} matches)"
        )
        print(f"Favorite: {result['prediction']['favorite']}")
    else:
        print(f"Error: {result['error']}")

    print("\n" + "=" * 70)

    def get_confidence_label(self, probability):
        """Get human-readable confidence label from probability.

        Args:
            probability: Win probability (0.0-1.0)

        Returns:
            str: Confidence label (Low, Moderate, High, Very High)
        """
        diff = abs(probability - 0.5) * 2  # Normalize to 0-1

        if diff < 0.1:
            return "Toss-up"
        elif diff < 0.2:
            return "Low"
        elif diff < 0.4:
            return "Moderate"
        elif diff < 0.6:
            return "High"
        else:
            return "Very High"
