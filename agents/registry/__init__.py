"""
Package Registry - Catalogue intelligent des agents
Découverte · Versioning · Dépendances · Cache
"""

from .agent import (
    RegistryAgent,
    RegistryEvent,
    AgentRegistryStatus,  # Renommé pour éviter la confusion
    create_registry_agent
)

__all__ = [
    'RegistryAgent',
    'RegistryEvent',
    'AgentRegistryStatus',
    'create_registry_agent'
]

__version__ = '2.0.0'