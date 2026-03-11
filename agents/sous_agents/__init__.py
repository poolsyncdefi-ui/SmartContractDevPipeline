"""
Package des classes de base pour les sous-agents
Fournit les classes abstraites et utilitaires communes à TOUS les sous-agents
"""

from .base_subagent import (
    BaseSubAgent,
    SubAgentTaskPriority,
    SubAgentTaskStatus,
    SubAgentTask,
    SubAgentMetrics
)

__all__ = [
    'BaseSubAgent',
    'SubAgentTaskPriority',
    'SubAgentTaskStatus',
    'SubAgentTask',
    'SubAgentMetrics'
]

__version__ = '1.0.0'