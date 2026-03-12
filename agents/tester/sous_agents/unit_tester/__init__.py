"""
Package pour le sous-agent de tests unitaires.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import UnitTesterSubAgent, get_agent_class

__all__ = [
    'UnitTesterSubAgent',
    'get_agent_class'
]