"""
Package Documenter - Documentation professionnelle
Gère la documentation technique, diagrammes, API, README avec qualité et validation
Version: 2.2.0
"""

from .agent import (
    DocumenterAgent,
    DocFormat,
    DocType,
    DiagramType,
    DocStatus,
    QualityLevel,
    DocRequest,
    DocSection,
    DocPackage,
    create_documenter_agent,
    get_agent_class
)

__all__ = [
    'DocumenterAgent',
    'DocFormat',
    'DocType',
    'DiagramType',
    'DocStatus',
    'QualityLevel',
    'DocRequest',
    'DocSection',
    'DocPackage',
    'create_documenter_agent',
    'get_agent_class'
]

__version__ = '2.2.0'