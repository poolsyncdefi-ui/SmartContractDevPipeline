"""
Package Frontend Web3
Génération d'interfaces React/Next.js pour smart contracts
"""

from .agent import (
    FrontendWeb3Agent,
    FrameworkType,
    ComponentType,
    Web3Library,
    FrontendProject,
    ContractABI,
    create_frontend_web3_agent
)

__all__ = [
    'FrontendWeb3Agent',
    'FrameworkType',
    'ComponentType',
    'Web3Library',
    'FrontendProject',
    'ContractABI',
    'create_frontend_web3_agent'
]

__version__ = '2.5.0'