#!/usr/bin/env python3
"""Example: Predict a tennis match"""
import sys
sys.path.insert(0, 'src')

from tennis_elo import TennisPredictionEngine

def main():
    # Initialize engine
    engine = TennisPredictionEngine(db_path="data/tennis_elo.db")
    
    # Example predictions
    matchups = [
        ("Alcaraz", "Sinner", "Wimbledon"),
        ("Sabalenka", "Swiatek", "French Open"),
        ("Djokovic", "Medvedev", "US Open"),
    ]
    
    print("="*70)
    print("TENNIS ELO PREDICTION EXAMPLES")
    print("="*70)
    
    for player1, player2, tournament in matchups:
        print(f"\n{player1} vs {player2} @ {tournament}")
        print("-"*70)
        
        result = engine.predict_match(player1, player2, tournament)
        
        if "error" not in result:
            p1 = result["match"]["player1"]
            p2 = result["match"]["player2"]
            
            print(f"{p1['name']}: {p1['win_percentage']} (ELO: {p1['adjusted_elo']})")
            print(f"{p2['name']}: {p2['win_percentage']} (ELO: {p2['adjusted_elo']})")
            print(f"Favorite: {result['prediction']['favorite']}")
        else:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
