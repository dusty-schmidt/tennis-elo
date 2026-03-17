"""Tests for Tennis Prediction Engine"""
import pytest
import sys
sys.path.insert(0, 'src')

from tennis_elo import TennisPredictionEngine, PlayerNameResolver

class TestNameResolver:
    """Test player name resolution"""
    
    @pytest.fixture
    def resolver(self):
        return PlayerNameResolver(db_path="data/tennis_elo.db")
    
    def test_resolve_full_name(self, resolver):
        """Test resolving full player name"""
        player = resolver.resolve_name("Alcaraz", "ATP")
        assert player is not None
        assert "Alcaraz" in player["player_name"]
    
    def test_resolve_last_name(self, resolver):
        """Test resolving by last name only"""
        player = resolver.resolve_name("Sinner", "ATP")
        assert player is not None
    
    def test_resolve_with_typo(self, resolver):
        """Test fuzzy matching with typos"""
        player = resolver.resolve_name("Alcarz", "ATP")
        assert player is not None
        assert "Alcaraz" in player["player_name"]
    
    def test_resolve_nickname(self, resolver):
        """Test resolving nickname"""
        player = resolver.resolve_name("Djoko", "ATP")
        assert player is not None
        assert "Djokovic" in player["player_name"]


class TestPredictionEngine:
    """Test match predictions"""
    
    @pytest.fixture
    def engine(self):
        return TennisPredictionEngine(db_path="data/tennis_elo.db")
    
    def test_predict_match(self, engine):
        """Test basic match prediction"""
        result = engine.predict_match("Alcaraz", "Sinner", "Wimbledon")
        assert "error" not in result
        assert "match" in result
        assert "player1" in result["match"]
        assert "player2" in result["match"]
        assert "win_probability" in result["match"]["player1"]
    
    def test_prediction_probabilities_sum(self, engine):
        """Test that win probabilities sum to 100%"""
        result = engine.predict_match("Alcaraz", "Sinner", "Wimbledon")
        p1 = result["match"]["player1"]["win_probability"]
        p2 = result["match"]["player2"]["win_probability"]
        assert abs((p1 + p2) - 1.0) < 0.001
    
    def test_surface_adjustment(self, engine):
        """Test that surface affects predictions"""
        wimbledon = engine.predict_match("Alcaraz", "Sinner", "Wimbledon")
        french_open = engine.predict_match("Alcaraz", "Sinner", "French Open")
        
        # Different surfaces should give different adjusted ELOs
        wimb_adj = wimbledon["match"]["player1"]["adjusted_elo"]
        fo_adj = french_open["match"]["player1"]["adjusted_elo"]
        assert wimb_adj != fo_adj  # Grass vs Clay
    
    def test_invalid_tournament(self, engine):
        """Test error handling for invalid tournament"""
        result = engine.predict_match("Alcaraz", "Sinner", "Invalid Tournament")
        assert "error" in result
    
    def test_invalid_player(self, engine):
        """Test error handling for invalid player"""
        result = engine.predict_match("InvalidPlayer", "Sinner", "Wimbledon")
        assert "error" in result


class TestYELOWeighting:
    """Test yELO sample-size calibration"""
    
    @pytest.fixture
    def engine(self):
        return TennisPredictionEngine(db_path="data/tennis_elo.db")
    
    def test_zero_weight_few_matches(self, engine):
        """Test that < 3 matches gets 0% weight"""
        weight = engine.calculate_yelo_weight(2, "ATP")
        assert weight == 0.0
    
    def test_increasing_weight(self, engine):
        """Test that weight increases with matches"""
        w5 = engine.calculate_yelo_weight(5, "ATP")
        w15 = engine.calculate_yelo_weight(15, "ATP")
        w25 = engine.calculate_yelo_weight(25, "ATP")
        
        assert w5 < w15 < w25
    
    def test_max_weight_cap(self, engine):
        """Test that weight is capped at maximum"""
        w30 = engine.calculate_yelo_weight(30, "ATP")
        w50 = engine.calculate_yelo_weight(50, "ATP")
        
        assert w30 <= 0.25
        assert w50 <= 0.25
        assert abs(w30 - w50) < 0.001  # Both at max
