#!/usr/bin/env python3
"""Player Name Resolution System
   Handles name lookups with aliases, fuzzy matching, and multi-source support
"""
import sqlite3
import re
from difflib import SequenceMatcher
from typing import Optional, List, Dict, Tuple

DB_PATH = "/a0/usr/projects/tennis-elo/tennis_elo.db"

class PlayerNameResolver:
    """
    Robust player name resolution with multiple matching strategies.
    
    Matching priority:
    1. Exact alias match
    2. Normalized match (case, spaces, special chars)
    3. Fuzzy match (typo tolerance)
    4. Last name match
    """
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._alias_cache = None
    
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize name for comparison:
        - Lowercase
        - Remove special characters
        - Normalize spaces
        """
        name = name.lower().strip()
        name = re.sub(r'[^\w\s]', '', name)
        name = ' '.join(name.split())
        return name
    
    def load_aliases(self) -> Dict[str, int]:
        """Load all aliases into memory for fast lookup"""
        if self._alias_cache is not None:
            return self._alias_cache
        
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT alias_name, player_id FROM player_aliases")
        
        alias_map = {}
        for row in cur.fetchall():
            normalized = self.normalize_name(row['alias_name'])
            alias_map[normalized] = row['player_id']
        
        conn.close()
        self._alias_cache = alias_map
        return alias_map
    
    def resolve_name(self, query: str, tour: str = None) -> Optional[Dict]:
        """
        Resolve a name query to a player.
        
        Strategies (in order):
        1. Exact alias match
        2. Normalized match
        3. Fuzzy match (85%+ similarity)
        4. Last name match
        
        Returns player dict or None if not found
        """
        if not query:
            return None
        
        query_normalized = self.normalize_name(query)
        
        conn = self._conn()
        cur = conn.cursor()
        
        # Strategy 1: Exact alias match
        player_id = self.load_aliases().get(query_normalized)
        if player_id:
            return self._get_player_by_id(player_id, tour)
        
        # Strategy 2: LIKE query on aliases
        cur.execute("""
            SELECT pa.player_id, p.player_name, p.tour
            FROM player_aliases pa
            JOIN players p ON pa.player_id = p.player_id
            WHERE pa.alias_name LIKE ?
        """, (f"%{query}%",))
        
        rows = cur.fetchall()
        if rows:
            # If tour specified, filter
            if tour:
                for row in rows:
                    if row['tour'] == tour:
                        return self._get_player_by_id(row['player_id'], tour)
            # Otherwise return first match
            return self._get_player_by_id(rows[0]['player_id'], tour)
        
        # Strategy 3: Fuzzy match on player names
        cur.execute("SELECT player_id, player_name, tour FROM players")
        all_players = cur.fetchall()
        
        best_match = None
        best_score = 0.85  # Minimum 85% similarity
        
        for player in all_players:
            if tour and player['tour'] != tour:
                continue
            
            # Compare normalized names
            player_normalized = self.normalize_name(player['player_name'])
            score = SequenceMatcher(None, query_normalized, player_normalized).ratio()
            
            # Also check against aliases
            aliases = self._get_player_aliases(player['player_id'])
            for alias in aliases:
                alias_normalized = self.normalize_name(alias)
                alias_score = SequenceMatcher(None, query_normalized, alias_normalized).ratio()
                score = max(score, alias_score)
            
            if score > best_score:
                best_score = score
                best_match = player
        
        if best_match:
            return self._get_player_by_id(best_match['player_id'], tour)
        
        # Strategy 4: Last name match
        query_parts = query.strip().split()
        if query_parts:
            last_name = query_parts[-1]
            cur.execute("""
                SELECT player_id, player_name, tour FROM players
                WHERE player_name LIKE ?
            """, (f"%{last_name}%",))
            
            rows = cur.fetchall()
            if rows:
                if tour:
                    for row in rows:
                        if row['tour'] == tour:
                            return self._get_player_by_id(row['player_id'], tour)
                return self._get_player_by_id(rows[0]['player_id'], tour)
        
        conn.close()
        return None
    
    def _get_player_by_id(self, player_id: int, tour: str = None) -> Optional[Dict]:
        """Get player details by ID"""
        conn = self._conn()
        cur = conn.cursor()
        
        if tour:
            cur.execute("SELECT * FROM players WHERE player_id = ? AND tour = ?", (player_id, tour))
        else:
            cur.execute("SELECT * FROM players WHERE player_id = ?", (player_id,))
        
        row = cur.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def _get_player_aliases(self, player_id: int) -> List[str]:
        """Get all aliases for a player"""
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT alias_name FROM player_aliases WHERE player_id = ?", (player_id,))
        aliases = [row['alias_name'] for row in cur.fetchall()]
        conn.close()
        return aliases
    
    def search_players(self, query: str, tour: str = None, limit: int = 10) -> List[Dict]:
        """
        Search for players matching query.
        Returns list of matching players with scores.
        """
        if not query:
            return []
        
        query_normalized = self.normalize_name(query)
        
        conn = self._conn()
        cur = conn.cursor()
        
        # Get all players (filtered by tour if specified)
        if tour:
            cur.execute("SELECT player_id, player_name, tour FROM players WHERE tour = ?", (tour,))
        else:
            cur.execute("SELECT player_id, player_name, tour FROM players")
        
        all_players = cur.fetchall()
        conn.close()
        
        matches = []
        for player in all_players:
            player_normalized = self.normalize_name(player['player_name'])
            
            # Calculate similarity score
            score = SequenceMatcher(None, query_normalized, player_normalized).ratio()
            
            # Also check aliases
            aliases = self._get_player_aliases(player['player_id'])
            for alias in aliases:
                alias_normalized = self.normalize_name(alias)
                alias_score = SequenceMatcher(None, query_normalized, alias_normalized).ratio()
                score = max(score, alias_score)
            
            if score >= 0.5:  # Minimum 50% similarity
                matches.append({
                    'player_id': player['player_id'],
                    'player_name': player['player_name'],
                    'tour': player['tour'],
                    'match_score': round(score, 3)
                })
        
        # Sort by score and limit
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:limit]
    
    def add_alias(self, player_name: str, alias: str, alias_type: str = 'manual') -> bool:
        """
        Add a new alias for a player.
        Returns True if successful, False if player not found.
        """
        player = self.resolve_name(player_name)
        if not player:
            return False
        
        conn = self._conn()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT OR IGNORE INTO player_aliases (player_id, alias_name, alias_type, source)
                VALUES (?, ?, ?, ?)
            """, (player['player_id'], alias, alias_type, 'manual'))
            
            conn.commit()
            success = cur.rowcount > 0
            
            # Clear cache
            self._alias_cache = None
            
            return success
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()


