"""
Package Formal Verification - Vérification formelle des smart contracts
Gère les preuves formelles, invariants et certifications avec Certora, Halo2 et Mythril
Version: 2.0.0
"""

from .agent import (
    FormalVerificationAgent,
    VerificationStatus,
    VerificationTool,
    PropertyType,
    VerificationProperty,
    VerificationProof,
    VerificationCertificate,
    create_formal_verification_agent,
    get_agent_class
)

# Exports des sous-agents pour un accès direct
from .sous_agents.certora_specialist.agent import CertoraSpecialistSubAgent
from .sous_agents.halo2_specialist.agent import Halo2SpecialistSubAgent
from .sous_agents.mythril_specialist.agent import MythrilSpecialistSubAgent

__all__ = [
    # Agent principal
    'FormalVerificationAgent',
    
    # Classes de données
    'VerificationStatus',
    'VerificationTool',
    'PropertyType',
    'VerificationProperty',
    'VerificationProof',
    'VerificationCertificate',
    
    # Fonctions d'usine
    'create_formal_verification_agent',
    'get_agent_class',
    
    # Sous-agents
    'CertoraSpecialistSubAgent',
    'Halo2SpecialistSubAgent',
    'MythrilSpecialistSubAgent'
]

__version__ = '2.0.0'