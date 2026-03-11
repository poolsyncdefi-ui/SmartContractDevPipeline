"""
Package des sous-agents de communication
Exporte tous les sous-agents disponibles
"""

from .circuit_breaker.agent import CircuitBreakerSubAgent
from .queue_manager.agent import QueueManagerSubAgent
from .pubsub_manager.agent import PubSubManagerSubAgent
from .message_router.agent import MessageRouterSubAgent
from .dead_letter_analyzer.agent import DeadLetterAnalyzerSubAgent
from .performance_optimizer.agent import PerformanceOptimizerSubAgent
from .security_validator.agent import SecurityValidatorSubAgent

__all__ = [
    'CircuitBreakerSubAgent',
    'QueueManagerSubAgent',
    'PubSubManagerSubAgent',
    'MessageRouterSubAgent',
    'DeadLetterAnalyzerSubAgent',
    'PerformanceOptimizerSubAgent',
    'SecurityValidatorSubAgent',
]

__version__ = '2.0.0'