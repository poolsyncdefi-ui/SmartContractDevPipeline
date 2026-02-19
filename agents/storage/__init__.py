"""
Package Storage - Gestion centralisée des données
Stockage clé-valeur, documents, fichiers, cache, IPFS, chiffrement
"""

from .storage_agent import (
    StorageAgent,
    StorageType,
    DataType,
    CachePolicy,
    create_storage_agent
)

__all__ = [
    'StorageAgent',
    'StorageType',
    'DataType',
    'CachePolicy',
    'create_storage_agent'
]

__version__ = '1.0.0'