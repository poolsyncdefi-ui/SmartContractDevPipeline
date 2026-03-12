"""
Package pour le sous-agent de tests d'intégration.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import IntegrationTesterSubAgent, get_agent_class

__all__ = [
    'IntegrationTesterSubAgent',
    'get_agent_class'
]