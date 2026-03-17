"""
Package des sous-agents de documentation
Exporte tous les sous-agents spécialisés disponibles
Version: 2.0.0
"""

from .doc_generator.agent import DocGeneratorSubAgent
from .diagram_generator.agent import DiagramGeneratorSubAgent
from .api_doc_specialist.agent import ApiDocSpecialistSubAgent
from .readme_specialist.agent import ReadmeSpecialistSubAgent

__all__ = [
    'DocGeneratorSubAgent',
    'DiagramGeneratorSubAgent',
    'ApiDocSpecialistSubAgent',
    'ReadmeSpecialistSubAgent'
]

__version__ = '2.0.0'