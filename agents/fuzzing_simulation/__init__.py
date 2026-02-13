"""
Package Fuzzing Simulation
Détection automatique de vulnérabilités par tests aléatoires et invariants
"""

from .fuzzing_agent import (
    FuzzingSimulationAgent,
    FuzzingEngine,
    FuzzingStrategy,
    VulnerabilityType,
    FuzzingCampaign,
    Vulnerability,
    create_fuzzing_agent
)

__all__ = [
    'FuzzingSimulationAgent',
    'FuzzingEngine',
    'FuzzingStrategy',
    'VulnerabilityType',
    'FuzzingCampaign',
    'Vulnerability',
    'create_fuzzing_agent'
]

__version__ = '1.0.0'