"""Tennis ELO Database Utility Module - ATP + WTA Support"""

import sqlite3
from datetime import datetime

DB_PATH = "/a0/usr/projects/tennis-elo/tennis_elo.db"


class TennisELODatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _conn(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    def get_top_elo(self, tour=None, limit=10):
        """Get top players by career ELO. tour: 'ATP', 'WTA', or None for both"""
        conn = self._conn()
        cur = conn.cursor()
        if tour:
            cur.execute(
                """SELECT p.player_name, p.tour, e.overall_elo, e.hard_elo, e.clay_elo, e.grass_elo, e.atp_rank
                FROM elo_ratings e JOIN players p ON e.player_id = p.player_id
                WHERE p.tour = ? AND e.rating_date = (SELECT MAX(rating_date) FROM elo_ratings)
                ORDER BY e.overall_elo DESC LIMIT ?""",
                (tour, limit),
            )
        else:
            cur.execute(
                """SELECT p.player_name, p.tour, e.overall_elo, e.hard_elo, e.clay_elo, e.grass_elo, e.atp_rank
                FROM elo_ratings e JOIN players p ON e.player_id = p.player_id
                WHERE e.rating_date = (SELECT MAX(rating_date) FROM elo_ratings)
                ORDER BY e.overall_elo DESC LIMIT ?""",
                (limit,),
            )
        res = [dict(x) for x in cur.fetchall()]
        conn.close()
        return res

    def get_top_yelo(self, tour=None, year=None, limit=10):
        """Get top players by seasonal yELO. tour: 'ATP', 'WTA', or None for both"""
        if year is None:
            year = datetime.now().year
        conn = self._conn()
        cur = conn.cursor()
        if tour:
            cur.execute(
                """SELECT p.player_name, p.tour, y.yelo_rating, y.wins, y.losses
                FROM yelo_ratings y JOIN players p ON y.player_id = p.player_id
                WHERE y.season_year = ? AND p.tour = ?
                ORDER BY y.yelo_rating DESC LIMIT ?""",
                (year, tour, limit),
            )
        else:
            cur.execute(
                """SELECT p.player_name, p.tour, y.yelo_rating, y.wins, y.losses
                FROM yelo_ratings y JOIN players p ON y.player_id = p.player_id
                WHERE y.season_year = ?
                ORDER BY y.yelo_rating DESC LIMIT ?""",
                (year, limit),
            )
        res = [dict(x) for x in cur.fetchall()]
        conn.close()
        return res

    def get_player(self, name, tour=None):
        """Search player by name. Optionally filter by tour"""
        conn = self._conn()
        cur = conn.cursor()
        if tour:
            cur.execute(
                """SELECT p.player_name, p.tour, e.overall_elo, e.hard_elo, e.clay_elo, e.grass_elo, e.peak_elo, e.atp_rank
                FROM elo_ratings e JOIN players p ON e.player_id = p.player_id
                WHERE p.player_name LIKE ? AND p.tour = ?
                ORDER BY e.overall_elo DESC LIMIT 1""",
                (f"%{name}%", tour),
            )
        else:
            cur.execute(
                """SELECT p.player_name, p.tour, e.overall_elo, e.hard_elo, e.clay_elo, e.grass_elo, e.peak_elo, e.atp_rank
                FROM elo_ratings e JOIN players p ON e.player_id = p.player_id
                WHERE p.player_name LIKE ?
                ORDER BY e.overall_elo DESC LIMIT 1""",
                (f"%{name}%",),
            )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_player_yelo(self, name, tour=None, year=None):
        """Get player seasonal yELO rating"""
        if year is None:
            year = datetime.now().year
        conn = self._conn()
        cur = conn.cursor()
        if tour:
            cur.execute(
                """SELECT p.player_name, p.tour, y.yelo_rating, y.wins, y.losses, y.season_year
                FROM yelo_ratings y JOIN players p ON y.player_id = p.player_id
                WHERE p.player_name LIKE ? AND p.tour = ? AND y.season_year = ?
                ORDER BY y.yelo_rating DESC LIMIT 1""",
                (f"%{name}%", tour, year),
            )
        else:
            cur.execute(
                """SELECT p.player_name, p.tour, y.yelo_rating, y.wins, y.losses, y.season_year
                FROM yelo_ratings y JOIN players p ON y.player_id = p.player_id
                WHERE p.player_name LIKE ? AND y.season_year = ?
                ORDER BY y.yelo_rating DESC LIMIT 1""",
                (f"%{name}%", year),
            )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_stats(self, tour=None):
        """Get database statistics. Optionally filter by tour"""
        conn = self._conn()
        cur = conn.cursor()
        if tour:
            cur.execute("SELECT COUNT(*) FROM players WHERE tour = ?", (tour,))
            players = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM elo_ratings WHERE tour = ?", (tour,))
            elo = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM yelo_ratings WHERE tour = ?", (tour,))
            yelo = cur.fetchone()[0]
            cur.execute("SELECT MAX(overall_elo) FROM elo_ratings WHERE tour = ?", (tour,))
            max_elo = cur.fetchone()[0]
            cur.execute("SELECT MAX(yelo_rating) FROM yelo_ratings WHERE tour = ?", (tour,))
            max_yelo = cur.fetchone()[0]
        else:
            cur.execute("SELECT COUNT(*) FROM players")
            players = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM elo_ratings")
            elo = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM yelo_ratings")
            yelo = cur.fetchone()[0]
            cur.execute("SELECT MAX(overall_elo) FROM elo_ratings")
            max_elo = cur.fetchone()[0]
            cur.execute("SELECT MAX(yelo_rating) FROM yelo_ratings")
            max_yelo = cur.fetchone()[0]
        conn.close()
        return {
            "players": players,
            "elo_ratings": elo,
            "yelo_ratings": yelo,
            "max_elo": max_elo,
            "max_yelo": max_yelo,
        }

    def win_prob(self, elo1, elo2):
        """Calculate win probability between two ELO ratings"""
        return 1 / (1 + 10 ** ((elo2 - elo1) / 400))

    def compare_players(self, name1, name2):
        """Compare two players career ELO and calculate win probability"""
        p1 = self.get_player(name1)
        p2 = self.get_player(name2)
        if not p1 or not p2:
            return None
        prob1 = self.win_prob(p1["overall_elo"], p2["overall_elo"])
        return {
            "player1": {"name": p1["player_name"], "tour": p1["tour"], "elo": p1["overall_elo"]},
            "player2": {"name": p2["player_name"], "tour": p2["tour"], "elo": p2["overall_elo"]},
            "win_probability": {
                p1["player_name"]: f"{prob1:.2%}",
                p2["player_name"]: f"{1 - prob1:.2%}",
            },
        }

    def get_tournaments(self, tour=None, surface=None, category=None):
        """Get tournaments with optional filters"""
        conn = self._conn()
        cur = conn.cursor()
        query = "SELECT * FROM tournaments WHERE 1=1"
        params = []

        if tour:
            query += " AND tour = ?"
            params.append(tour)
        if surface:
            query += " AND surface = ?"
            params.append(surface)
        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY start_date"
        cur.execute(query, params)
        res = [dict(x) for x in cur.fetchall()]
        conn.close()
        return res

    def get_tournament_by_name(self, name):
        """Search tournament by name"""
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM tournaments WHERE name LIKE ? ORDER BY start_date DESC LIMIT 1",
            (f"%{name}%",),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_surface_stats(self, tour=None):
        """Get player ELO stats by surface type"""
        conn = self._conn()
        cur = conn.cursor()

        if tour:
            cur.execute(
                """
                SELECT p.player_name, e.overall_elo, e.hard_elo, e.clay_elo, e.grass_elo
                FROM elo_ratings e JOIN players p ON e.player_id = p.player_id
                WHERE p.tour = ? AND e.rating_date = (SELECT MAX(rating_date) FROM elo_ratings)
                ORDER BY e.overall_elo DESC LIMIT 20
            """,
                (tour,),
            )
        else:
            cur.execute("""
                SELECT p.player_name, p.tour, e.overall_elo, e.hard_elo, e.clay_elo, e.grass_elo
                FROM elo_ratings e JOIN players p ON e.player_id = p.player_id
                WHERE e.rating_date = (SELECT MAX(rating_date) FROM elo_ratings)
                ORDER BY e.overall_elo DESC LIMIT 20
            """)

        res = [dict(x) for x in cur.fetchall()]
        conn.close()
        return res

    def count_tournaments(self):
        """Get tournament counts by surface and category"""
        conn = self._conn()
        cur = conn.cursor()

        cur.execute("SELECT surface, COUNT(*) FROM tournaments GROUP BY surface")
        by_surface = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute("SELECT category, COUNT(*) FROM tournaments GROUP BY category")
        by_category = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute("SELECT tour, COUNT(*) FROM tournaments GROUP BY tour")
        by_tour = {row[0]: row[1] for row in cur.fetchall()}

        conn.close()
        return {"by_surface": by_surface, "by_category": by_category, "by_tour": by_tour}


if __name__ == "__main__":
    db = TennisELODatabase()

    print("=" * 60)
    print("TENNIS ELO DATABASE - QUICK TEST")
    print("=" * 60)

    print("\nTop 5 Career ELO (All Tours):")
    for i, p in enumerate(db.get_top_elo(limit=5), 1):
        print(f"  {i}. {p['player_name']} ({p['tour']}): {p['overall_elo']:.1f}")

    print("\nTop 5 Seasonal yELO (All Tours):")
    for i, p in enumerate(db.get_top_yelo(limit=5), 1):
        print(
            f"  {i}. {p['player_name']} ({p['tour']}): {p['yelo_rating']:.1f} ({p['wins']}-{p['losses']})"
        )

    print("\nDatabase Stats:")
    stats = db.get_stats()
    print(f"  Total Players: {stats['players']}")
    print(f"  Career ELO Records: {stats['elo_ratings']}")
    print(f"  Seasonal yELO Records: {stats['yelo_ratings']}")
    print(f"  Highest Career ELO: {stats['max_elo']:.1f}")
    print(f"  Highest Seasonal yELO: {stats['max_yelo']:.1f}")

    print("\nTournament Counts:")
    t_counts = db.count_tournaments()
    print(f"  By Surface: {t_counts['by_surface']}")
    print(f"  By Tour: {t_counts['by_tour']}")

    print("\nPlayer Comparison (Alcaraz vs Sinner):")
    comp = db.compare_players("Alcaraz", "Sinner")
    if comp:
        print(
            f"  {comp['player1']['name']} ({comp['player1']['tour']}): {comp['player1']['elo']:.1f}"
        )
        print(
            f"  {comp['player2']['name']} ({comp['player2']['tour']}): {comp['player2']['elo']:.1f}"
        )
        print(f"  Win Probability: {comp['win_probability']}")
