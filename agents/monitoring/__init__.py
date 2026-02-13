"""
Package Monitoring - Command Center
Interface mission control pour la surveillance du pipeline
"""

from .monitoring_agent import (
    MonitoringAgent,
    MetricType,
    AlertSeverity,
    PerformanceLevel,
    create_monitoring_agent
)

__all__ = [
    'MonitoringAgent',
    'MetricType',
    'AlertSeverity',
    'PerformanceLevel',
    'create_monitoring_agent'
]

__version__ = '2.0.0'