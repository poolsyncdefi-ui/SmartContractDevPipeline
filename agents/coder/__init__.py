"""
Package Coder Agent - Agent principal de développement de code
Génération de code backend, frontend, smart contracts, tests et documentation
"""

from .agent import (
    CoderAgent,
    CodeLanguage,
    Framework,
    ComponentType,
    GenerationStatus,
    CodeComponent,
    GeneratedFile,
    GenerationResult,
    create_coder_agent
)

__all__ = [
    'CoderAgent',
    'CodeLanguage',
    'Framework',
    'ComponentType',
    'GenerationStatus',
    'CodeComponent',
    'GeneratedFile',
    'GenerationResult',
    'create_coder_agent'
]

__version__ = '2.2.0'