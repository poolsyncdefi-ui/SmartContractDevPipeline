"""
Package Registry - Catalogue intelligent des agents
Découverte · Versioning · Dépendances · Cache
"""

from .registry_agent import (
    RegistryAgent,
    RegistryEvent,
    AgentStatus,
    create_registry_agent
)

__all__ = [
    'RegistryAgent',
    'RegistryEvent',
    'AgentStatus',
    'create_registry_agent'
]

__version__ = '2.0.0'