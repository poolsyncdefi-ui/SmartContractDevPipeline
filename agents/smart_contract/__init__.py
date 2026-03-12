"""
Package Smart Contract - Développement de smart contracts sécurisés
Version: 2.5.0
"""

from .agent import (
    SmartContractAgent,
    ContractType,
    ContractStandard,
    SolidityVersion,
    AuditSeverity,
    VulnerabilityType,
    GasOptimizationLevel,
    VerificationStatus,
    create_smart_contract_agent,
    get_agent_class
)

__all__ = [
    'SmartContractAgent',
    'ContractType',
    'ContractStandard',
    'SolidityVersion',
    'AuditSeverity',
    'VulnerabilityType',
    'GasOptimizationLevel',
    'VerificationStatus',
    'create_smart_contract_agent',
    'get_agent_class'
]

__version__ = '2.5.0'