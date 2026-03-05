"""
Learning Agent Package - Intelligence Artificielle pour l'optimisation du pipeline
"""

# Import depuis le module principal
from .agent import (
    LearningAgent,
    LearningTaskType,
    ModelType,
    ConfidenceLevel,
    TrainingExample,
    ModelMetadata,
    Insight,
    create_learning_agent
)

__all__ = [
    'LearningAgent',
    'LearningTaskType',
    'ModelType',
    'ConfidenceLevel',
    'TrainingExample',
    'ModelMetadata',
    'Insight',
    'create_learning_agent'
]

__version__ = '2.0.0'