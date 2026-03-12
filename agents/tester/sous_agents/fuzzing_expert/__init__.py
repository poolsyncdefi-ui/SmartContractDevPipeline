"""
Package pour le sous-agent de fuzzing.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import FuzzingExpertSubAgent, get_agent_class

__all__ = [
    'FuzzingExpertSubAgent',
    'get_agent_class'
]