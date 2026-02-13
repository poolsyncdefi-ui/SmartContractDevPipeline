"""
Package Learning & Intelligence Artificielle
Apprentissage automatique pour l'optimisation du pipeline
"""

# Import direct depuis le module
from agents.learning.learning_agent import (
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

__version__ = '1.0.0'