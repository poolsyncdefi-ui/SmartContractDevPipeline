"""
Package Communication - Système nerveux central
Gestion des messages inter-agents avec files d'attente, persistance, pub/sub
Version: 2.1.0
"""

from .agent import (
    CommunicationAgent,
    MessagePriority,
    MessageStatus,
    DeliveryGuarantee,
    MessageEnvelope,
    create_communication_agent
)

__all__ = [
    'CommunicationAgent',
    'MessagePriority',
    'MessageStatus',
    'DeliveryGuarantee',
    'MessageEnvelope',
    'create_communication_agent'
]

__version__ = '2.1.0'