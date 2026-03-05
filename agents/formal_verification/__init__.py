"""
Package de vérification formelle pour smart contracts
"""

from .agent import (
    FormalVerificationAgent,
    VerificationType,
    VerificationStatus,
    FormalSpecification,
    VerificationProof,
    create_formal_verification_agent
)

__all__ = [
    'FormalVerificationAgent',
    'VerificationType',
    'VerificationStatus',
    'FormalSpecification',
    'VerificationProof',
    'create_formal_verification_agent'
]

__version__ = '2.0.0'