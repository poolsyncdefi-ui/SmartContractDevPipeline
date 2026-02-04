"""
Classe de base pour tous les agents - Version corrigée
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

class BaseAgent(ABC):
    """Classe abstraite de base pour tous les agents"""
    
    def __init__(self, config_path: str = ""):
        self.config_path = config_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.agent_id = f"{self.__class__.__name__.lower()}_01"
        
        self.logger.info(f"Agent {self.agent_id} initialisé")
    
    @abstractmethod
    async def execute(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Méthode abstraite pour exécuter une tâche"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé de l'agent"""
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "type": self.__class__.__name__
        }
