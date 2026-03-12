"""
Package pour le sous-agent de tests blockchain.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import BlockchainTesterSubAgent, get_agent_class

__all__ = [
    'BlockchainTesterSubAgent',
    'get_agent_class'
]