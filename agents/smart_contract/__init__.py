"""
Package Smart Contract Agent
Génération, audit, optimisation et déploiement de smart contracts
"""

from .agent import (
    SmartContractAgent,
    create_smart_contract_agent
)

__all__ = [
    'SmartContractAgent',
    'create_smart_contract_agent'
]

__version__ = '2.5.0'