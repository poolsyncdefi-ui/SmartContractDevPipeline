"""
Package pour le sous-agent expert sécurité.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import SecurityExpertSubAgent, get_agent_class

__all__ = [
    'SecurityExpertSubAgent',
    'get_agent_class'
]