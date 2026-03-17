"""
Package Documenter - Documentation professionnelle
Gère la documentation technique, diagrammes, API, README
Version: 2.2.0
"""

from .agent import (
    DocumenterAgent,
    DocFormat,
    DocSection,
    DiagramType,
    create_documenter_agent,
    get_agent_class
)

# Exports des sous-agents
from .sous_agents.doc_generator.agent import DocGeneratorSubAgent
from .sous_agents.diagram_generator.agent import DiagramGeneratorSubAgent
from .sous_agents.api_doc_specialist.agent import ApiDocSpecialistSubAgent
from .sous_agents.readme_specialist.agent import ReadmeSpecialistSubAgent

__all__ = [
    'DocumenterAgent',
    'DocFormat',
    'DocSection',
    'DiagramType',
    'create_documenter_agent',
    'get_agent_class',
    'DocGeneratorSubAgent',
    'DiagramGeneratorSubAgent',
    'ApiDocSpecialistSubAgent',
    'ReadmeSpecialistSubAgent'
]

__version__ = '2.2.0'