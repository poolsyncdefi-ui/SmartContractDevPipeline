"""
Package Orchestrator - Orchestration des workflows et sprints
"""
def __init__(self, config_path: str = ""):
    """Initialise l'orchestrateur"""
    super().__init__(config_path)
    
    self._logger.info("🚀 Orchestrator Agent créé")
    
    # Charger la configuration (utilise self._agent_config)
    self._load_configuration()
    
from .orchestrator import (
    OrchestratorAgent,
    Workflow,
    WorkflowStep,
    WorkflowStatus,
    StepStatus,
    DomainType,
    FragmentStatus,
    create_orchestrator_agent
)

__all__ = [
    'OrchestratorAgent',
    'Workflow',
    'WorkflowStep',
    'WorkflowStatus',
    'StepStatus',
    'DomainType',
    'FragmentStatus',
    'create_orchestrator_agent'
]

__version__ = '2.0.0'