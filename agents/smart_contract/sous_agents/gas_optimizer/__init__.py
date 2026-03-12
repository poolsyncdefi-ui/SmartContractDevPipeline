"""
Package pour le sous-agent d'optimisation gas.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import GasOptimizerSubAgent, get_agent_class

__all__ = [
    'GasOptimizerSubAgent',
    'get_agent_class'
]