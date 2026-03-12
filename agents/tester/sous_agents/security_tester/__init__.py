"""
Package pour le sous-agent de tests de sécurité.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import SecurityTesterSubAgent, get_agent_class

__all__ = [
    'SecurityTesterSubAgent',
    'get_agent_class'
]