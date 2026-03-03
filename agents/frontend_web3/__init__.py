"""
Package Frontend Web3
Génération d'interfaces React/Next.js pour smart contracts
"""

from .agent import (
    FrontendWeb3Agent,
    FrameworkType,
    ComponentType,
    Web3Library,
    FrontendProject
)

__all__ = [
    'FrontendWeb3Agent',
    'FrameworkType',
    'ComponentType',
    'Web3Library',
    'FrontendProject'
]

__version__ = '2.0.0'