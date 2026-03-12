"""
Package pour le sous-agent de tests end-to-end.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import E2ETesterSubAgent, get_agent_class

__all__ = [
    'E2ETesterSubAgent',
    'get_agent_class'
]