"""
Package des sous-agents de communication
Exporte tous les sous-agents disponibles
"""

from .circuit_breaker.agent import CircuitBreakerSubAgent

__all__ = [
    'CircuitBreakerSubAgent',
]

__version__ = '1.0.0'