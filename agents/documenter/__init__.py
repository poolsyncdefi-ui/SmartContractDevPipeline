"""
Package Documenter Pro - Documentation professionnelle
Génération de documentation structurée avec Mermaid et navigation
"""

from .documenter_agent import (
    DocumenterAgent,
    DocFormat,
    DocSection,
    DiagramType,
    create_documenter_agent
)

__all__ = [
    'DocumenterAgent',
    'DocFormat',
    'DocSection',
    'DiagramType',
    'create_documenter_agent'
]

__version__ = '2.0.0'