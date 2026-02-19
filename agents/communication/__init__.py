"""
Package Communication - Système nerveux central
Gestion des messages inter-agents avec files d'attente, persistance, pub/sub
"""

from .communication_agent import (
    CommunicationAgent,
    MessagePriority,
    MessageStatus,
    DeliveryGuarantee,
    Message,
    create_communication_agent
)

__all__ = [
    'CommunicationAgent',
    'MessagePriority',
    'MessageStatus',
    'DeliveryGuarantee',
    'Message',
    'create_communication_agent'
]

__version__ = '1.0.0'