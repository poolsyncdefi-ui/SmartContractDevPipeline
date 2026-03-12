"""
Package pour le sous-agent de tests de performance.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import PerformanceTesterSubAgent, get_agent_class

__all__ = [
    'PerformanceTesterSubAgent',
    'get_agent_class'
]