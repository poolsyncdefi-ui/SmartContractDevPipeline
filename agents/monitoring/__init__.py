"""
Package Monitoring - Command Center
Interface mission control pour la surveillance du pipeline
"""

from .agent import (
    MonitoringAgent,
    AlertSeverity,
    PerformanceLevel,
    create_monitoring_agent
)

from reports.monitoring.dashboard_generator import DashboardGenerator

__all__ = [
    'MonitoringAgent',
    'AlertSeverity',
    'PerformanceLevel',
    'create_monitoring_agent'
    'DashboardGenerator'
]

__version__ = '2.0.0'