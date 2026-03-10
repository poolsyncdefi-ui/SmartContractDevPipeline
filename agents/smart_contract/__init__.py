"""
Package Smart Contract Agent - Agent principal de développement de smart contracts
Génération, audit, optimisation et déploiement de smart contracts sécurisés
"""

from .agent import (
    SmartContractAgent,
    ContractStandard,
    AuditSeverity,
    DeploymentStatus,
    ContractTemplate,
    AuditFinding,
    DeploymentInfo,
    create_smart_contract_agent
)

__all__ = [
    'SmartContractAgent',
    'ContractStandard',
    'AuditSeverity',
    'DeploymentStatus',
    'ContractTemplate',
    'AuditFinding',
    'DeploymentInfo',
    'create_smart_contract_agent'
]

__version__ = '2.6.0'