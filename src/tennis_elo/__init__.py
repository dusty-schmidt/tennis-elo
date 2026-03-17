"""Tennis ELO Prediction Engine

A comprehensive tennis match prediction system using ELO ratings
with surface-specific adjustments and sample-size calibrated seasonal form.
"""

__version__ = "1.0.1"
__author__ = "Tennis ELO Project"

from .name_resolver import PlayerNameResolver
from .prediction_engine import TennisPredictionEngine
from .database import TennisELODatabase

__all__ = [
    "TennisPredictionEngine",
    "PlayerNameResolver",
    "TennisELODatabase",
]
