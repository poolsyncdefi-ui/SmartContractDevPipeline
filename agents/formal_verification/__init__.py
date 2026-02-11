"""
Package de vérification formelle pour smart contracts
"""

from .formal_verification import (
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

__version__ = '1.0.0'