"""
Package pour le sous-agent de vérification formelle.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import FormalVerificationSubAgent, get_agent_class

__all__ = [
    'FormalVerificationSubAgent',
    'get_agent_class'
]