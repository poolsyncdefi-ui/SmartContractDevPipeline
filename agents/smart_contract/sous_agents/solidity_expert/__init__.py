"""
Package pour le sous-agent expert Solidity.
Exporte la classe principale et la fonction d'usine.
"""

from .agent import SolidityExpertSubAgent, get_agent_class

__all__ = [
    'SolidityExpertSubAgent',
    'get_agent_class'
]