# CLI Test
if __name__ == "__main__":
    resolver = PlayerNameResolver()
    
    print("="*70)
    print("PLAYER NAME RESOLVER - TEST")
    print("="*70)
    
    # Test cases that previously failed
    test_queries = [
        ("De Minaur", None),
        ("De Minaur", "ATP"),
        ("de minaur", None),
        ("minaur", None),
        ("A. De Minaur", None),
        ("Alcaraz", None),
        ("C. Alcaraz", None),
        ("carlos alcaraz", None),
        ("Djokovic", None),
        ("Djoko", None),
        ("Sabalenka", "WTA"),
        ("Swiatek", "WTA"),
    ]
    
    print("\nTesting name resolution:")
    print("-"*70)
    
    for query, tour in test_queries:
        result = resolver.resolve_name(query, tour)
        if result:
            print(f"✓ '{query}' → {result['player_name']} ({result['tour']})")
        else:
            print(f"✗ '{query}' → NOT FOUND")
    
    # Test fuzzy matching
    print("\n\nFuzzy matching tests:")
    print("-"*70)
    
    fuzzy_tests = [
        "Alcarz",  # Typo
        "Sinnr",   # Typo
        "Medvedev",  # Correct
        "Medveded",  # Typo
        "Zverev",   # Correct
        "Zvere",    # Partial
    ]
    
    for query in fuzzy_tests:
        result = resolver.resolve_name(query, "ATP")
        if result:
            print(f"✓ '{query}' → {result['player_name']} (fuzzy match)")
        else:
            print(f"✗ '{query}' → NOT FOUND")
    
    # Test search
    print("\n\nSearch tests (multiple results):")
    print("-"*70)
    
    search_queries = ["Alex", "Carlos", "Novak"]
    
    for query in search_queries:
        results = resolver.search_players(query, limit=3)
        print(f"\n'{query}':")
        for r in results:
            print(f"  - {r['player_name']} ({r['tour']}) [score: {r['match_score']}]")
    
    print("\n" + "="*70)
    print("Name resolver test complete!")
    print("="*70)
